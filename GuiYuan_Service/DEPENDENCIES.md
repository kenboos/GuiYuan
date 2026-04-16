# 归园服务端依赖文档

## 项目信息
- 项目名称: guiyuan-service
- 版本: 1.0.0
- Python 要求: >=3.11
- 框架: FastAPI

## 核心依赖

### Web 框架
- **fastapi>=0.115.0**
  - 用途: 现代、快速的 Web 框架，用于构建 API
  - 说明: 提供高性能的异步 API 支持，自动生成 API 文档

- **uvicorn[standard]>=0.30.0**
  - 用途: ASGI 服务器，用于运行 FastAPI 应用
  - 说明: [standard] 包含了额外的依赖，如 websockets、httptools 等

### 数据库相关
- **sqlalchemy[asyncio]>=2.0.0**
  - 用途: Python SQL 工具包和对象关系映射 (ORM)
  - 说明: [asyncio] 提供异步数据库操作支持

- **aiomysql>=0.2.0**
  - 用途: 异步 MySQL 驱动
  - 说明: 与 SQLAlchemy 配合使用，提供 MySQL 异步连接

- **alembic>=1.13.0**
  - 用途: 数据库迁移工具
  - 说明: 用于管理数据库 schema 变更和版本控制

### 数据验证
- **pydantic>=2.9.0**
  - 用途: 数据验证和设置管理
  - 说明: 使用 Python 类型注解进行数据验证

- **pydantic-settings>=2.6.0**
  - 用途: 从环境变量加载设置
  - 说明: 管理应用配置，支持从 .env 文件加载

### 认证和安全
- **python-jose[cryptography]>=3.3.0**
  - 用途: JWT (JSON Web Token) 处理
  - 说明: 用于生成和验证 JWT 令牌

### HTTP 客户端
- **httpx>=0.27.0**
  - 用途: 异步 HTTP 客户端
  - 说明: 用于发送 HTTP 请求，支持异步操作

### 缓存
- **redis>=5.1.0**
  - 用途: Redis 客户端
  - 说明: 用于缓存、会话管理等

### 文件上传
- **python-multipart>=0.0.12**
  - 用途: 处理多部分表单数据
  - 说明: 用于文件上传功能

## 开发依赖

### 代码质量
- **ruff>=0.7.0**
  - 用途: 快速的 Python 代码检查器和格式化工具
  - 说明: 替代 flake8、isort、black 等工具

### 测试
- **pytest>=8.3.0**
  - 用途: Python 测试框架
  - 说明: 用于编写和运行测试

- **pytest-asyncio>=0.24.0**
  - 用途: pytest 的异步测试支持
  - 说明: 用于测试异步函数

## 安装方法

### 1. 安装核心依赖
```bash
cd /Users/Mr.Zhang/Users/IMAC/Product/GuiYuan/Porject/GuiYuan_Service
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiomysql pydantic pydantic-settings python-jose[cryptography] httpx redis alembic python-multipart
```

### 2. 安装开发依赖
```bash
pip install ruff pytest pytest-asyncio
```

### 3. 一键安装所有依赖
```bash
cd /Users/Mr.Zhang/Users/IMAC/Product/GuiYuan/Porject/GuiYuan_Service
pip install -e .
```

或者使用 pip 直接安装：
```bash
cd /Users/Mr.Zhang/Users/IMAC/Product/GuiYuan/Porject/GuiYuan_Service
pip install .
```

### 4. 安装开发依赖（可选）
```bash
cd /Users/Mr.Zhang/Users/IMAC/Product/GuiYuan/Porject/GuiYuan_Service
pip install -e ".[dev]"
```

## 环境配置

在安装依赖后，请确保 `.env` 文件配置正确：

```env
# 服务
HOST=0.0.0.0
PORT=3000

# 数据库 MySQL 8.0
DATABASE_URL=mysql+aiomysql://root:root@localhost:3306/guiyuan



# Redis
REDIS_URL=redis://localhost:6379

# 微信小程序
WECHAT_APPID=your_appid
WECHAT_SECRET=your_secret

# JWT
JWT_SECRET=guiyuan_jwt_dev_secret_2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7
```

## 启动服务

安装完所有依赖后，可以使用以下命令启动服务：

```bash
cd /Users/Mr.Zhang/Users/IMAC/Product/GuiYuan/Porject/GuiYuan_Service
uvicorn app.main:app --reload
```

服务启动后，访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 实际安装版本

以下是成功安装的依赖版本：

- **FastAPI**: 0.128.0
- **SQLAlchemy**: 2.0.45
- **Pydantic**: 2.12.5
- **Uvicorn**: 0.39.0
- **pytest**: 8.4.2

## 验证安装

运行以下命令验证依赖是否安装成功：

```bash
python -c "import fastapi; print(f'FastAPI 版本: {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy 版本: {sqlalchemy.__version__}')"
python -c "import pydantic; print(f'Pydantic 版本: {pydantic.__version__}')"
python -c "import uvicorn; print(f'Uvicorn 版本: {uvicorn.__version__}')"
python -c "import pytest; print(f'pytest 版本: {pytest.__version__}')"
```

## 常见问题

### 1. MySQL 连接失败
确保 MySQL 服务已启动，并且连接信息正确。

### 2. Redis 连接失败
确保 Redis 服务已启动，或者可以暂时禁用 Redis 相关功能。

### 3. 依赖冲突
如果遇到依赖冲突，可以尝试使用虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 4. 权限问题
如果遇到权限问题，可以使用用户安装：
```bash
pip install --user .
```

### 5. pip 版本过旧
建议升级 pip 到最新版本：
```bash
/Library/Developer/CommandLineTools/usr/bin/python3 -m pip install --upgrade pip
```

### 6. 脚本路径不在 PATH 中
某些工具的脚本可能不在 PATH 中，可以添加到 PATH 或使用完整路径：
```bash
export PATH="$PATH:/Users/Mr.Zhang/Library/Python/3.9/bin"
```

## 依赖版本更新

定期更新依赖以获得安全修复和新功能：

```bash
pip list --outdated
pip install --upgrade package_name
```

## 总结

本项目的依赖主要包括：
- Web 框架: FastAPI + Uvicorn
- 数据库: SQLAlchemy + aiomysql + Alembic
- 数据验证: Pydantic
- 认证: python-jose
- 缓存: redis
- 测试: pytest + pytest-asyncio
- 代码质量: ruff

所有依赖都可以通过 `pip install -e .` 或 `pip install .` 安装。