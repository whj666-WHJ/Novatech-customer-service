"""
NovaTech Mock API 连通性测试脚本
运行：python scripts/test_api.py
"""

import json
import urllib.request
import sys

BASE_URL = "http://localhost:3000"


def request(path):
    """发送GET请求并返回JSON"""
    url = f"{BASE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def test_health():
    print("测试1：健康检查...")
    data = request("/")
    if data.get("status") == "ok":
        print("  ✅ API 正常运行")
        return True
    print(f"  ❌ 失败: {data}")
    return False


def test_logistics():
    print("测试2：物流查询接口...")
    data = request("/api/logistics?order_id=NV202609080001")
    if data.get("found") and data.get("status") == "运输中":
        print(f"  ✅ 物流查询正常 — {data['express']}，{data['status']}")
        return True
    print(f"  ❌ 失败: {data}")
    return False


def test_logistics_not_found():
    print("测试3：物流查询（不存在的订单）...")
    data = request("/api/logistics?order_id=INVALID")
    if not data.get("found"):
        print(f"  ✅ 正确返回未找到 — {data['message']}")
        return True
    print(f"  ❌ 失败: {data}")
    return False


def test_stock():
    print("测试4：库存查询接口...")
    data = request("/api/stock?product_id=x1_pro")
    if data.get("found") and "variants" in data:
        variants = data["variants"]
        in_stock = sum(1 for v in variants.values() if v["available"])
        print(f"  ✅ 库存查询正常 — {len(variants)}个版本，{in_stock}个有货")
        return True
    print(f"  ❌ 失败: {data}")
    return False


def test_products():
    print("测试5：产品列表接口...")
    data = request("/api/products")
    products = data.get("products", [])
    if len(products) > 0:
        print(f"  ✅ 产品列表正常 — 共{len(products)}款产品")
        return True
    print(f"  ❌ 失败: {data}")
    return False


def main():
    print("=" * 50)
    print("  NovaTech Mock API 连通性测试")
    print("=" * 50)
    print()

    tests = [
        test_health,
        test_logistics,
        test_logistics_not_found,
        test_stock,
        test_products,
    ]

    results = []
    for test in tests:
        results.append(test())
        print()

    passed = sum(results)
    total = len(results)
    print("=" * 50)
    print(f"  测试结果：{passed}/{total} 通过")
    print("=" * 50)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
