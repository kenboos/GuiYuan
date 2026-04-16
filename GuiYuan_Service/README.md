# 归园服务端 (GuiYuan Service) — Python 版

> 在线农场 x 线下实地 — FastAPI + MySQL + SQLAlchemy(async)

## 技术栈

| 技术 | 说明 |
|------|------|
| **框架** | FastAPI |
| **语言** | Python 3.11+ (ESM) |
| **ORM** | SQLAlchemy 2.x (async) |
| **数据库** | MySQL 8.0 + Redis |
| **认证** | JWT (python-jose) |
| **验证** | Pydantic v2 |
| **配置管理** | pydantic-settings |
| **数据迁移** | Alembic |

## 项目结构

```
GuiYuan_Service/
├── app/
│   ├── main.py              # 应用入口 (FastAPI实例 + 全局中间件 + 异常处理)
│   ├── config.py             # 环境变量加载 (pydantic-settings)
│   ├── db.py                 # 异步引擎 + Session 工厂 + Base 模型基类
│   ├── models/__init__.py   # 13张表 SQLAlchemy ORM 定义
│   ├── schemas/__init__.py   # Pydantic 请求/响应模型定义
│   ├── core/
│   │   ├── deps.py           # JWT 认证依赖注入 (get_current_user / get_optional_user / create_token)
│   │   └── exceptions.py     # 统一业务异常类 + 预定义错误码常量
│   ├── utils/
│   │   ├── response.py       # ok() / paginated() 响应工具函数
│   │   └── common.py         # 订单号生成等通用函数
│   ├── api/v1/
│   │   ├── router.py         # 路由注册中心 (统一 /api 前缀)
│   │   ├── auth_router.py    # POST /login (微信code换openid) + POST /refresh
│   │   ├── user_router.py    # GET/PUT /info
│   │   ├── plot_router.py    # 地块CRUD + 购买 + 装饰 + 种植 + 托管 + 生长日志/状态
│   │   ├── coin_router.py    # 余额查询 / 充值(5档位) / 交易记录
│   │   ├── plant_router.py   # 作物列表(分类) / 详情 / 种植订单
│   │   ├── decoration_router.py  # 装饰商品(fence/landscape分组) / 详情
│   │   ├── hosting_router.py     # 托管套餐 / 服务记录
│   │   ├── order_router.py   # 订单列表/详情/支付/取消
│   │   ├── payment_router.py    # 微信支付回调 (XML格式返回)
│   │   └── admin_router.py   # 管理后台 (登录/Dashboard/用户/地块/订单/日志)
│   ├── services/
│   │   └── coin_service.py   # 支付回调处理服务
│   └── jobs/
│       └── scheduler.py      # 定时任务 (托管到期/生长阶段/订单超时/日报统计)
├── alembic/                  # 数据库迁移目录
│   ├── env.py                # 迁移环境配置 (async模式)
│   └── script.py.mako        # 迁移脚本模板
├── alembic.ini               # Alembic 配置
├── pyproject.toml            # Python 项目依赖
├── .env / .env.example       # 环境变量
└── README.md                 # 本文档
```

## 快速开始

### 前置条件

- Python >= 3.11
- MySQL 8.0+
- Redis（可选）

### 1. 创建虚拟环境并安装依赖

```bash
cd Porject/GuiYuan_Service

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写以下关键配置：
```

```env
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/guiyuan
WECHAT_APPID=wx你的appid
WECHAT_SECRET=your_secret
JWT_SECRET=自定义随机密钥
```

### 3. 初始化数据库

```bash
# 方式一：自动建表（开发阶段）
# 启动应用时会自动执行 Base.metadata.create_all()

# 方式二：使用 Alembic 迁移（推荐生产环境）
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 4. 启动开发服务器

```bash
uvicorn app.main:app --reload --port 3000 --host 0.0.0.0
```

访问 `http://localhost:3000/health` 验证服务正常运行。

### 5. 构建生产版本

