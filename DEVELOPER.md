# KamiPro 开发文档

> 本文档提供 KamiPro 的 API 调用规范和插件开发指南。

---

## 目录

1. [API 调用规范](#api-调用规范)
2. [插件开发指南](#插件开发指南)
3. [全局插件开发](#全局插件开发)
4. [常用工具函数](#常用工具函数)

---

## API 调用规范

### 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://localhost:8000/api/v1` |
| 认证方式 | Bearer Token (JWT) |
| 内容类型 | `application/json` |

### 认证

#### 登录获取 Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

**响应：**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

#### 使用 Token

在请求头中添加：
```http
Authorization: Bearer <access_token>
```

### 主要 API 端点

#### 统计数据
```http
GET /api/v1/stats          # 获取系统统计
```

#### 卡密管理
```http
GET    /api/v1/kami              # 获取卡密列表
POST   /api/v1/kami              # 创建卡密
DELETE /api/v1/kami/{id}         # 删除卡密
POST   /api/v1/kami/batch        # 批量生成卡密
```

#### 群组管理
```http
GET    /api/v1/groups            # 获取群组列表
POST   /api/v1/groups/{id}/auth  # 授权群组
DELETE /api/v1/groups/{id}/auth  # 取消授权
```

#### 会员管理
```http
GET  /api/v1/members             # 获取会员列表
GET  /api/v1/members/stats       # 获取会员统计
GET  /api/v1/members/{qq}        # 获取会员详情
POST /api/v1/members/{qq}/adjust # 调整余额/积分
POST /api/v1/members/{qq}/ban    # 封禁/解封会员
```

#### 充值订单
```http
GET    /api/v1/recharge              # 获取订单列表
GET    /api/v1/recharge/stats        # 获取订单统计
DELETE /api/v1/recharge/{id}         # 删除订单
POST   /api/v1/recharge/batch-delete # 批量删除
POST   /api/v1/recharge/clear-useless # 清除无用订单
```

#### 插件管理
```http
GET    /api/v1/plugins                    # 获取插件列表
POST   /api/v1/plugins/{id}/toggle        # 启用/禁用插件
POST   /api/v1/plugins/{id}/reload        # 热重载插件
POST   /api/v1/plugins/install            # 安装插件
DELETE /api/v1/plugins/{id}               # 卸载插件
GET    /api/v1/plugins/{id}/config        # 获取插件配置
POST   /api/v1/plugins/{id}/config        # 保存插件配置
GET    /api/v1/plugins/market             # 获取云端市场
```

#### 系统设置
```http
GET  /api/v1/system/config       # 获取系统配置
POST /api/v1/system/config       # 保存系统配置
```

### 错误响应

```json
{
    "detail": "错误描述信息"
}
```

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 插件开发指南

### 插件目录结构

```
backend/plugins/
└── my_plugin/
    ├── manifest.json      # 插件元信息（必需）
    ├── main.py            # 插件入口（必需）
    ├── config_schema.json # 配置表单定义（可选）
    └── requirements.txt   # 依赖包（可选，自动安装）
```

### manifest.json

```json
{
    "id": "my_plugin",
    "name": "我的插件",
    "version": "1.0.0",
    "author": "开发者",
    "description": "插件功能描述",
    "main": "main.py",
    "plugin_type": "qq"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | ✅ | 插件唯一标识，小写字母+下划线 |
| name | string | ✅ | 插件显示名称 |
| version | string | ✅ | 版本号，如 "1.0.0" |
| author | string | ✅ | 作者名称 |
| description | string | ✅ | 功能描述 |
| main | string | ✅ | 入口文件名 |
| plugin_type | string | ❌ | 插件类型：`qq`(默认) 或 `global` |

### main.py 基础模板

```python
"""
插件名称
插件描述
"""

def register(bot, config: dict = None):
    """
    插件注册时调用
    
    Args:
        bot: KamiBot 实例，用于注册命令和监听器
        config: 插件配置字典（如果有 config_schema.json）
    """
    
    # 注册命令监听器
    @bot.on_command("测试")
    async def handle_test(event):
        await event.reply("Hello World!")
    
    # 注册消息监听器（所有消息）
    @bot.on_message()
    async def handle_message(event):
        if "关键词" in event.message:
            await event.reply("检测到关键词")
    
    print("✅ 插件已加载")


def unregister(bot):
    """
    插件卸载时调用
    用于清理资源、取消监听器等
    """
    print("❌ 插件已卸载")
```

### MessageEvent 对象

```python
class MessageEvent:
    message: str          # 消息内容
    user_id: str          # 发送者QQ号
    group_id: str | None  # 群号（私聊为None）
    message_id: str       # 消息ID
    raw_message: str      # 原始消息
    
    async def reply(self, text: str):
        """回复消息"""
        
    async def send_private(self, user_id: str, text: str):
        """发送私聊消息"""
```

### 命令监听器

```python
@bot.on_command("签到")
async def handle_sign(event):
    """处理 "签到" 命令"""
    await event.reply(f"签到成功！")

@bot.on_command("查询", "余额")  # 多个触发词
async def handle_query(event, args: str):
    """
    处理 "查询 xxx" 或 "余额 xxx" 命令
    args: 命令后的参数，如 "查询 张三" 中的 "张三"
    """
    await event.reply(f"查询参数: {args}")
```

### 消息监听器

```python
@bot.on_message()
async def handle_all_messages(event):
    """监听所有消息"""
    print(f"收到消息: {event.message}")

@bot.on_message(group_only=True)
async def handle_group_messages(event):
    """仅监听群消息"""
    pass

@bot.on_message(private_only=True)
async def handle_private_messages(event):
    """仅监听私聊消息"""
    pass
```

### 配置表单 (config_schema.json)

```json
[
    {
        "name": "api_key",
        "label": "API密钥",
        "type": "password",
        "default": "",
        "placeholder": "请输入API密钥",
        "description": "用于调用外部API的密钥"
    },
    {
        "name": "enabled_groups",
        "label": "启用群组",
        "type": "text",
        "default": "",
        "placeholder": "群号用逗号分隔",
        "description": "限制插件生效的群组"
    },
    {
        "name": "max_count",
        "label": "最大次数",
        "type": "number",
        "default": 10,
        "description": "每日最大使用次数"
    }
]
```

**支持的字段类型：**

| type | 说明 |
|------|------|
| text | 单行文本 |
| password | 密码（隐藏显示） |
| number | 数字 |
| textarea | 多行文本 |
| select | 下拉选择 |
| checkbox | 复选框 |

### 使用配置

```python
def register(bot, config: dict = None):
    api_key = config.get('api_key', '') if config else ''
    max_count = config.get('max_count', 10) if config else 10
    
    @bot.on_command("功能")
    async def handle(event):
        if not api_key:
            await event.reply("请先配置API密钥")
            return
        # 使用配置...


def on_config_change(new_config: dict):
    """配置变更时调用（可选）"""
    global api_key
    api_key = new_config.get('api_key', '')
```

### 调用后端 API

```python
import httpx

API_BASE = "http://localhost:8000/api/v1"

async def call_api():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # GET 请求
        resp = await client.get(f"{API_BASE}/members/stats")
        data = resp.json()
        
        # POST 请求
        resp = await client.post(
            f"{API_BASE}/members/123456/adjust",
            json={"points": 100, "reason": "奖励"}
        )
```

### 数据库操作

```python
from app.database.mysql import AsyncSessionLocal
from app.database.models import Member
from sqlalchemy import select

async def get_member(qq: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Member).where(Member.qq == qq)
        )
        return result.scalar_one_or_none()
```

---

## 全局插件开发

全局插件提供系统级服务，供其他插件或模块调用。

### manifest.json

```json
{
    "id": "my_service",
    "name": "我的服务",
    "version": "1.0.0",
    "author": "开发者",
    "description": "提供xxx服务",
    "main": "main.py",
    "plugin_type": "global"
}
```

### main.py 模板

```python
"""
全局服务插件
"""
from typing import Dict, Any

_config: Dict[str, Any] = {}

def register(bot=None, config: dict = None):
    """注册时调用"""
    global _config
    if config:
        _config = config
    print("🔧 服务已启动")

def unregister(bot=None):
    """卸载时调用"""
    global _config
    _config = {}
    print("🔧 服务已停止")

def on_config_change(new_config: dict):
    """配置变更时调用"""
    global _config
    _config = new_config

# ========== 对外提供的服务接口 ==========

def is_configured() -> bool:
    """检查是否已配置"""
    return bool(_config.get('api_key'))

async def do_something(param: str) -> dict:
    """
    服务方法
    
    Args:
        param: 参数说明
    
    Returns:
        {"success": True, "data": ...}
    """
    if not is_configured():
        return {"success": False, "error": "服务未配置"}
    
    # 业务逻辑...
    return {"success": True, "data": "result"}
```

### 调用全局插件

```python
from app.core.plugin_manager import plugin_manager

# 获取全局插件模块
service = plugin_manager.loaded_plugins.get('my_service')

if service and service.is_configured():
    result = await service.do_something("参数")
    if result['success']:
        print(result['data'])
```

### 示例：易支付服务

```python
from app.core.plugin_manager import plugin_manager

async def create_order(order_no: str, amount: float):
    epay = plugin_manager.loaded_plugins.get('epay_service')
    
    if not epay:
        return {"error": "支付服务未安装"}
    
    if not epay.is_configured():
        return {"error": "支付服务未配置"}
    
    result = await epay.create_payment(
        order_no=order_no,
        amount=amount,
        name="商品购买",
        pay_type="alipay"
    )
    
    return result
```

---

## 常用工具函数

### 缓存服务

```python
from app.core.cache import cache_service

# 设置缓存
await cache_service.set("key", "value", ttl=3600)

# 获取缓存
value = await cache_service.get("key")

# 删除缓存
await cache_service.delete("key")

# 缓存装饰器
@cache_service.cached(ttl=300)
async def get_data(param):
    return expensive_operation(param)
```

### 日志记录

```python
from app.core.logger import log_manager

log_manager.info("普通日志")
log_manager.warning("警告日志")
log_manager.error("错误日志")
log_manager.bot("机器人相关日志")
```

### HTTP 客户端

```python
import httpx

async def fetch_data(url: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
```

---

## 最佳实践

1. **错误处理** - 使用 try-except 捕获异常，避免插件崩溃影响系统
2. **资源清理** - 在 `unregister` 中清理定时任务、连接等资源
3. **配置验证** - 在使用配置前检查必要字段是否存在
4. **日志记录** - 关键操作添加日志，便于调试
5. **异步编程** - 使用 async/await，避免阻塞主线程

---

## 更新日志

- **v1.0.0** (2026-01-24) - 初始版本
