"""模拟数据 — 订单物流和产品库存"""

# ==================== 订单数据 ====================
ORDERS = {
    "NV202609080001": {
        "order_id": "NV202609080001",
        "product": "NovaTech X1 Pro",
        "storage": "12+512G",
        "express": "顺丰速运",
        "tracking_no": "SF1234567890",
        "status": "运输中",
        "current_location": "深圳转运中心",
        "estimated_arrival": "2026-09-10",
    },
    "NV202609080002": {
        "order_id": "NV202609080002",
        "product": "NovaTech X1",
        "storage": "8+256G",
        "express": "京东物流",
        "tracking_no": "JD0987654321",
        "status": "已发货",
        "current_location": "上海分拨中心",
        "estimated_arrival": "2026-09-09",
    },
    "NV202609080003": {
        "order_id": "NV202609080003",
        "product": "NovaTech Watch GT",
        "storage": "蓝牙版",
        "express": "中通快递",
        "tracking_no": "ZT5678901234",
        "status": "已签收",
        "current_location": "北京朝阳区",
        "estimated_arrival": "2026-09-07",
    },
    "NV202609080004": {
        "order_id": "NV202609080004",
        "product": "NovaTech Buds Pro",
        "storage": "标配",
        "express": "圆通速递",
        "tracking_no": "YT1357902468",
        "status": "运输中",
        "current_location": "杭州转运中心",
        "estimated_arrival": "2026-09-10",
    },
    "NV202609080005": {
        "order_id": "NV202609080005",
        "product": "NovaTech Z3",
        "storage": "6+128G",
        "express": "顺丰速运",
        "tracking_no": "SF2468013579",
        "status": "待发货",
        "current_location": "仓库准备中",
        "estimated_arrival": "2026-09-11",
    },
}


# ==================== 库存数据 ====================
STOCKS = {
    "x1_pro": {
        "product_id": "x1_pro",
        "product_name": "NovaTech X1 Pro",
        "variants": {
            "8+128G": {"stock": 0, "available": False},
            "8+256G": {"stock": 12, "available": True},
            "12+512G": {"stock": 5, "available": True},
        },
    },
    "x1": {
        "product_id": "x1",
        "product_name": "NovaTech X1",
        "variants": {
            "6+128G": {"stock": 23, "available": True},
            "8+256G": {"stock": 8, "available": True},
        },
    },
    "z3": {
        "product_id": "z3",
        "product_name": "NovaTech Z3",
        "variants": {
            "6+128G": {"stock": 0, "available": False},
            "8+256G": {"stock": 3, "available": True},
        },
    },
    "watch_gt": {
        "product_id": "watch_gt",
        "product_name": "NovaTech Watch GT",
        "variants": {
            "蓝牙版": {"stock": 45, "available": True},
            "LTE版": {"stock": 0, "available": False},
        },
    },
    "buds_pro": {
        "product_id": "buds_pro",
        "product_name": "NovaTech Buds Pro",
        "variants": {
            "标配": {"stock": 67, "available": True},
        },
    },
}


# ==================== 产品列表 ====================
PRODUCTS = [
    {"product_id": "x1_pro", "name": "NovaTech X1 Pro"},
    {"product_id": "x1", "name": "NovaTech X1"},
    {"product_id": "z3", "name": "NovaTech Z3"},
    {"product_id": "watch_gt", "name": "NovaTech Watch GT"},
    {"product_id": "buds_pro", "name": "NovaTech Buds Pro"},
]