```bash
# 使用 gunicorn 运行 (推荐)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000

# 或直接用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## API 接口说明

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

### 错误码表

| 码段 | 错误码 | 说明 | 所属模块 |
|------|--------|------|----------|
| 0 | 0 | 成功 | — |
| 1xx | 1001 | 参数错误 | 通用 |
| 1xx | 1002 | 服务器内部错误 | 通用 |
| 2xx | 2001 | Token已过期 | 认证 |
| 2xx | 2002 | Token无效 | 认证 |
| 4xx | 4001 | 地块不存在 | 地块 |
| 4xx | 4002 | 地块已售出 | 地块 |
| 5xx | 5001 | 订单不存在 | 订单 |
| 5xx | 5002 | 订单已支付 | 订单 |
| 7xx | 7001 | C币余额不足 | C币 |
| 8xx | 8001 | 托管套餐不存在 | 托管 |

---

### 一、认证 `/api/auth`（无需Token）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/login` | 微信登录 → 返回JWT |
| `POST` | `/refresh` | 刷新Token |

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code": "wx_login_code"}'

# 响应示例
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOi...",
    "expire_in": 604800,
    "user": { "id": "...", "nickname": "归园用户a3f1", "cCoin": 0 }
  }
}
```

后续请求携带：`Authorization: Bearer {token}`

---

### 二、用户 `/api/user`（需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/info` | 用户信息(C币、地块数等) |
| `PUT` | `/info` | 更新昵称/头像 |

---

### 三、地块 `/api/plots`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/` | 地块列表(status/area筛选) | 可选 |
| `GET` | `/{id}` | 地块详情(+拥有者信息) | 可选 |
| `POST` | `/{id}/purchase` | 购买地块(扣C币) | 必须 |
| `GET` | `/{id}/decoration` | 装饰状态 | 必须 |
| `POST` | `/{id}/decoration` | 保存装饰方案(扣C币) | 必须 |
| `GET` | `/{id}/plantings` | 种植记录 | 必须 |
| `GET` | `/{id}/hosting` | 托管状态 | 必须 |
| `POST` | `/{id}/hosting` | 购买托管(扣C币) | 必须 |
| `GET` | `/{id}/growth-logs` | 生长日志(分页) | 必须 |
| `GET` | `/{id}/growth-status` | 生长状态概览 | 必须 |

**购买地块请求体：**
```json
{ "decorationId": "可选" }
```

**保存装饰请求体：**
```json
{
  "items": [
    { "itemId": "fence_wood", "position": { "x": 10, "y": 20 } },
    { "itemId": "path_stone" }
  ]
}
```

**购买托管请求体：**
```json
{ "packageId": "hosting_basic", "year": 1 }
```

---

### 四、C币 `/api/coin`（需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/balance` | C币余额 |
| `POST` | `/recharge` | 创建充值订单 |
| `GET` | `/transactions` | 交易记录(分页) |

**充值档位(tier)：**
| tier | 实付(¥) | 到账C币 | 赠送 |
|------|---------|---------|------|
| basic | ¥10 | 100 | — |
| standard | ¥30 | 320 | +6.7% |
| premium | ¥100 | 1100 | +10% |
| gold | ¥300 | 3600 | +20% |
| platinum | ¥1000 | 13000 | +30% |

---

### 五、作物 `/api/plants`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/` | 作物列表(vegetables/fruits分组) | 可选 |
| `GET` | `/{id}` | 作物详情 | 可选 |
| `POST` | `/{id}/order` | 创建种植订单 | 必须 |

---

### 六、装饰 `/api/decorations`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/` | 商品列表(fence/landscape) | 可选 |
| `GET` | `/{id}` | 商品详情 | 必须 |

---

### 七、托管 `/api/hosting`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/packages` | 套餐列表(基础/标准/尊享) | 可选 |
| `GET` | `/plots/{id}/logs` | 服务记录(分页) | 必须 |

**套餐：**
- **基础** 800C/年 — 浇水、除草
- **标准** 1500C/年 — +施肥、病虫害防治
- **尊享** 2800C/年 — +专属管家、24h监控

---

### 八、订单 `/api/orders`（需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 订单列表(type/status筛选) |
| `GET` | `/{id}` | 订单详情 |
| `POST` | `/{id}/pay` | 支付订单 |
| `POST` | `/{id}/cancel` | 取消订单 |

**订单类型：** `plot_purchase` / `coin_recharge` / `decoration` / `planting` / `hosting`
**订单状态：** `pending` → `paid` → `completed` / `cancelled` / `refunded`

---

### 九、支付回调 `/api/payment`（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/wechat/notify` | 微信支付异步通知(XML响应) |

---

