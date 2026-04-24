# FastAPI-Admin

基于 `FastAPI + Vue3` 的后台管理系统模板后端，当前模板内置：

- `admin` 管理模块
- `label_manager` 示例业务模块
- JWT 认证
- RBAC + Casbin API 权限
- 数据权限样板链路

## 目录说明

- `backend/`: 后端代码
- `documentation/`: 架构设计、整改方案、待办清单等文档
- `deployment.yaml`: 模板最小部署示例

## 环境要求

- Python `3.11+`
- MySQL `8+`
- Redis `6+`
- `uv`

## 快速开始

### 1. 安装依赖

```bash
cd backend
uv sync
```

### 2. 准备配置

复制模板配置并按实际环境修改：

```bash
cp config.example.yaml config.yaml
```

至少需要确认以下配置：

- `database_url`
- `secret_key`
- `redis.url`
- `token_issuer`
- `token_audience`

## 3. 初始化数据库

```bash
cd backend
uv run python init_db.py
```

说明：

- 当前 `init_db.py` 会检查数据库是否存在
- 然后执行 Alembic 迁移
- 默认管理员、系统角色、权限菜单等基础数据由 Alembic 数据迁移管理
- 默认管理员用户名为 `admin`
- 默认初始化密码为 `Admin@123456`，首次登录后应立即修改

## 4. 启动开发服务

```bash
cd backend
uv run python main.py
```

默认地址：

- API: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- 健康检查: `http://127.0.0.1:8000/health`

## 测试

执行当前最小测试基线：

```bash
cd backend
uv run pytest tests/unit
```

## 模板当前能力边界

当前模板只保留已实际交付并可运行的最小能力集合：

- `modules/admin`
- `modules/label_manager`
- `modules/iam`

如果继续基于模板扩展新业务模块，请先阅读：

- [CLAUDE.md](file:///Users/fengjun/code/python/FastAPI-Admin/CLAUDE.md)
- [permission_integration_guide.md](file:///Users/fengjun/code/python/FastAPI-Admin/documentation/permission_integration_guide.md)

## 权限接入约束

新增业务模块时，权限接入遵循以下规则：

- 当前用户统一依赖 `CurrentPrincipal`
- API 权限统一依赖 `IPermissionChecker`
- 数据权限统一依赖 `IDataScopeResolver`
- 权限同步与投影统一依赖 `IPermissionManager`
- 禁止新增模块直接依赖 Casbin 具体实现
- 禁止在 `app_setup` 中硬编码业务模块仓储或权限实现

## 系统角色规则

- 系统内置角色依赖 `role.code + is_system` 表达主语义
- 默认超级管理员角色通过数据库脚本初始化为稳定 `code`
- 所有通过接口创建的普通角色 `code` 统一使用 `role:{id}`

## 部署说明

根目录 [deployment.yaml](file:///Users/fengjun/code/python/FastAPI-Admin/deployment.yaml) 为模板最小 Kubernetes 部署样例，仅包含：

- 1 个 API Deployment
- 1 个 ClusterIP Service
- 1 份 ConfigMap
- 1 份 Secret

该清单默认依赖外部 MySQL 和 Redis，使用前请至少替换：

- 镜像地址
- `database_url`
- `secret_key`
- Redis 连接信息

### 容器镜像构建

当前仓库根目录 [Dockerfile](file:///Users/fengjun/code/python/FastAPI-Admin/Dockerfile) 已按 `uv workspace + backend` 布局调整，可直接在仓库根目录构建：

```bash
docker build -t fastapi-admin:latest .
```

### 初始化说明

部署前需先准备：

- 可访问的 MySQL 实例
- 可访问的 Redis 实例
- 对应的 `DATABASE_URL` 与 `SECRET_KEY`

首次启动前，建议先在后端目录执行数据库初始化：

```bash
cd backend
uv run python init_db.py
```

如果使用容器执行初始化，可基于同一镜像运行：

```bash
docker run --rm \
  -e DATABASE_URL='mysql+aiomysql://root:password@mysql:3306/fastapi_admin' \
  -e SECRET_KEY='change-me-in-production' \
  -e REDIS__URL='redis://redis:6379/0' \
  fastapi-admin:latest \
  python init_db.py
```

## 后续扩展建议

- 先基于 `label_manager` 样板扩展新业务模块
- 扩展前先补资源映射和权限动作语义
- 配置项变更必须同步 `config.example.yaml`
