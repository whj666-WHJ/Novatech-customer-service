# NovaTech 3C数码电商智能客服系统

基于 Dify + RAG + HTTP API工具调用 搭建的3C数码电商智能客服，支持产品参数咨询、售后政策解答、物流/支付查询、产品对比、实时库存查询、投诉转人工等场景。

## 系统架构

```
用户提问
    │
    ▼
┌─────────────────────────────────────────────┐
│  8类意图分类（通义千问 qwen-plus, temperature=0）│
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
- **动态信息**（实时物流、实时库存）→ HTTP API工具调用

## 技术栈

| 组件 | 技术选型 | 说明 |
|---|---|---|
| 对话编排 | Dify Chatflow | 本地Docker部署 |
| 嵌入模型 | 通义千问 text-embedding-v4 | 在线API，中文语义嵌入 |
| 对话/分类模型 | 通义千问 qwen-plus | 在线API，意图分类+答案生成 |
| 向量库 | Weaviate | Dify内置 |
| 物流API | 快递100真实API | 实时物流轨迹查询，订单存在性前置校验 |
| 库存API | FastAPI + Python | 模拟ERP库存系统 |
| 部署 | Docker + Docker Compose | 一键启动 |

## 目录结构

```
novatech-customer-service/
├── README.md                    # 本文件
├── requirements.txt             # Python依赖（根目录）
├── docker-compose.yml           # Mock API容器编排
├── .env.example                 # 环境变量模板
├── .gitignore
├── mock_api/                    # API服务（物流对接快递100 + 本地库存）
│   ├── main.py                  # FastAPI入口（快递100签名+订单校验）
│   ├── data/                    # JSON配置文件（改数据不动代码）
│   │   ├── orders.json          # 订单数据（含快递单号）
│   │   ├── stocks.json          # 库存数据
│   │   └── products.json        # 产品列表
│   ├── requirements.txt
│   └── Dockerfile
├── data/                        # 知识库数据
│   ├── 产品手册_分册1_手机平板音频.md（16 款）
│   ├── 产品手册_分册2_穿戴充电外设.md（16 款）
│   ├── 产品手册_分册3_智能家居桌面配件.md（8 款）
│   └── 客服话术_QA.csv（55 条）
├── dify/                        # Dify工作流DSL（导入即用）
│   └── chatflow_dsl.yml
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
| Git | 最新版 | https://git-scm.com/ |

> 不需要安装 Ollama，嵌入模型和对话模型均使用通义千问在线API。

### 步骤1：启动 API 服务

**配置快递100 API Key**（可选，不配置则物流查询回退到本地缓存）：

1. 注册 [快递100](https://www.kuaidi100.com) 账号 → 开放平台获取 `customer` 和 `key`
2. 在项目根目录创建 `.env` 文件：
   ```env
   KUAIDI100_CUSTOMER=你的customer
   KUAIDI100_KEY=你的key
   ```

**启动服务**：

```bash
# 方式一：Python直接运行（开发调试）
cd mock_api
pip install -r requirements.txt
python main.py
# 服务运行在 http://localhost:3000

# 方式二：Docker运行（推荐，无需装Python）
docker-compose up -d mock_api
```

验证：浏览器访问 `http://localhost:3000/api/logistics?order_id=NV202609080001`
能看到JSON返回就说明API正常。

**订单存在性前置校验**：物流查询接口会先校验订单号是否存在于本地系统，不存在则直接返回，不调用快递100 API（降低调用成本 + 防止恶意请求）。

**修改数据**：直接编辑 `mock_api/data/` 下的 JSON 文件，改完调用 `POST http://localhost:3000/api/reload` 热加载，无需重启服务。

### 步骤2：部署 Dify

```bash
# 克隆 Dify 官方仓库
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 复制环境变量模板
cp .env.example .env

# 启动 Dify
docker compose up -d
```

**重要**：修改 Dify 的 `.env` 文件，确保 SSRF 代理允许访问宿主机（根据实际网络环境调整 CIDR 网段）：

```env
# 不能填 true，必须填具体 CIDR 网段，否则 Squid 会崩溃
# 以下为常见配置，根据你的 Docker 网络实际调整
SSRF_PROXY_ALLOW_PRIVATE_IPS=172.28.0.0/16,127.0.0.1/32,192.168.0.0/16
```

修改后重建 ssrf_proxy 容器：

```bash
docker compose up -d ssrf_proxy
```

### 步骤3：配置 Dify

1. 浏览器访问 `http://localhost` → 注册/登录 Dify
2. **配置模型供应商**（设置 → 模型供应商）：
   - 通义千问：填入 API Key（https://dashscope.console.aliyun.com/ 获取）
   - 嵌入模型选 `text-embedding-v4`
   - 对话/分类模型选 `qwen-plus`
3. **导入工作流**：工作室 → 创建应用 → 导入DSL → 选择 `dify/chatflow_dsl.yml`
4. **上传知识库**（知识库 → 创建）：
   - 库1「产品参数」：上传 `data/` 下3个产品手册Markdown文件，分段512，重叠64
   - 库2「客服话术」：上传 `data/客服话术_QA.csv`，分段256
   - 检索方式均选「混合检索」，score_threshold=0.5
5. 在工作流中绑定知识库到对应检索节点
6. 点击「发布」→ 获取访问链接

### 步骤4：验证测试

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

> 以下数据基于40条测试用例的人工评估，非自动化基准测试，仅供参考。

| 指标 | 数值 | 测试方法 |
|---|---|---|
| 知识库召回率 |95% | 40条产品/售后问题，人工判断是否召回正确片段 |
| 答案准确率 | 97.5% | 40条问题，人工判断回答是否正确且无幻觉 |
| 意图识别准确率 | 92% | 40条问题，对比分类器输出与人工标注 |
| HTTP API调用成功率 | 100% | 10条订单/库存查询，验证返回数据正确 |
| 客户满意度 | 4.3/5.0 | 模拟用户主观评分（5分制） |
| 平均响应时间 | 2.3s | Web前端实测，含网络传输 |

## API 接口

| 接口 | 方法 | 参数 | 说明 |
|---|---|---|---|
| `/api/logistics` | GET | `order_id` | 物流查询：先校验订单存在性，再调用快递100真实API获取实时轨迹 |
| `/api/stock` | GET | `product_id` | 库存查询：本地模拟ERP库存数据 |
| `/api/products` | GET | 无 | 产品列表 |
| `/api/reload` | POST | 无 | 热加载JSON数据，改数据不重启 |

## 文档

- [搭建指南](docs/01_搭建指南.md)
- [测试问题与解决办法](docs/02_测试问题与解决办法.md)
- [效果评估报告](docs/03_效果评估报告.md)
