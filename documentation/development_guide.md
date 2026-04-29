# FastAPI-Admin 开发指导手册

本文档面向基于当前模板继续开发业务模块的后端开发者，目标是帮助你在不破坏现有架构边界的前提下，快速完成：

- 新业务模块开发
- 认证与权限接入
- 数据库与迁移规范落地
- 测试与交付自检

## 1. 适用范围

当前模板已经收口为一个可直接扩展的后台管理系统后端骨架，当前真实交付模块包括：

- `modules/admin`：后台管理与权限配置真源
- `modules/iam`：权限运行域，负责 Casbin 运行时、策略投影与权限检查
- `modules/label_manager`：示例业务模块，可作为后续扩展参考

模板的核心原则如下：

- `core/` 只放基础设施和框架能力，不依赖业务模块
- `app_setup/` 只负责装配，不承担业务逻辑
- 每个业务模块遵循 `api / application / domain / infra` 分层
- 共享身份、权限检查、数据权限统一通过 Port 和装配层接入
- 不保留历史兼容层，不允许通过跨模块引用偷渡依赖

## 2. 先理解当前架构

### 2.1 分层职责

- `api/`：接口层，负责 HTTP 路由、请求/响应模型、返回格式
- `application/`：应用层，负责业务流程编排
- `domain/`：领域层，负责实体、值对象、仓储抽象、领域规则
- `infra/`：基础设施层，负责仓储实现和数据库访问

### 2.2 运行时装配入口

应用启动后，装配层会统一完成以下工作：

- 通过 [router_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/router_registry.py) 收集模块路由
- 通过 [resource_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/resource_registry.py) 收集资源映射
- 通过 [provider_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/provider_registry.py) 注册模块级 Provider
- 通过 [permission_providers.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/permission_providers.py) 暴露共享权限相关接口

模块自注册的载体是 [module_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/common/module_registry.py) 中定义的 `ModuleManifest`。

### 2.3 当前权限边界

- `modules/admin`：维护角色、菜单、接口权限、数据权限规则
- `modules/iam`：持有 Casbin Enforcer、Watcher、策略投影
- `app_setup/auth_dependencies.py`：暴露 `CurrentPrincipal`、`require_permission()`、`IDataScopeResolver`
- 业务模块只依赖：
  - `CurrentPrincipal`
  - `IPermissionChecker`
  - `IDataScopeResolver`
  - 必要时通过装配层拿 `IPermissionManager`

## 3. 日常开发流程

推荐的日常开发顺序如下：

1. 明确业务资源和动作语义
2. 创建模块骨架
3. 先写领域模型与仓储抽象
4. 再写应用服务和输入契约
5. 最后接 API、权限、资源映射和迁移脚本
6. 补最小测试并做自检

开发常用命令：

```bash
cd backend
uv sync
uv run python init_db.py
uv run pytest tests/unit
uvx ruff format .
```

## 4. 新模块添加开发指导

### 4.1 模块目录骨架

新增模块时，至少建立如下结构：

```text
backend/modules/your_module/
├── __init__.py
├── manifest.py
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py
│       ├── schemas.py
│       └── your_resources.py
├── application/
│   ├── __init__.py
│   ├── contracts.py
│   ├── dto.py
│   └── services.py
├── domain/
│   ├── __init__.py
│   ├── entities.py
│   └── repositories.py
└── infra/
    ├── __init__.py
    ├── model.py
    └── repositories.py
```

如果模块不需要 `dto.py` 或暂时没有复杂映射，可以后续再补，但 `api / application / domain / infra` 四层建议一次补齐。

### 4.2 领域层先行

优先在 `domain/` 中定义：

- 领域实体
- 仓储抽象接口
- 核心业务约束

注意：

- 仓储接口放在 `domain/repositories.py`
- 仓储实现放在 `infra/repositories.py`
- 应用服务依赖仓储抽象，不直接依赖 ORM 细节

### 4.3 应用层建模

`application/contracts.py` 只放应用层输入契约，例如：

