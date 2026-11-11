# LLMOps - Agent Guide

## Monorepo Structure

- `api/` — Flask backend (Python 3.13+, uv)
- `ui/` — Vue 3 frontend (Vite + TypeScript + Tailwind + Arco Design)
- `docker-compose.yml` — 本地开发依赖：PostgreSQL, Redis, Weaviate
- `docker/` — 生产编排 `docker/docker-compose.yaml`（ui/api/celery/redis/db/weaviate/nginx）+ `.env.example` + `postgres/init.sql`
- `docs/`, `storage/` — Documentation, runtime artifacts

`llmops-api/` / `llmops-ui/` 是历史目录名，现已改为 `api/` / `ui/`；Docker 服务名仍叫 `llmops-api`、`llmops-ui`，两者不要混淆。

## Prerequisites

```bash
docker compose up -d          # PostgreSQL + Redis + Weaviate (root compose file)
# Ollama must be running locally for embeddings (default: http://127.0.0.1:11434)
```

## api/

```bash
cd api
uv sync                       # Install dependencies
uv run python app/http/app.py # Dev server on :5000
```

### Celery Worker

Use the PowerShell script (cleans .pyc, sets PYTHONPATH, runs with eventlet):

```bash
.\start_celery.ps1
```

Or manually:

```bash
celery -A app.http.app.celery worker -l info --pool eventlet
```

### Database Migrations

```bash
flask --app app.http.app db migrate -m "msg"
flask --app app.http.app db upgrade
```

Migrations config: `internal/migration/`（`alembic.ini` + `env.py`）。

注意：`internal/migration/versions/` 未纳入版本库，仓库里也没有 `db.create_all()` 兜底，`docker/postgres/init.sql` 只安装 `uuid-ossp` 扩展。新环境需要自己生成初始迁移，或从已有数据库导入 schema。

### Testing

```bash
cd api
pytest                        # pytest.ini: -v -s, cache in tmp/
```

测试覆盖极少，目前只有 `test/internal/handler/test_app_handler.py`（+ `test/conftest.py`）。

### Architecture

- Entry: `app/http/app.py` → creates `Http` (Flask subclass, `internal/server/http.py`), wires db / weaviate / migrate / celery extensions
- DI: `injector` library; bindings in `internal/model/module.py`
- Routes: `internal/router/router.py` — 全部手工 `add_url_rule`，两个 Blueprint：控制台 `llmops` 与对外开放 `openapi`
- Extensions: `internal/extension/` — DB, Redis, Celery, Migrate, Login, Logging, Weaviate
- Config: `config/config.py`（仅 52 行）直接 `os.getenv` 读取，不继承任何 base class
- Shared infra: `pkg/` — db, oauth, paginator, password, response

### Key Directory Layout (internal/)

```
core/         — agent, workflow, tools, memory, retrievers, language_model,
                  vector_store, file_extractor, unstructured, builtin_apps
entity/       — Enums, defaults, constants（按域拆分：app/dataset/conversation/workflow…）
model/        — SQLAlchemy ORM models（app/dataset/conversation 是主体）
service/      — Business logic（34 个，handler 之下的真正实现层）
handler/      — HTTP request handlers (thin layer over services)
schema/       — Request/response validation (WTForms)
router/       — Flask route registration
extension/    — Flask extensions
task/         — Celery async tasks
middleware/   — Auth/request loading
lib/          — helper, llm_error
exception/    — 自定义异常
server/       — Http (Flask subclass)
migration/    — Alembic config (versions/ 未提交)
schedule/     — 预留，目前为空
```

### AI Core 速查

- **Agent**：`core/agent/agents/` — `BaseAgent(Runnable)` 在子线程执行编译好的 LangGraph，主线程从队列消费 `AgentThought`。`FunctionCallAgent` 图结构为 敏感词审核 → 长期记忆召回 → llm ⇄ tools；模型不支持 tool_call 时走 `ReACTAgent` 的 prompt JSON 解析。SSE 事件由 `AgentQueueManager` 按 task_id 隔离（10s PING / 600s TIMEOUT），中止标志写在 Redis key `generate_task_stopped:*`。
- **Workflow**：`core/workflow/` — LangGraph `StateGraph`，节点类型只有 start / llm / tool / code / dataset_retrieval / http_request / template_transform / end 共 8 种，**没有条件分支节点**。配置校验（连通性、Kahn 判环、变量引用）在 `entity/workflow_entity.py`。工作流本身作为 `BaseTool` 注册给 Agent。
- **RAG**：`service/indexing_service.py` 串联 解析(FileExtractor/Unstructured，PDF 用 PyMuPDF) → 切片(默认 chunk_size=500 / overlap=50) → jieba 关键词表 → 批量写 Weaviate（集合名 `Dataset`，HNSW + cosine）。Embedding 为 Ollama `qwen3-embedding:0.6b`，经 `CacheBackedEmbeddings` 做 Redis 缓存。检索是 `EnsembleRetriever` 语义 0.5 + 全文 0.5 混合。
- **Model providers**：`core/language_model/providers/` — yaml 驱动（openai / tongyi / ollama / xiaomi / deepseek / moonshot），每个 provider 一个 `providers.yaml` + 逐模型 yaml；`LanguageModelManager` 单例加载。
- **Memory**：短期 `TokenBufferMemory`（tiktoken 本地计数，2000 token + 10 条消息双上限）；长期为会话摘要，后台线程生成后注入系统提示词。
- **Celery tasks**：`document_task`（索引构建 / enabled 同步 / 删除）、`dataset_task.delete_dataset`、`app_task.auto_create_app`、`demo_task`。

