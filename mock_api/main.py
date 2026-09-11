"""
NovaTech 3C电商智能客服 — Mock API
提供物流查询和库存查询接口，供Dify HTTP请求节点调用

启动方式：
    pip install -r requirements.txt
    python main.py
    # 服务运行在 http://localhost:3000

数据配置：
    修改 data/ 目录下的 JSON 文件即可更新订单和库存数据，无需改代码
"""

import json
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# ==================== 数据加载 ====================
# 从 JSON 配置文件读取数据，改数据不需要动代码
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


# ==================== FastAPI 应用 ====================
app = FastAPI(title="NovaTech Mock API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["健康检查"])
def root():
    return {"status": "ok", "service": "NovaTech Mock API", "version": "1.0.0"}


@app.get("/api/logistics", tags=["物流查询"])
def query_logistics(order_id: str = Query(..., description="订单号，如 NV202609080001")):
    """物流查询接口 — Dify HTTP请求节点调用"""
    order = ORDERS.get(order_id)
    if not order:
        return {
            "found": False,
            "message": f"未找到订单号 {order_id}，请确认订单号是否正确",
        }
    return {
        "found": True,
        "order_id": order["order_id"],
        "product": order["product"],
        "storage": order["storage"],
        "express": order["express"],
        "tracking_no": order["tracking_no"],
        "status": order["status"],
        "current_location": order["current_location"],
        "estimated_arrival": order["estimated_arrival"],
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
    print("=" * 55)
    print("  NovaTech Mock API 启动中...")
    print("  接口地址：")
    print("    物流查询：http://localhost:3000/api/logistics?order_id=NV202609080001")
    print("    库存查询：http://localhost:3000/api/stock?product_id=x1_pro")
    print("    产品列表：http://localhost:3000/api/products")
    print("    重新加载：POST http://localhost:3000/api/reload")
    print("  数据配置：修改 data/ 目录下的 JSON 文件")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=3000)
