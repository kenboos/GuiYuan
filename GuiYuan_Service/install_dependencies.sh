#!/bin/bash

# 归园服务端依赖安装脚本

echo "======================================"
echo "归园服务端依赖安装"
echo "======================================"

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $python_version"

# 检查是否满足最低要求
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "错误: Python 版本需要 >= 3.11"
    exit 1
fi

echo "Python 版本满足要求"
echo ""

# 安装核心依赖
echo "======================================"
echo "安装核心依赖..."
echo "======================================"

pip install fastapi>=0.115.0
pip install uvicorn[standard]>=0.30.0
pip install sqlalchemy[asyncio]>=2.0.0
pip install aiomysql>=0.2.0
pip install pydantic>=2.9.0
pip install pydantic-settings>=2.6.0
pip install python-jose[cryptography]>=3.3.0
pip install httpx>=0.27.0
pip install redis>=5.1.0
pip install alembic>=1.13.0
pip install python-multipart>=0.0.12

echo "核心依赖安装完成"
echo ""

# 安装开发依赖
echo "======================================"
echo "安装开发依赖..."
echo "======================================"

pip install ruff>=0.7.0
pip install pytest>=8.3.0
pip install pytest-asyncio>=0.24.0

echo "开发依赖安装完成"
echo ""

# 验证安装
echo "======================================"
echo "验证依赖安装..."
echo "======================================"

echo "FastAPI 版本:"
python3 -c "import fastapi; print(fastapi.__version__)" 2>/dev/null || echo "未安装"

echo "SQLAlchemy 版本:"
python3 -c "import sqlalchemy; print(sqlalchemy.__version__)" 2>/dev/null || echo "未安装"

echo "Pydantic 版本:"
python3 -c "import pydantic; print(pydantic.__version__)" 2>/dev/null || echo "未安装"

echo "Uvicorn 版本:"
python3 -c "import uvicorn; print(uvicorn.__version__)" 2>/dev/null || echo "未安装"

echo "pytest 版本:"
python3 -c "import pytest; print(pytest.__version__)" 2>/dev/null || echo "未安装"

echo ""
echo "======================================"
echo "依赖安装完成！"
echo "======================================"
echo ""
echo "下一步:"
echo "1. 确保 .env 文件配置正确"
echo "2. 启动服务: uvicorn app.main:app --reload"
echo "3. 访问 API 文档: http://localhost:8000/docs"
echo ""