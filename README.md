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
├── requirements.txt             # Python依赖（根目录）
├── docker-compose.yml           # Mock API容器编排
├── .env.example                 # 环境变量模板
├── .gitignore
├── mock_api/                    # Mock API服务
│   ├── main.py                  # FastAPI入口
│   ├── data/                    # JSON配置文件（改数据不动代码）
│   │   ├── orders.json          # 订单物流数据
│   │   ├── stocks.json          # 库存数据
│   │   └── products.json        # 产品列表
│   ├── requirements.txt
│   └── Dockerfile
├── data/                        # 知识库数据
│   ├── NovaTech产品手册.pdf
│   └── 客服话术_QA.csv
├── dify/                        # Dify工作流DSL（导入即用）
│   └── chatflow_dsl.yaml
├── scripts/                     # 辅助脚本
│   ├── start.bat                # Windows一键启动
│   └── test_api.py              # API连通性测试（5个用例）
└── docs/                        # 项目文档
    ├── 01_搭建指南.md
    ├── 02_测试问题与解决办法.md
    └── 03_效果评估报告.md
```

## 快速开始

### 前置条件

| 软件 | 版本要求 | 下载地址 |
|---|---|---|
| Docker Desktop | 最新版 | https://www.docker.com/products/docker-desktop/ |
| Python | 3.10+ | https://www.python.org/downloads/ |
| Ollama | 最新版 | https://ollama.com/download |
| Git | 最新版 | https://git-scm.com/ |

### 步骤1：安装 Ollama 并拉取嵌入模型

```bash
# 安装后执行
ollama pull bge-m3
```

### 步骤2：启动 Mock API

```bash
# 方式一：Python直接运行（开发调试）
cd mock_api
pip install -r requirements.txt
python main.py

# 方式二：Docker运行（推荐，无需装Python）
cd ..
docker-compose up -d mock_api
```

验证：浏览器访问 `http://localhost:3000/api/logistics?order_id=NV202609080001`
能看到JSON返回就说明API正常。

**修改数据**：直接编辑 `mock_api/data/` 下的 JSON 文件，改完调用 `POST http://localhost:3000/api/reload` 热加载，无需重启服务。

### 步骤3：部署 Dify

```bash
# 克隆 Dify 官方仓库
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 复制环境变量模板
cp .env.example .env

# 启动 Dify
docker compose up -d
```

**重要**：修改 Dify 的 `.env` 文件，确保 SSRF 代理允许访问宿主机：

```env
# 不能填 true，必须填具体 CIDR 网段，否则 Squid 会崩溃
SSRF_PROXY_ALLOW_PRIVATE_IPS=172.28.0.0/16,127.0.0.1/32,192.168.0.0/16
```

修改后重建 ssrf_proxy 容器：

```bash
docker compose up -d ssrf_proxy
```

### 步骤4：配置 Dify

1. 浏览器访问 `http://localhost` → 注册/登录 Dify
2. **导入工作流**：工作室 → 创建应用 → 导入DSL → 选择 `dify/chatflow_dsl.yaml`
3. **配置模型供应商**（设置 → 模型供应商）：
   - 通义千问：填入 API Key（https://dashscope.console.aliyun.com/ 获取）
   - Ollama：地址填 `http://host.docker.internal:11434`
4. **上传知识库**（知识库 → 创建）：
   - 库1「产品参数」：上传 `data/NovaTech产品手册.pdf`，分段512，重叠64
   - 库2「客服话术」：上传 `data/客服话术_QA.csv`，分段256
   - 检索方式均选「混合检索」，score_threshold=0.5
5. 在工作流中绑定知识库到对应检索节点
6. 点击「发布」→ 获取访问链接

### 步骤5：验证测试

```bash
# 测试 Mock API 连通性
python scripts/test_api.py
```

5个用例全部通过即说明环境正常。

### 数据修改说明

| 要改什么 | 改哪个文件 | 怎么生效 |
|---|---|---|
| 订单物流数据 | `mock_api/data/orders.json` | 调用 `POST /api/reload` |
| 库存数据 | `mock_api/data/stocks.json` | 调用 `POST /api/reload` |
| 产品列表 | `mock_api/data/products.json` | 调用 `POST /api/reload` |
| 知识库内容 | 在Dify知识库页面上传新文件 | 自动生效 |

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