- `CreateXxx`
- `UpdateXxx`
- `GrantXxxInput`

不要把 API 响应模型放在 `contracts.py` 中。

`application/dto.py` 用于定义应用层输出 DTO，适合：

- 列表聚合结果
- 授权结果
- 多表拼装后的只读数据

### 4.4 API 层建模

`api/v1/schemas.py` 负责：

- 请求模型
- 响应模型
- 展示模型
- 查询参数模型

推荐边界：

- API 入参如果本质上就是应用层输入契约，可以直接复用 `application/contracts.py`
- API 响应模型保留在 `api/v1/schemas.py`
- API 层负责把 DTO 映射为对外响应模型

### 4.5 模块依赖装配

模块内部的仓储和服务装配统一收口到 `api/dependencies.py`。

参考 [label_manager/api/dependencies.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/label_manager/api/dependencies.py)：

- 模块自己的服务构造留在本模块
- 共享认证和权限依赖从 `app_setup/auth_dependencies.py` 引入
- 不要跨模块引用 `admin/api/dependencies.py`

### 4.6 路由接入

模块路由定义在 `api/v1/` 下，最后通过 `router.py` 聚合，再由 `manifest.py` 暴露给装配层。

参考：

- [admin/manifest.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/admin/manifest.py)
- [label_manager/manifest.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/label_manager/manifest.py)

## 5. 如何对接框架中的权限模块

### 5.1 先定义资源和动作语义

在写权限代码前，先明确：

- 资源类型，例如 `labels`、`orders`、`customers`
- 动作语义，例如 `view`、`edit`

不要直接把权限语义写成 URL 字符串和 if/else 组合。

### 5.2 API 权限接入

受保护接口统一通过 `require_permission()` 接入：

```python
@router.get(
    "",
    dependencies=[Depends(require_permission())],
)
async def list_items(...):
    ...
```

说明：

- `require_permission()` 来自 [auth_dependencies.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/auth_dependencies.py)
- 它会根据当前请求路径和方法调用 `IPermissionChecker`
- 业务服务不要直接操作 Casbin API

### 5.3 当前用户接入

业务模块默认通过 `CurrentPrincipal` 获取当前用户：

```python
async def handler(
    current_user: CurrentPrincipal = Depends(get_current_principal),
):
    operator_id = current_user.user_id
```

注意：

- 不要在业务模块里注入 `admin.domain.entities.User`
- 只有确实需要完整用户实体时，才根据 `current_user.user_id` 再调用应用服务查询

### 5.4 数据权限接入

当业务存在“只能看自己的数据”或“只能操作允许范围内数据”时，统一使用 `IDataScopeResolver`：

列表过滤：

```python
scope_filter = await data_scope_resolver.build_query_scope(
    user_id=current_user.user_id,
    resource_type="your_resource",
    action="view",
    model_cls=YourEntity,
)
```

实体校验：

```python
allowed = await data_scope_resolver.can_operate_entity(
    user_id=current_user.user_id,
    resource_type="your_resource",
    action="edit",
    entity=existing,
)
```

参考实现：

- [label_manager/api/v1/labels.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/label_manager/api/v1/labels.py)

### 5.5 资源映射注册

只要模块接入了数据权限，就必须在模块 `manifest.py` 中补充资源映射：

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

装配层会统一收集这些映射，不需要额外手写全局注册表。

### 5.6 权限种子与菜单种子

新增受保护接口后，需要同步补齐默认权限数据：

- API 权限种子
- 菜单权限种子
- 角色默认绑定关系

当前种子入口以 Alembic 管理为准，重点关注：

- `backend/alembic/versions/d0d6403df0d7_seed_default_admin_and_permissions.py`
- `backend/alembic/versions/init_permissions.sql`
- `backend/alembic/versions/init_user_data.sql`

不要把初始化权限逻辑写回 `init_db.py`。

### 5.7 什么时候使用 `IPermissionManager`

`IPermissionManager` 只适合：

