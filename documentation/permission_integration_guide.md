# 权限模块接入指南

本文档面向基于当前模板新增业务模块的开发者，说明如何标准接入：

- API 权限
- 数据权限
- 菜单权限
- 资源映射

同时补充当前模板的系统角色与初始化规则，避免继续从历史兼容行为中猜测约束。

## 1. 当前模板边界

当前模板实际交付的后端模块只有：

- `modules/admin`
- `modules/iam`
- `modules/label_manager`

权限相关职责边界如下：

- `modules/admin`：权限配置真源，负责角色、菜单、接口权限、数据权限规则管理
- `modules/iam`：权限运行时，负责 Casbin Enforcer、策略投影、权限检查
- `modules/*/manifest.py`：声明模块路由、资源映射和 Provider 装配入口
- `common.auth.CurrentPrincipal`：统一请求身份模型
- `common.ports.IPermissionChecker`：API 权限检查 Port
- `common.ports.IDataScopeResolver`：数据权限 Port
- `common.ports.IPermissionManager`：权限投影与同步 Port

## 2. 系统角色与种子规则

当前模板只内置一个稳定系统角色：

- 角色名：`超级管理员`
- 角色编码：`role:admin`
- `is_system`：`true`

对应默认管理员种子规则：

- 用户 ID：`1`
- 用户名：`admin`
- 角色 ID：`1`
- 默认角色：`role:admin`
- 默认数据权限：`__all__ -> view=ALL, edit=ALL`

普通角色规则：

- 所有通过接口创建的普通角色都使用 `role:{id}`
- 不再按角色名称生成语义化 `code`

实现约束：

- 运行时判断系统角色时，主语义依赖 `role.code + is_system`
- 模板层不保留面向旧结构的跨模块兼容入口

初始化入口：

- `backend/init_db.py` 只负责驱动建库与执行 Alembic 迁移
- 默认管理员、系统角色、菜单/API 权限及默认授权均通过 Alembic 数据迁移管理
- `backend/alembic/versions/init_user_data.sql`
- `backend/alembic/versions/init_permissions.sql`
- `backend/alembic/versions/d0d6403df0d7_seed_default_admin_and_permissions.py`

其中 SQL 文件由对应 Alembic revision 执行，并作为默认种子数据来源。

## 3. API 权限接入

### 3.1 接入步骤

1. 在模块路由中为受保护接口接入 `require_permission()`
2. 为该接口补充 `api_permissions` 种子定义
3. 如该接口属于数据权限资源，再同步补资源映射

### 3.2 路由层写法

以 `label_manager` 为例：

```python
@router.get(
    "",
    response_model=ResponseSchema[list[LabelRead]],
    dependencies=[Depends(require_permission())],
    summary="获取标签列表",
)
async def list_labels(...):
    ...
```

说明：

- `require_permission()` 会根据请求路径和 HTTP 方法调用 `IPermissionChecker`
- 业务服务层不要直接感知 Casbin 或 Enforcer

### 3.3 API 权限种子

新增接口后，需要把对应 API 权限定义加入默认种子：

- Alembic 数据迁移：`backend/alembic/versions/d0d6403df0d7_seed_default_admin_and_permissions.py`
- 参考快照：`backend/alembic/versions/init_permissions.sql`

建议每条记录至少包含：

- 权限 ID
- 权限名称
- 分组名称
- `api_path`
- `method`
- `status`

只为真正经过 `require_permission()` 保护的接口建立 API 权限定义；纯登录、刷新 token 这类接口不要滥加到 Casbin 投影里。

## 4. 数据权限接入

### 4.1 接入原则

需要做“可见范围过滤”或“实体可操作校验”的模块，统一依赖 `IDataScopeResolver`：

- 列表查询：`build_query_scope()`
- 实体更新/删除：`can_operate_entity()`

禁止新代码继续依赖：

- 任何业务模块的跨模块 `api/dependencies.py`
- 在 `app_setup` 中硬编码具体业务模块的数据权限实现

### 4.2 列表查询示例

```python
scope_filter = await data_scope_resolver.build_query_scope(
    user_id=current_user.user_id,
    resource_type="labels",
    action="view",
    model_cls=Label,
)
labels = await service.list_labels_with_scope(scope_filter=scope_filter)
```

