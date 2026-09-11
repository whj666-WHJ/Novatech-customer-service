"""
NovaTech 3C电商智能客服 — Mock API
提供物流查询和库存查询接口，供Dify HTTP请求节点调用

启动方式：
    pip install -r requirements.txt
    python main.py
    # 服务运行在 http://localhost:3000
"""

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from data.mock_data import ORDERS, STOCKS, PRODUCTS

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


if __name__ == "__main__":
    print("=" * 55)
    print("  NovaTech Mock API 启动中...")
    print("  接口地址：")
    print("    物流查询：http://localhost:3000/api/logistics?order_id=NV202609080001")
    print("    库存查询：http://localhost:3000/api/stock?product_id=x1_pro")
    print("    产品列表：http://localhost:3000/api/products")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=3000)