- `admin` 模块执行权限投影同步
- 后台任务执行策略重试或同步
- 装配层初始化权限运行时相关能力

普通业务模块不要直接为了“判断有没有权限”去调用 `IPermissionManager`，判断场景只用 `IPermissionChecker`。

## 6. 模块级 Provider 如何使用

如果模块需要向全局暴露共享实现，可以使用 `ModuleManifest.provider_setup`。

当前 `admin` 就通过该机制注册：

- 当前用户解析实现
- 数据权限实现

参考：

- [providers.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/admin/providers.py)
- [provider_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/provider_registry.py)

适用场景：

- 模块需要向装配层注册共享 Provider
- 模块需要补充运行时依赖实现

不适用场景：

- 单纯构造本模块 service/repository
- 业务接口自己的普通依赖

## 7. 数据库与迁移规范

### 7.1 表结构约束

- 不创建数据库外键
- 主键使用雪花 ID
- 所有数据库 I/O 使用异步 `AsyncSession`

### 7.2 迁移规则

- 数据结构和种子数据统一通过 Alembic 管理
- 使用 `alembic revision` 生成迁移
- 不允许手改版本链路
- 不允许用 `alembic stamp` 伪造版本状态
- 不自动执行 `alembic upgrade head`

### 7.3 配置变更

每次修改 `config/settings.py` 的配置模型时，必须同步更新 `config.example.yaml`。

## 8. 测试与自检建议

新增模块后，至少补以下验证：

- 路由是否已通过 `manifest.py` 注册
- API 权限接口是否已加 `require_permission()`
- 数据权限资源是否已补资源映射
- 应用服务是否只依赖仓储抽象
- 请求模型和响应模型是否越层放置

推荐至少增加：

- 1 个聚焦单元测试验证模块装配
- 1 个权限拒绝或数据过滤场景测试
- 1 个应用服务核心规则测试

执行命令：

```bash
cd backend
uv run pytest tests/unit
```

## 9. 常见误区

- 在 `core/` 中引入具体业务模块
- 在 `app_setup/` 中硬编码具体业务仓储实现
- 跨模块复用别的模块 `api/dependencies.py`
- 直接依赖 Casbin Enforcer 或 Casbin API
- 把 API 响应模型放到 `application/contracts.py`
- 把业务数据库操作写进路由函数
- 把种子初始化写进 `init_db.py`

## 10. 新模块开发检查清单

开始开发前确认：

- 是否已定义资源类型和动作语义
- 是否已确定是否需要数据权限
- 是否已规划默认菜单和 API 权限种子

开发完成后确认：

- 是否已补齐 `api / application / domain / infra`
- 是否已提供模块级 `api/dependencies.py`
- 是否已补模块 `manifest.py`
- 是否已注册资源映射
- 是否已按需注册 `provider_setup`
- 是否已补 Alembic 迁移
- 是否已补最小测试
- 是否已更新 README 或相关文档

## 11. 推荐阅读顺序

建议后续开发者按以下顺序阅读：

1. [README.md](file:///Users/fengjun/code/python/FastAPI-Admin/README.md)
2. [CLAUDE.md](file:///Users/fengjun/code/python/FastAPI-Admin/CLAUDE.md)
3. [development_guide.md](file:///Users/fengjun/code/python/FastAPI-Admin/documentation/development_guide.md)
4. [permission_integration_guide.md](file:///Users/fengjun/code/python/FastAPI-Admin/documentation/permission_integration_guide.md)
5. `label_manager` 模块完整实现

## 12. 现成参考入口

最适合作为样板阅读的文件：

- [label_manager/manifest.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/label_manager/manifest.py)
- [label_manager/dependencies.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/label_manager/api/dependencies.py)
- [labels.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/modules/label_manager/api/v1/labels.py)
- [auth_dependencies.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/auth_dependencies.py)
- [provider_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/provider_registry.py)
- [resource_registry.py](file:///Users/fengjun/code/python/FastAPI-Admin/backend/app_setup/resource_registry.py)
