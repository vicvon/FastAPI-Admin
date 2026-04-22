# 项目介绍

这是一个基于FastAPI+Vue3的后台管理系统模板，基于此项目可以快速搭建后台管理系统，该项目以内置 `admin` 管理模块提供基于RBAC模型的权限管理功能。

## 技术栈

- Python 3.11+ + FastAPI, Pydantic, SQLAlchemy (or SQLModel), Alembic, Casbin, casbin\_sqlalchemy\_adapter
- redis、mysql

## 相关命令

```shell
# 安装依赖, 在项目根目录执行
uv sync --all-packages
# 安装依赖, 在子目录执行
uv sync

# 添加依赖, 在项目根目录执行
uv add <package-name> --package backend
# 添加依赖, 在子目录执行
uv add <package-name>

# 格式化代码
uvx ruff format .

# 执行单元测试
uv run pytest
```

## 代码风格

Python 3.11+: Follow standard conventions

<!-- MANUAL ADDITIONS START -->

## 架构设计规范

### 1. 后端项目目录结构

```text
backend/
├── alembic/                      # Alembic 数据库迁移目录
│   ├── env.py                    # Alembic 环境配置
│   ├── script.py.mako            # Alembic 脚本模板
│   └── versions/                 # 数据库迁移版本目录
│
├── app_setup/                    # 应用装配层
│   ├── __init__.py
│   ├── app.py                    # create_app，负责应用实例装配
│   ├── router_registry.py        # 路由注册中心
│   ├── task_registry.py          # 后台任务注册中心
│   └── lifecycle.py              # 生命周期管理
│
├── common/                        # 通用代码, 不依赖具体业务模块
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── identity.py           # CurrentPrincipal 等共享身份抽象
│   ├── exceptions.py             # 通用异常
│   ├── constants.py              # 常量定义
│   ├── enums.py                  # 枚举类型
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── permission.py         # IPermissionChecker / IPermissionManager
│   │   └── data_scope.py         # IDataScopeResolver
│   ├── schemas.py                # 通用Schema
│   └── responses.py              # 统一响应格式
│
├── config/                        # 配置管理
│   ├── __init__.py
│   └── settings.py               # 应用配置
│
├── core/                          # 核心框架，包含全局依赖、中间件、安全等
│   ├── __init__.py
│   ├── base.py                   # 基类
│   │── database.py               # 数据库会话
│   ├── dependencies.py           # 全局依赖注入
│   ├── middleware.py             # 中间件
│   └── security.py               # 安全相关（JWT等）
│
├── modules/                       # 业务模块
│   ├── __init__.py
│   ├── iam/                      # 权限运行域，封装 Casbin 运行时能力
│   │   ├── application/
│   │   ├── domain/
│   │   └── infra/
│   └── xxxx/                     # xxx业务模块
│       ├── __init__.py
│       ├── api/                  # 接口层
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py         # 路由定义
│       │       ├── schemas.py        # 请求/响应模型
│       │       └── dependencies.py   # 模块依赖
│       │
│       ├── application/          # 应用层
│       │   ├── __init__.py
│       │   ├── services.py          # 应用服务
│       │   ├── contracts.py         # 应用层输入/契约模型
│       │   └── dto.py               # 数据传输对象
│       │
│       ├── domain/               # 领域层
│       │   ├── __init__.py
│       │   ├── entities.py          # 实体
│       │   ├── value_objects.py     # 值对象
│       │   ├── repositories.py      # 仓储接口
│       │   ├── services.py          # 领域服务
│       │   ├── events.py            # 领域事件
│       │   └── exceptions.py        # 领域异常
│       │
│       └── infra/                # 基础设施层
│           ├── __init__.py
│           ├── model.py             # ORM模型
│           ├── repositories.py      # 仓储实现
│           └── mappers.py           # 对象映射
│
├── tests/                         # 测试
│   ├── conftest.py                # pytest配置
│   ├── unit/                      # 单元测试
│   │   ├── domain/
│   │   │   └── test_xxxx.py       # 单元测试代码
│   │   └── application/
│   ├── integration/               # 集成测试
│   │   ├── api/
│   │   └── infra/
│   └── fixtures/                  # 测试夹具
│
├── utils/                         # 工具函数
│   ├── __init__.py
│   └── helpers.py                 # 辅助函数
│
├── main.py                        # 最小启动入口，只负责导入 create_app 和启动服务
├── pyproject.toml                 # 项目依赖管理
├── alembic.ini                    # Alembic 配置文件
└── README.md
```

### 2. 模块化与分层原则 (DDD)

- **Core 层纯净性**: `core/` 目录存放通用的基础设施和框架代码，**严禁**依赖具体的 `modules/` 业务代码。
  - _Anti-Pattern_: 在 `core/` 中导入 `modules.audit.domain.entities`。
