"""
NovaTech 3C电商智能客服 — API 服务
物流查询：对接快递100真实API + 订单存在性前置校验
库存查询：本地数据（模拟ERP库存系统）

启动方式：
    pip install -r requirements.txt
    python main.py
    # 服务运行在 http://localhost:3000

数据配置：
    修改 data/ 目录下的 JSON 文件即可更新订单和库存数据，无需改代码

快递100配置：
    1. 注册 https://www.kuaidi100.com 账号
    2. 开放平台 → 获取 customer 和 key
    3. 填入 .env 文件或直接写在下方配置
"""

import hashlib
import json
import os
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ==================== 环境变量 ====================
load_dotenv(Path(__file__).parent.parent / ".env")

# 快递100 API 配置
KUAIDI100_CUSTOMER = os.getenv("KUAIDI100_CUSTOMER", "")
KUAIDI100_KEY = os.getenv("KUAIDI100_KEY", "")

# ==================== 数据加载 ====================
DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str):
    """加载 JSON 配置文件"""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# 启动时加载一次，运行期间常驻内存
ORDERS = load_json("orders.json")
STOCKS = load_json("stocks.json")
PRODUCTS = load_json("products.json")


# ==================== 快递100 API 对接 ====================
async def query_kuaidi100(com: str, num: str, phone: str = ""):
    """
    调用快递100实时查询接口
    官方文档：https://www.kuaidi100.com/openapi/api_post.shtml

    参数：
        com: 快递公司编码（如 shunfeng, jd, zhongtong, yuantong）
        num: 快递单号
        phone: 手机号（顺丰、京东需要，其他可不填）
    返回：
        物流轨迹列表
    """
    if not KUAIDI100_CUSTOMER or not KUAIDI100_KEY:
        # 未配置快递100，返回提示
        return None, "快递100 API 未配置，请在 .env 中设置 KUAIDI100_CUSTOMER 和 KUAIDI100_KEY"

    # 快递100签名规则：MD5(param + key + customer) 然后转大写
    # 注意：param 是完整的 JSON 字符串，不是单号
    param_str = json.dumps({
        "com": com,
        "num": num,
        "phone": phone,
        "fromv": "",
        "tov": "",
        "resultv2": "4",
    }, separators=(",", ":"))  # 紧凑JSON，避免空格影响签名

    sign_str = param_str + KUAIDI100_KEY + KUAIDI100_CUSTOMER
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    params = {
        "customer": KUAIDI100_CUSTOMER,
        "sign": sign,
        "param": param_str,
    }

    url = "https://poll.kuaidi100.com/poll/query.do"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, data=params)
        result = resp.json()

    if result.get("status") == "200":
        return result.get("data"), None
    elif result.get("status") == "408":
        return None, "快递100接口超时，请稍后重试"
    elif result.get("status") in ("401", "403"):
        return None, "快递100鉴权失败，请检查 customer 和 key"
    else:
        return None, result.get("message", "快递100查询失败")


# ==================== 快递公司编码映射 ====================
# 订单数据里的快递名称 → 快递100的快递公司编码
EXPRESS_CODE_MAP = {
    "顺丰速运": "shunfeng",
    "顺丰": "shunfeng",
    "京东物流": "jd",
    "中通快递": "zhongtong",
    "圆通速递": "yuantong",
    "韵达快递": "yunda",
    "申通快递": "shentong",
    "邮政快递": "ems",
    "极兔速递": "jtexpress",
    "丰网速运": "fengwang",
}