### 十、管理后台 `/api/admin`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/login` | 管理员登录(JWT) |
| `GET` | `/dashboard` | Dashboard统计 |
| `GET` | `/users` | 用户列表 |
| `GET` | `/plots` | 地块列表(含销售信息) |
| `POST` | `/plots` | 新增地块 |
| `PUT` | `/plots/{id}` | 编辑地块 |
| `GET` | `/orders` | 全部订单管理 |
| `GET` | `/growth-logs` | 生长日志列表 |
| `POST` | `/growth-logs` | 新增生长日志 |

---

## 数据库模型（13张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `users` | 用户 | openid, c_coin |
| `admins` | 管理员 | username, role |
| `plots` | 地块 | name, area, price, status, lat/lng, owner_id |
| `plot_decorations` | 地块装饰 | plot_id, items(JSON), total_cost |
| `decoration_items` | 装饰商品 | type(fence/landscape), price |
| `plants` | 作物 | category, price, growth_cycle, season(JSON) |
| `plantings` | 种植记录 | plot_id, plant_id, area, status |
| `hosting_packages` | 托管套餐 | name, price_per_year, services(JSON) |
| `hostings` | 托管服务 | package_id, years, start_date, end_date |
| `hosting_logs` | 托管日志 | service, images(JSON), staff_name |
| `orders` | 订单 | type, amount, currency, status, trade_no |
| `transactions` | C币流水 | type, amount, balance |
| `growth_logs` | 生长日志 | stage, images(JSON), care_actions(JSON) |

完整 ORM 定义见 `app/models/__init__.py`。

---

## 定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| `order_auto_cancel` | 每15分钟 | 取消超时未支付订单(15分钟) |
| `hosting_expire_check` | 每15分钟 | 托管到期提醒 + 自动停用过期托管 |
| `growth_stage_update` | 每15分钟 | 更新种植记录的生长阶段(seeding→germination→growing→flowering→fruiting→harvesting) |
| `stats_daily_report` | 每15分钟 | 生成每日运营日报 |

开发模式下使用线程 + 循环模拟；生产建议使用 APScheduler 或 Celery Beat。

---

## 部署指南

### 开发部署

```bash
cd Porject/GuiYuan_Service
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env && vim .env
alembic upgrade head          # 初始化数据库
uvicorn app.main:app --reload --port 3000
```

### 生产部署

#### 方式A：Gunicorn + Uvicorn Worker（推荐）

```bash
pip install gunicorn
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:3000 \
  --access-logfile - \
  --error-logfile -
```

使用 supervisor/systemd 守护进程：

```ini
# /etc/supervisor/conf.d/guiyuan.conf
[program:guiyuan-service]
command=/path/to/.venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000
directory=/path/to/GuiYuan_Service
user=www-data
autostart=true
autorestart=true
environment=DATABASE_URL="mysql+aiomysql://...",JWT_SECRET="..."
```

#### 方式B：Docker Compose

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e "." --no-cache-dir
COPY . .
RUN pip install gunicorn
EXPOSE 3000
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:3000"]
```

```yaml
# docker-compose.yml
version: '3.9'
services:
  web:
    build: .
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: mysql+aiomysql://root:pass@mysql:3306/guiyuan
      REDIS_URL: redis://redis:6379
      WECHAT_APPID: ${WECHAT_APPID}
      WECHAT_SECRET: ${WECHAT_SECRET}
      JWT_SECRET: ${JWT_SECRET}
    depends_on: [mysql, redis]

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: guiyuan
    volumes: [mysql_data:/var/lib/mysql]
    ports: ["3306:3306"]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

volumes:
  mysql_data:
  redis_data:
```

#### Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name api.guiyuan.farm;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    client_max_body_size 10m;
}
```

### 数据库种子数据

首次部署后需要导入基础数据：
- 管理员账号
- 地块列表（编号、面积、价格、坐标）
- 装饰商品（篱笆/景观）
- 作物品种（蔬菜/瓜果）
- 托管套餐（3档）

可在 `app/jobs/` 下创建 seed 脚本。

---

## 注意事项

1. **微信支付对接** — 当前为框架结构，需在腾讯商户平台获取 MCH_ID/API_KEY/证书，实现 V3 签名和回调验签
2. **密码安全** — 生产环境务必使用 bcrypt 替代明文密码比较
3. **CORS 配置** — 生产环境将 origin 限制为小程序合法域名
4. **Redis 缓存** — 已预留连接配置，可接入热点数据缓存/限流场景
5. **定时任务生产化** — 建议替换线程循环为 APScheduler 或 Celery Beat
6. **环境变量安全** — `.env` 已在 `.gitignore` 中，切勿提交代码仓库