- **应用装配层独立**: `app_setup/` 负责应用实例装配、路由注册、生命周期与后台任务治理；`main.py` 只作为最小启动入口，禁止继续堆积应用装配细节。
- **内置管理模块命名**: 后台模板内置的用户、角色、菜单、接口权限、数据权限等管理能力统一放在 `modules/admin/` 中，后续不要继续使用 `access_control` 作为模块名。
- **权限运行域独立**: `modules/iam/` 负责权限运行时能力，包括 `IPermissionChecker`、`IPermissionManager` 的实现、Casbin Enforcer 适配与权限投影；业务模块不得直接依赖 `core.casbin.*` 或具体 Enforcer。
- **业务模块自包含**: 每个业务模块应遵循 DDD 分层结构，包含 `domain` (实体), `application` (服务), `infra` (仓储实现), `api` (接口)。
- **职责分离**:
  - **Infrastructure Layer**: 负责所有 I/O 操作（数据库读写、外部 API 调用）。禁止在 Controller 或 Utility 中直接操作 DB Session。
  - **Application Layer**: 负责业务流程编排。
  - **Domain Layer**: 负责核心业务规则和实体定义。
  - **Repository Pattern**: 必须在 `domain/repositories.py` 中定义 Repository 抽象接口（继承 `abc.ABC`），并在 `infra/repositories.py` 中实现具体逻辑。应用层服务 (`application/services.py`) 必须依赖 Domain 层接口，严禁直接依赖 Infra 层实现。
  - **Application Contracts**: 应用层输入模型统一定义在 `application/contracts.py` 中；`application/services.py` **禁止**依赖 `api/v1/schemas.py`。如果接口层需要复用应用层输入模型，可以在 `api/v1/schemas.py` 中导入或再导出。
  - **API Schema 职责**: `api/v1/schemas.py` 负责请求/响应模型组织与对外接口表达；响应模型、展示模型保留在 API 层，请求契约和应用层输入模型优先放到 `application/contracts.py`。
  - **共享身份抽象**: 业务模块获取当前登录用户时，优先依赖 `common/auth/identity.py` 中的 `CurrentPrincipal`；除 `admin` 模块自身外，禁止将 `modules.admin.domain.entities.User` 作为跨模块共享身份模型。
  - **权限 Port 约束**: 业务模块做 API 权限校验时，必须依赖 `IPermissionChecker`；`admin` 配置域做权限投影与同步时，必须依赖 `IPermissionManager`；数据权限必须依赖 `IDataScopeResolver`。禁止新增模块直接依赖 `core.casbin.enforcer` 或 Casbin API。
  - **装配层权限依赖**: 共享的当前用户解析、权限校验和数据权限 Provider 统一通过 `app_setup/auth_dependencies.py` 与 `app_setup/permission_providers.py` 暴露；业务模块不得跨模块复用其他业务模块的 `api/dependencies.py`。

### 3. 数据库规范（手工补充）

- 数据表结构禁止使用外键（不创建 FK 约束；关联关系由应用层保证）
- 数据库表结构定义时，主键 id 用雪花算法生成（应用层生成 64-bit 整数 ID）
- 数据库迁移脚本使用alembic进行管理，严禁使用`alembic stamp`命令只修改`alembic_version`表中的版本ID，导致无法执行数据库变动的操作
- 数据库迁移脚本的生成必须使用`alembic revision`命令生成，严禁手动修改版本ID，破坏版本链路，具体命令参考alembic skill
- 严禁自动执行`alembic upgrade head`命令

### 4. 异步IO规范 (Async IO)

- **全栈异步**: 项目强制使用 Python 的 `asyncio` 异步编程模型以提升高并发性能。
- **数据库交互**:
  - 必须使用 `sqlmodel.ext.asyncio.session.AsyncSession` (基于 SQLAlchemy AsyncIO) 进行所有数据库操作。
  - 查询优先使用 `session.exec(select(...))`，避免使用 `session.execute(select(...)).scalars()` 这类旧写法。
  - **严禁**使用同步的 `Session` 或阻塞式 DB 驱动。
  - 数据库初始化脚本 (`init_db.py`) 也必须异步执行。
- **Web 接口**: 所有 FastAPI 路由处理函数 (`router` methods) 必须定义为 `async def`。
- **分层实现**:
  - **Repository**: 接口定义和实现类中的方法必须为 `async def`。
  - **Service**: 涉及 I/O 操作的业务逻辑方法必须为 `async def` 并 `await` 仓储层调用。
- **其他 I/O**: Redis 操作、HTTP 请求等外部调用均需使用异步客户端（如 `aioredis`, `httpx`）。

### 5. 配置模板同步规范

- **配置项变更必须同步模板**：每次在 `config/settings.py` 新增、删除或重命名配置项（含二级配置模型）时，必须同步更新 `config.example.yaml`，确保模板完整覆盖所有可配置项并提供合理示例值。

### 6. API 响应规范

