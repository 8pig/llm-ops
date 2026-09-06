# 开发笔记（DEVELOPMENT）

> 从原首页 README 迁移的开发向内容：环境变量清单、数据库迁移、ER 图、Agent 概念与流程、常用命令、参考链接。

---

## 一、完整环境变量清单

### LLM / LangSmith

```
# LLM 主模型（DashScope 兼容模式示例）
OPENAI_API_KEY=<your-api-key>
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# LangSmith（可选；注意存在泄露风险，本地部署建议用 langfuse 等替代）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=<your-api-key>
LANGCHAIN_PROJECT="llmops"
```

### Flask

```
FLASK_ENV=development
FLASK_DEBUG=1
JWT_SECRET_KEY=<random-secret>
WTF_CSRF_ENABLED=False
```

### PostgreSQL

```
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/llmops?client_encoding=utf8
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_ECHO=True
```

### Redis / Celery

```
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_USERNAME=
REDIS_USE_SSL=False

CELERY_BROKER_DB=1
CELERY_RESULT_BACKEND_DB=1
CELERY_TASK_IGNORE_RESULT=False
CELERY_RESULT_EXPIRES=3600
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
```

### 第三方工具与存储

```
# 高德地图工具
GAODE_API_KEY=
# 谷歌 Serper 搜索  https://serper.dev/api-keys
SERPER_API_KEY=
# 腾讯云 COS 对象存储
COS_SECRET_ID=
COS_SECRET_KEY=
COS_BUCKET=
COS_REGION=
COS_SCHEME=https
COS_DOMAIN=
```

### 向量化（embedding）

```
EMBEDDING_MODEL=qwen3-embedding:0.6b    # 或 4b / 8b
OLLAMA_BASE_URL=http://127.0.0.1:11434
TIKTOKEN_CACHE_DIR=<tiktoken缓存目录>    # Docker 内为 /app/api/tiktoken_cache
```

> 代码入口 `internal/service/embeddings_service.py`：默认走 `OllamaEmbeddings`，模型名取 `EMBEDDING_MODEL`，地址取 `OLLAMA_BASE_URL`，向量在 Redis 中以 `embeddings` 命名空间做缓存。
>
> **切换 embedding 模型注意**：Weaviate `Dataset` 集合的向量维度在首次创建时定死且不可改；若从 0.6b(1024 维) 换到 4b(2560 维) / 8b(4096 维)，需删除旧集合并清空 Redis `embeddings:*` 缓存，再让其自动按新维度重建。

---

## 二、本地依赖服务（Docker run）

```bash
# PostgreSQL
docker run --name postgres-dev -p 5432:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -d postgres

# Weaviate
docker run -d --name weaviate-dev -p 8080:8080 -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:1.35.3

# Redis
docker run --name redis-dev -d -p 6379:6379 redis
```

---

## 三、运行项目

```bash
# 异步任务（Windows 用仓库内 start_celery.ps1；必须 --pool eventlet）
celery -A app.http.app.celery worker -l info --pool eventlet --logfile storage/log/celery.log

# 开发服务
uv run python app/http/app.py
```

### 数据库迁移

```bash
flask --app app.http.app db init
flask --app app.http.app db migrate -m "msg"
flask --app app.http.app db upgrade
flask --app app.http.app db downgrade
```

---

## 四、数据库关系图（ER）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   UploadFile    │◄────│    Document     │◄────│     Segment     │
│  (上传文件)      │ 1:1 │  (文档)         │ 1:N │   (片段)         │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 │                       │
                    ┌────────────┘                       │
                    │                                    │
                    ▼                                    ▼
           ┌─────────────────┐                 ┌─────────────────┐
           │     Dataset     │◄────────────────│  KeywordTable   │
           │   (知识库)       │ 1:1             │  (关键词表)       │
           └────────┬────────┘                 └─────────────────┘
                    │
                    │ N:M
                    ▼
           ┌─────────────────┐
           │ AppDatasetJoin  │
           │(应用-知识库关联)  │
           └─────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │       App       │
           │    (AI应用)      │
           └─────────────────┘
```

---

## 五、Agent 概念与运行流程

在 LLM 应用中，若工具使用顺序已知，用 LCEL 构建链式应用非常有效；但当工具使用次数与顺序取决于用户输入时，更适合让 LLM 自行决策 —— 这正是 **Agent 智能体**：利用语言模型 + 工具执行复杂任务，处理多步骤或依赖外部数据源的问题。

任何 Agent 的基础流程只有 5 步：

1. **输入理解**：解析用户输入，理解意图与需求
2. **计划定制**：制定执行计划，决定工具与顺序
3. **工具调用**：按计划调用工具
4. **结果整合**：收集并整合工具返回结果，形成输出
5. **反馈循环**：未完成则迭代，直到满足条件

```
┌─────────────┐     ┌─────┐     ┌─────────────┐     ┌─────────┐
│   初始问题   │────▶│ LLM │────▶│ 格式化输出   │────▶│选择工具 │
└─────────────┘     └──┬──┘     └─────────────┘     └────┬────┘
                       │                                    │
                      函数调用                            工具列表
                                                              │
                         ←───────────────────────────────────┘
                         │        观察/循环执行              │
                         │   (直到最终完成条件满足)          ↓
                         ▼                              ┌──────────────┐
                     ┌──────────┐                       │ 工具执行结果  │
                     │   LLM    │ ◀────────────────────┤              │
                     │(再次调用) │                       └──────────────┘
                     └──────────┘                          │
                             │                           │ 最终调用
                             │                           ↓
                             └────────────────────────►┌──────────────┐
                                                       │  最终答案      │
                                                       └──────────────┘
```

---

## 六、常见问题

- **psycopg2 在 Linux/Docker 编译失败**：不要直接依赖 `psycopg2`（Linux 无 wheel，需 pg_config）。使用 `psycopg2-binary`。
- **DetachedInstanceError（SQLAlchemy）**：在生成器/SSE 流中，`yield` 前先取出 ORM 字段（会话可能在流中途关闭）。
- **Celery 崩溃**：必须使用 eventlet pool（`--pool eventlet`），默认 prefork 会挂。
- **Docker 构建上下文过大**：确保 `api/.dockerignore` 已排除 `.venv`（可达 1.9GB+）、`__pycache__`、`.env` 等。

---

## 七、参考链接

- [Hello-Agents](https://datawhalechina.github.io/hello-agents/#/)
- [LangChain Docs (Python)](https://docs.langchain.com/oss/python/langchain/quickstart) · [中文文档](https://langchain-doc.cn/)
- [uv 文档 / 国内镜像加速](https://uv.oaix.tech/blog/2025/06/17/quickly-set-uv-package-index-is-china-mirror/#__tabbed_1_3)
- [Weaviate 部署文档](https://docs.weaviate.org.cn/deploy)
- [Flask 中文文档](https://flask.org.cn/en/stable/)
- [llm-action](https://github.com/liguodongiot/llm-action)
- [LangGraph 工作流实践](./langgraph-workflow.md)