# ==================== FastAPI 应用 ====================
app = FastAPI(title="NovaTech Customer Service API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["健康检查"])
def root():
    return {
        "status": "ok",
        "service": "NovaTech Customer Service API",
        "version": "2.0.0",
        "kuaidi100_configured": bool(KUAIDI100_CUSTOMER and KUAIDI100_KEY),
    }


@app.get("/api/logistics", tags=["物流查询"])
async def query_logistics(order_id: str = Query(..., description="订单号，如 NV202609080001")):
    """
    物流查询接口 — Dify HTTP请求节点调用

    业务逻辑：
    1. 先校验订单号是否存在于本地系统（防恶意请求 + 省API调用费）
    2. 订单存在 → 调用快递100真实API获取物流轨迹
    3. 订单不存在 → 直接返回，不调用快递100
    """
    # 第一步：订单存在性前置校验
    order = ORDERS.get(order_id)
    if not order:
        return {
            "found": False,
            "message": f"订单号 {order_id} 不存在，请确认订单号是否正确",
            "call_kuaidi100": False,  # 未调用，省钱
        }

    # 第二步：订单存在，调用快递100真实API
    express_name = order.get("express", "")
    express_code = EXPRESS_CODE_MAP.get(express_name, "")
    tracking_no = order.get("tracking_no", "")
    phone = order.get("phone", "")  # 顺丰/京东需要手机号

    tracks, error = await query_kuaidi100(express_code, tracking_no, phone)

    if error:
        # 快递100调用失败，回退到本地缓存的状态信息
        return {
            "found": True,
            "order_id": order["order_id"],
            "product": order["product"],
            "storage": order.get("storage", ""),
            "express": express_name,
            "tracking_no": tracking_no,
            "status": order.get("status", ""),
            "current_location": order.get("current_location", ""),
            "estimated_arrival": order.get("estimated_arrival", ""),
            "call_kuaidi100": True,
            "kuaidi100_error": error,
            "tracks": None,
            "note": "快递100接口异常，显示本地缓存信息"
        }

    # 第三步：返回真实物流轨迹
    # 快递100返回的 tracks 是一个列表，每条包含时间、地点、状态
    last_track = tracks[0] if tracks else None  # 最新的轨迹

    return {
        "found": True,
        "order_id": order["order_id"],
        "product": order["product"],
        "storage": order.get("storage", ""),
        "express": express_name,
        "tracking_no": tracking_no,
        "status": "运输中" if last_track else "待发货",
        "last_update": last_track.get("time", "") if last_track else "",
        "current_location": last_track.get("location", "") if last_track else "",
        "latest_status": last_track.get("context", "") if last_track else "",
        "call_kuaidi100": True,
        "tracks": tracks,
        "track_count": len(tracks) if tracks else 0,
    }


@app.get("/api/stock", tags=["库存查询"])
def query_stock(product_id: str = Query(..., description="产品ID，如 x1_pro")):
    """库存查询接口 — Dify HTTP请求节点调用"""
    product = STOCKS.get(product_id)
    if not product:
        return {
            "found": False,
            "message": f"未找到产品 {product_id}，请确认产品名称",
        }
    return {
        "found": True,
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "variants": product["variants"],
    }


@app.get("/api/products", tags=["产品列表"])
def list_products():
    """列出所有产品"""
    return {"products": PRODUCTS}


@app.post("/api/reload", tags=["数据管理"])
def reload_data():
    """重新加载 JSON 配置文件（修改数据后无需重启服务）"""
    global ORDERS, STOCKS, PRODUCTS
    ORDERS = load_json("orders.json")
    STOCKS = load_json("stocks.json")
    PRODUCTS = load_json("products.json")
    return {
        "message": "数据已重新加载",
        "orders_count": len(ORDERS),
        "stocks_count": len(STOCKS),
        "products_count": len(PRODUCTS),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  NovaTech Customer Service API 启动中...")
    print("  版本：2.0.0（对接快递100真实API）")
    print()
    print("  接口地址：")
    print("    物流查询：http://localhost:3000/api/logistics?order_id=NV202609080001")
    print("    库存查询：http://localhost:3000/api/stock?product_id=x1_pro")
    print("    产品列表：http://localhost:3000/api/products")
    print("    重新加载：POST http://localhost:3000/api/reload")
    print()
    print("  快递100配置：")
    if KUAIDI100_CUSTOMER:
        print(f"    Customer: {KUAIDI100_CUSTOMER[:4]}***")
        print(f"    Key: {'已配置' if KUAIDI100_KEY else '未配置'}")
        print("    状态：✅ 已对接快递100真实API")
    else:
        print("    状态：⚠️  未配置，物流查询将回退到本地缓存")
        print("    配置方式：在 .env 文件中设置 KUAIDI100_CUSTOMER 和 KUAIDI100_KEY")
    print()
    print("  数据配置：修改 data/ 目录下的 JSON 文件")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=3000)