所有后端服务接口统一采用以下 JSON 格式返回：

```json
{
    "code": 0,
    "message": "success",
    "data": {}
}
```

- `code`: 业务状态码，成功为 0，错误为正整数。
- `message`: 提示信息，成功为 "success"。
- `data`: 实际响应数据，可以为对象、列表或 null。

在`common/responses.py`中已经定义统一的响应模型, 所有后端接口统一使用这个模型定义。

- **ID 字段处理**: 所有涉及雪花算法生成的 64 位整数 ID（如主键 id），在 API 响应 Schema 中必须定义为字符串类型（或使用 `common.types.SnowflakeId`），以避免前端 JavaScript 发生精度丢失。

### 7. 异常处理规范

- **异常的定义**: 项目中使用的所有自定义异常都定义在`common/exceptions.py`中, 其他模块直接引用这个模块定义的异常, **禁止**在其他模块定义自定义异常。
- **异常的命名**: 所有自定义异常类名必须以 `Error` 结尾，例如 `ValidationError`, `PermissionError` 等。

### 8. 依赖注入规范

- **依赖注入**: 项目使用 `fastapi.Depends` 进行依赖注入, 所有公共的依赖项都在`core/dependencies.py`中定义, 接口需要使用依赖时先判断是否是公共依赖, 如果是公共依赖先检查`core/dependencies.py`中是否已经定义, 没有定义则在公共依赖文件中定义; 如果使用非公共依赖则在模块内定义使用。
- **模块级 Provider**: 模块内部的服务构造、仓储装配、应用服务工厂优先在模块内集中管理，避免在多个路由文件中重复手动实例化同一组仓储与服务。
- **权限 Provider 装配**: 权限运行时实例通过 `app_setup/permission_providers.py` 统一装配。禁止在路由、应用服务或后台任务中散落 new `PermissionCheckerImpl`、`PermissionManagerImpl`；如需构造权限管理器，应优先复用装配层暴露的工厂入口。

### 9. 权限开发规范

- **API 权限接入**: 新增接口时，先定义资源与动作语义，再通过 `require_permission()` 或后续基于 `IPermissionChecker` 的模块依赖接入权限校验；不要直接把 URL 路径字符串和 Casbin 细节写进业务服务。
- **数据权限接入**: 需要做数据行级过滤或实体级可操作校验时，统一通过 `IDataScopeResolver.build_query_scope()` 与 `IDataScopeResolver.can_operate_entity()` 接入；禁止新代码直接依赖 `DataPermissionContext`。
- **资源映射维护**: 资源映射由模块级 `manifest.py` 声明，并通过 `app_setup/resource_registry.py` 统一收集。新增业务模块时，必须同步补充对应资源映射；已经移除的业务模块映射必须及时删除，禁止长期保留历史残留资源。
- **权限配置真源**: 用户、角色、菜单、接口权限、数据权限规则等配置真源在 `modules/admin/`；Casbin 相关运行时投影由 `modules/iam/` 承接，禁止反向直接修改投影表来替代业务配置。
- **后台任务约束**: 涉及授权重试、权限投影、策略同步的后台任务必须通过 `IPermissionManager` 或装配层工厂接入，不得在任务中直接依赖具体 Casbin 实现。
- **系统角色语义**: 系统内置角色依赖 `role.code` 与 `is_system` 表达主语义，历史 `id == 1` 仅作兼容兜底。接口创建的普通角色 `code` 统一使用 `role:{id}`，内置角色的稳定 `code` 通过数据库初始化脚本写入。

### 10. 新增业务模块开发规范

- **模块创建步骤**: 新增业务模块时，至少补齐 `api / application / domain / infra` 四层骨架；涉及应用层输入时新增 `application/contracts.py`，不要直接把请求模型塞进 `api/v1/schemas.py` 后再让应用层反向依赖。
- **身份接入规则**: 业务模块需要当前用户信息时，优先依赖 `CurrentPrincipal`；禁止把 `admin.User` 当作跨模块通用身份对象传递。
- **权限接入步骤**: 新增模块需要权限能力时，先定义资源类型与动作，再接入 `IPermissionChecker` / `IDataScopeResolver`，最后补充 `resource_registry` 映射；不要先写业务代码再临时追加权限判断。
- **装配约束**: 模块内部服务装配、仓储构造、Provider 依赖应集中在模块自己的 `api/dependencies.py`；若需要权限运行时能力，应通过装配层或现有 Provider 获取，不得绕过装配层直接实例化。
- **模板收口要求**: 作为模板分发前，必须清理与当前模板无关的模块引用、资源映射、配置项和文档说明，保证模板只包含真实可运行的最小业务集合。

### 11.第三方依赖使用规范

- **Pydantic**：
  - Pydantic使用V2.0+版本, 不要使用在V2.0中已经废弃**deprecated**的特性

<!-- MANUAL ADDITIONS END -->