### Gotchas

- **DetachedInstanceError**: In generators/SSE streams, extract ORM IDs *before* yielding (session closes mid-stream)
- **SSE event 字段**: 必须用 `agent_thought.event.value`，直接 f-string 枚举会输出 `QueueEvent.AGENT_MESSAGE` 而不是 `agent_message`
- **Workflow validation**: Empty workflows auto-create START→END nodes; `workflow_entity.py` validator allows empty nodes/edges
- **Celery eventlet**: Must use `--pool eventlet`; default prefork breaks
- **Windows**: `start_celery.ps1` sets `PYTHONPATH` and cleans `.pyc` before start
- **跨进程文件写入**: API 与 Celery 会同时写同一文件，文件 handler 使用跨进程安全实现
- **Embedding 变量名**: 代码读 `EMBEDDING_MODEL`，`api/.env` 里若写成 `EMBEDDING_MODEL_NAME` 会静默回落到默认值

## ui/

```bash
cd ui
npm install
npm run dev                   # Vite dev server on :5173, proxies /api → localhost:5000
npm run build                 # vite build（不含类型检查，需要时用 build1）
npm run type-check            # vue-tsc --build --force
npm run lint                  # ESLint with auto-fix
npm run format                # Prettier
npm run test:unit             # Vitest
```

### Frontend Stack

- Vue 3 + Vue Router + Pinia（store 只有 account / credential / counter）
- Arco Design (`@arco-design/web-vue`) as UI component library — 未迁移到 Quasar
- `@vue-flow/*` + dagre：工作流画布（自动布局、节点面板在 `views/space/workflows/components/{nodes,infos}/`）
- echarts / vue-echarts（应用分析页）、markdown-it、highlight.js、js-audio-recorder（语音）
- Tailwind CSS + PostCSS、TypeScript、`@` alias → `./src`
- `services/*.ts` 与 `models/*.ts` 按后端 handler 一一对应

### Proxy Config

`/api` requests are proxied to `http://localhost:5000` (Flask backend). Path prefix `/api` is stripped.

## Environment Variables

Create `api/.env`. Key vars:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `LLM_MODEL` | 全局模型凭证（各 provider 未单独配置时的兜底） |
| `DASHSCOPE_API_KEY/BASE_URL`、`DEEPSEEK_API_KEY/BASE_URL`、`XIAOMI_API_KEY/BASE_URL`、`MOONSHOT_API_KEY/BASE_URL`、`OLLAMA_BASE_URL` | 按 provider 的独立凭证，优先级高于全局（映射见 `language_model_service.PROVIDER_ENV_PREFIX_MAP`） |
| `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_POOL_SIZE`, `SQLALCHEMY_POOL_RECYCLE` | PostgreSQL |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_USERNAME`, `REDIS_PASSWORD` | Redis（Celery + 缓存）|
| `CELERY_BROKER_DB`, `CELERY_RESULT_BACKEND_DB`, … | Celery（broker/backend 复用 Redis）|
| `WEAVIATE_HOST`, `WEAVIATE_PORT`, `WEAVIATE_GRPC_HOST`, `WEAVIATE_API_KEY` | Vector DB |
| `EMBEDDING_MODEL`, `OLLAMA_BASE_URL` | 本地向量模型 |
| `JWT_SECRET_KEY`, `GITHUB_CLIENT_ID/SECRET`, `ASSISTANT_AGENT_ID` | 鉴权与辅助会话 Agent |
| `COS_SECRET_ID/KEY`, `COS_BUCKET`, `COS_REGION` | 腾讯云对象存储 |
| `GAODE_API_KEY`, `SERPER_API_KEY`, `TAVILY_API_KEY` | 内置工具 |
| `AUDIO_API_BASE_URL`, `AUDIO_API_KEY`, `WHISPER_MODEL` | 语音（ASR/TTS）|
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY` | LangSmith 追踪 |
| `FLASK_ENV`, `FLASK_DEBUG`, `WTF_CSRF_ENABLED` | Flask dev mode |

## Code Conventions

- Python 3.13+, type hints required, Pydantic V2
- Flask-WTF for request validation
- `flask --app app.http.app` is the app entry for CLI commands
- Frontend: ESLint + Prettier; run `npm run lint` before committing
