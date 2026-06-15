# LLMOps - Agent Guide

## Monorepo Structure

- `llmops-api/` — Flask backend (Python 3.13+, uv)
- `llmops-ui/` — Vue 3 frontend (Vite + TypeScript + Tailwind + Arco Design)
- `docker-compose.yml` — PostgreSQL, Redis, Weaviate
- `docs/`, `storage/` — Documentation, logs

## Prerequisites

```bash
docker compose up -d          # PostgreSQL + Redis + Weaviate
# Ollama must be running locally for embeddings (default: http://127.0.0.1:11434)
```

## llmops-api

```bash
cd llmops-api
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
flask --app app.http.app db downgrade
```

Migrations directory: `internal/migration/`

### Testing

```bash
cd llmops-api
pytest                        # Uses pytest.ini: -v -s, cache in tmp/
```

### Architecture

- Entry: `app/http/app.py` → creates `Http` (Flask subclass), gets `celery` from extensions
- DI: Uses `injector` library; bindings in `internal/model/module.py`
- Routes: `internal/router/router.py` — all URL rules registered manually via `add_url_rule`
- Extensions: `internal/extension/` — DB, Redis, Celery, Migrate, Login, Logging
- Config: `config/config.py` reads from env vars via `os.getenv`

### Key Directory Layout (internal/)

```
core/         — Agent, tools, workflow engine (LangGraph), memory, retrievers
entity/       — Enums, defaults, constants
model/        — SQLAlchemy ORM models
service/      — Business logic
handler/      — HTTP request handlers (thin layer over services)
schema/       — Request/response validation (WTForms)
router/       — Flask route registration
extension/    — Flask extensions (DB, Redis, Celery)
task/         — Celery async tasks
middleware/   — Auth/request loading
migration/    — Alembic migrations
```

### Gotchas

- **DetachedInstanceError**: In generators/SSE streams, extract ORM IDs *before* yielding (session closes mid-stream)
- **Workflow validation**: Empty workflows auto-create START→END nodes; `workflow_entity.py` validator allows empty nodes/edges
- **Celery eventlet**: Must use `--pool eventlet`; default prefork breaks
- **Windows**: `start_celery.ps1` sets `PYTHONPATH` and cleans `.pyc` before start

## llmops-ui

```bash
cd llmops-ui
npm install
npm run dev                   # Vite dev server, proxies /api → localhost:5000
npm run build                 # type-check + vite build
npm run lint                  # ESLint with auto-fix
npm run format                # Prettier
npm run test:unit             # Vitest
```

### Frontend Stack

- Vue 3 + Vue Router + Pinia
- Arco Design (`@arco-design/web-vue`) as UI component library
- Tailwind CSS + PostCSS
- TypeScript strict mode
- `@` alias → `./src`

### Proxy Config

`/api` requests are proxied to `http://localhost:5000` (Flask backend). Path prefix `/api` is stripped.

## Environment Variables

Create `llmops-api/.env`. Key vars:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY`, `OPENAI_API_BASE_URL` | LLM provider (DashScope compatible) |
| `SQLALCHEMY_DATABASE_URI` | PostgreSQL connection |
| `REDIS_HOST`, `REDIS_PORT` | Redis for Celery + cache |
| `WEAVIATE_HOST`, `WEAVIATE_PORT` | Vector DB |
| `OLLAMA_BASE_URL` | Local embedding model |
| `FLASK_ENV`, `FLASK_DEBUG` | Flask dev mode |

## Code Conventions

- Python 3.13+, type hints required, Pydantic V2
- Flask-WTF for request validation
- `flask --app app.http.app` is the app entry for CLI commands
- Frontend: ESLint + Prettier; run `npm run lint` before committing

---

## llmops-ui 迁移计划：Arco Design → Quasar

> 状态：待执行 | 记录时间：2026-06-13

### 项目现状

- **58 个 Vue 文件**，分布在 views/components/layouts
- **Arco Design 组件**广泛使用：布局、表单、数据展示、反馈、导航、图标
- **Tailwind CSS** 用于原子化样式
- **Pinia** 状态管理，**Vue Router** 路由

### 迁移步骤

#### 1. 环境准备

```bash
# 安装 Quasar
npm install quasar @quasar/extras
npm install -D @quasar/vite-plugin

# 移除 Arco Design
npm uninstall @arco-design/web-vue
```

- 更新 `vite.config.ts` 添加 Quasar 插件
- 更新 `main.ts`：移除 Arco，添加 Quasar

#### 2. 组件映射

| Arco Design | Quasar | 说明 |
|-------------|--------|------|
| `a-layout` | `q-layout` | 布局容器 |
| `a-layout-sider` | `q-drawer` | 侧边栏 |
| `a-layout-content` | `q-page-container` | 内容区域 |
| `a-button` | `q-btn` | 按钮 |
| `a-input` | `q-input` | 输入框 |
| `a-textarea` | `q-input type="textarea"` | 文本域 |
| `a-form` | `q-form` | 表单 |
| `a-form-item` | `q-field` 或 `q-input` 的 `label` | 表单项 |
| `a-modal` | `q-dialog` | 模态框 |
| `a-drawer` | `q-drawer` | 抽屉 |
| `a-card` | `q-card` | 卡片 |
| `a-avatar` | `q-avatar` | 头像 |
| `a-table` | `q-table` | 表格 |
| `a-spin` | `q-spinner` | 加载中 |
| `a-empty` | 自定义 | 空状态 |
| `a-dropdown` | `q-btn-dropdown` / `q-menu` | 下拉菜单 |
| `a-row/a-col` | `div class="row"` / `div class="col"` | 栅格 |
| `a-space` | `q-gutter` | 间距 |
| `a-upload` | `q-file` / `q-uploader` | 文件上传 |
| `a-message` | `Notify.create()` | 消息提示 |

#### 3. 迁移顺序

1. **布局文件** (2个)：`DefaultLayout.vue`, `BlankLayout.vue`
2. **通用组件** (13个)：`CodeHighLight.vue`, `DotFlashing.vue`, `icons/*.vue`
3. **认证页面** (4个)：`LoginView.vue`, `AuthorizeView.vue`, `Banner.vue`, `LoginForm.vue`
4. **空间页面** (20+)：应用/数据集/工具/工作流管理
5. **开放 API 页面** (4个)：`IndexView.vue`, `ListView.vue`, 模态框
6. **商店页面** (2个)：应用/工具列表

#### 4. 注意事项

- **图标系统**：Arco 图标 → Quasar Material Icons 或自定义 SVG
- **表单验证**：Arco 验证语法与 Quasar 不同，需调整验证逻辑
- **模态框/抽屉**：`v-model:visible` → Quasar 的 `v-model` 或 `useDialog()`
- **栅格系统**：Arco 的 `span` 属性 → Quasar 的 `col-*` 类
- **TypeScript 类型**：更新组件类型定义
- **Tailwind CSS**：可与 Quasar 共存，无需移除

#### 5. 风险评估

- **中等风险**：组件 API 差异较大，需逐个调整
- **工作量**：约 58 个 Vue 文件，预计 2-3 天
- **建议**：渐进式迁移，先布局和通用组件，再业务页面