### 4.3 实体操作示例

```python
allowed = await data_scope_resolver.can_operate_entity(
    user_id=current_user.user_id,
    resource_type="labels",
    action="edit",
    entity=existing,
)
if not allowed:
    raise BusinessError("无数据操作权限", code=403)
```

## 5. 菜单权限接入

菜单权限由 `menu_permissions` 与 `role_menu_permissions` 两张表表达。

新增业务模块时，需要：

1. 为前端可见菜单补 `menu_permissions` 默认种子
2. 根据需要把该菜单分配给系统角色或其他默认角色

当前模板的默认菜单种子同样由以下位置维护：

- `backend/alembic/versions/d0d6403df0d7_seed_default_admin_and_permissions.py`
- `backend/alembic/versions/init_permissions.sql`

菜单权限只负责“展示哪些菜单”，不替代 API 权限检查。

## 6. 资源映射接入

只要模块涉及数据权限，就必须补资源映射。

当前推荐做法不是继续手工改单个大表，而是通过模块 manifest 自注册。

装配层统一收集入口：

- `backend/app_setup/module_registry.py`

模块级 manifest 示例位置：

- `backend/modules/label_manager/manifest.py`

资源注册运行时入口：

- `backend/app_setup/resource_registry.py`

映射内容包括：

- 路由路径
- HTTP 方法
- 资源类型
- 动作语义

例如：

```python
resource_registry.register(
    "/api/v1/labels",
    "GET",
    ResourceAction(resource_type="labels", action="view", primary_resource="labels"),
)
```

如果新增模块需要数据权限，推荐在模块自己的 `manifest.py` 中声明：

```python
module_manifest = ModuleManifest(
    name="your_module",
    router=router,
    resource_registrations=(
        ResourceRegistration(
            path_pattern="/api/v1/your-resources",
            method="GET",
            action=ResourceAction(
                resource_type="your_resources",
                action="view",
                primary_resource="your_resources",
            ),
        ),
    ),
)
```

建议动作语义保持稳定，如：

- `view`
- `edit`

不要直接把业务判断写死成 URL 字符串比较。

## 7. 身份模型接入

API 层默认使用：

- `CurrentPrincipal = Depends(get_current_principal)`

共享认证与权限依赖统一由装配层提供：

- `backend/app_setup/auth_dependencies.py`
- `backend/app_setup/permission_providers.py`

只有在确实需要完整用户资料时，才通过应用服务按 `principal.user_id` 显式查询用户实体。

推荐写法：

```python
async def get_my_resource(
    current_user: CurrentPrincipal = Depends(get_current_principal),
):
    operator_id = current_user.user_id
```

不推荐写法：

- 在 API 层默认注入 `admin.domain.entities.User`
- 把完整 `User` 当作跨模块共享身份对象传递

## 8. 接入检查清单

新增一个需要权限能力的业务模块时，至少检查以下事项：

- 是否新增了模块级 `manifest.py`
- 是否使用 `CurrentPrincipal` 作为默认身份模型
- 是否为受保护接口加上 `require_permission()`
- 是否为受保护接口补了 API 权限种子
- 是否为前端菜单补了菜单权限种子
- 是否通过模块 manifest 为数据权限资源补了 `resource_registry` 映射
- 是否通过 `IDataScopeResolver` 接入列表过滤或实体校验
- 是否通过模块自己的 `api/dependencies.py` 接入装配层共享依赖
- 是否通过模块 `manifest.py` 注册自身 Provider，而不是把实现硬编码到 `app_setup`
- 是否避免直接依赖 Casbin 具体实现
- 是否避免跨模块复用其他业务模块的 `api/dependencies.py`

## 9. 推荐参考

建议先参考以下现有实现：

- `backend/modules/label_manager/api/v1/labels.py`
- `backend/modules/label_manager/api/dependencies.py`
- `backend/app_setup/auth_dependencies.py`
- `backend/app_setup/resource_registry.py`
- `backend/app_setup/provider_registry.py`
- `backend/modules/label_manager/manifest.py`
- `backend/app_setup/permission_providers.py`
