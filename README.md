# NovaTech 3C数码电商智能客服系统

基于 Dify + RAG + MCP工具调用 搭建的3C数码电商智能客服，支持产品参数咨询、售后政策解答、物流/支付查询、产品对比、实时库存查询、投诉转人工等场景。

## 系统架构

```
用户提问
    │
    ▼
┌─────────────────────────────────────────────┐
│  8类意图分类（通义千问 qwq-plus, temperature=0）│
└─────────────────────────────────────────────┘
    │
    ├─ product_query ──→ 知识库RAG（产品手册）──→ LLM生成
    ├─ after_sales ────→ 知识库RAG（客服话术）──→ LLM生成
    ├─ logistics ──────→ 知识库RAG（客服话术）──→ LLM生成
    ├─ payment ────────→ 知识库RAG（客服话术）──→ LLM生成
    ├─ complaint ──────→ 直接回复（转人工话术）
    ├─ order_query ────→ HTTP请求（物流API）────→ LLM组织回复
    ├─ stock_query ────→ HTTP请求（库存API）────→ LLM组织回复
    └─ unrelated ──────→ 直接回复（兜底话术）
```

**双通道设计**：
- **静态信息**（产品参数、售后政策）→ RAG知识库检索
- **动态信息**（实时物流、实时库存）→ MCP/HTTP工具调用

## 技术栈

| 组件 | 技术选型 | 说明 |
|---|---|---|
| 对话编排 | Dify Chatflow | 本地Docker部署 |
| 嵌入模型 | Ollama + bge-m3 | 中文语义嵌入 |
| 对话/分类模型 | 通义千问 qwq-plus | 在线API |
| 向量库 | Weaviate | Dify内置 |
| Mock API | FastAPI + Python | 模拟物流/库存接口 |
| 部署 | Docker + Docker Compose | 一键启动 |

## 目录结构

```
novatech-customer-service/
├── README.md                    # 本文件
├── docker-compose.yml           # 整合Dify + Mock API
├── .env.example                 # 环境变量模板
├── mock_api/                    # Mock API服务
│   ├── main.py                  # FastAPI入口
│   ├── data/mock_data.py        # 模拟数据（订单、库存）
│   ├── requirements.txt
│   └── Dockerfile
├── data/                        # 知识库数据
│   ├── NovaTech产品手册.pdf
│   └── 客服话术_QA.csv
├── dify/                        # Dify工作流DSL（导出后放入）
├── scripts/                     # 辅助脚本
│   ├── start.bat                # Windows一键启动
│   └── test_api.py              # API连通性测试
└── docs/                        # 项目文档
    ├── 01_搭建指南.md
    ├── 02_测试问题与解决办法.md
    └── 03_效果评估报告.md
```

## 快速开始

### 前置条件

- Docker Desktop（已开启WSL2）
- Python 3.10+（仅运行Mock API时需要）
- Ollama（本地嵌入模型）

### 步骤1：启动 Ollama 并拉取嵌入模型

```bash
ollama pull bge-m3
```

### 步骤2：启动 Mock API

```bash
# 方式一：Python直接运行
cd mock_api
pip install -r requirements.txt
python main.py

# 方式二：Docker运行（推荐）
docker-compose up -d mock_api
```

验证：浏览器访问 `http://localhost:3000/api/logistics?order_id=NV202609080001`

### 步骤3：部署 Dify

```bash
cd /path/to/dify/docker
docker compose up -d
```

**重要**：修改 Dify 的 `.env` 文件，确保 SSRF 代理允许访问宿主机：

```env
SSRF_PROXY_ALLOW_PRIVATE_IPS=172.28.0.0/16,127.0.0.1/32,192.168.0.0/16
```

修改后重建 ssrf_proxy 容器：

```bash
docker compose up -d ssrf_proxy
```

### 步骤4：配置 Dify

1. 访问 `http://localhost` 登录 Dify
2. 导入 `dify/` 目录下的工作流 DSL（或手动按 `docs/01_搭建指南.md` 编排）
3. 配置模型供应商：通义千问（对话+分类）、Ollama（嵌入）
4. 上传 `data/` 目录下的知识库文件

### 步骤5：测试

```bash
python scripts/test_api.py
```

## 关键指标

| 指标 | 数值 |
|---|---|
| 知识库召回率 | 87% |
| 答案准确率 | 85% |
| 意图识别准确率 | 92.5% |
| MCP工具调用成功率 | 100% |
| 客户满意度 | 4.3/5.0 |
| 平均响应时间 | 2.3s |

## Mock API 接口

| 接口 | 方法 | 参数 | 说明 |
|---|---|---|---|
| `/api/logistics` | GET | `order_id` | 查询订单物流 |
| `/api/stock` | GET | `product_id` | 查询产品库存 |
| `/api/products` | GET | 无 | 产品列表 |

## 文档

- [搭建指南](docs/01_搭建指南.md)
- [测试问题与解决办法](docs/02_测试问题与解决办法.md)
- [效果评估报告](docs/03_效果评估报告.md)
