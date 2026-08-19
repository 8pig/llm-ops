# TODO

## SSE event 字段输出枚举名问题（待修复）

### 问题

后端 SSE 输出 `yield f"event: {agent_thought.event}\n..."`，其中 `agent_thought.event` 是 `QueueEvent(str, Enum)` 枚举，f-string 输出的是枚举名 `QueueEvent.AGENT_MESSAGE`，而不是值 `agent_message`。而 `data` 里的 `event` 字段经 pydantic 序列化为值 `agent_message`，导致两层不一致：

- `event_response.event = 'QueueEvent.AGENT_MESSAGE'`
- `event_response.data.event = 'agent_message'`

### 修改点

后端 4 处统一改为 `.value`：

| 文件 | 行号 |
|---|---|
| `llmops-api/internal/service/web_app_service.py` | 191 |
| `llmops-api/internal/service/app_service.py` | 593 |
| `llmops-api/internal/service/assistant_agent_service.py` | 141 |
| `llmops-api/internal/service/openapi_service.py` | 194 |

```diff
- yield f"event: {agent_thought.event}\ndata:{json.dumps(data)}\n\n"
+ yield f"event: {agent_thought.event.value}\ndata:{json.dumps(data)}\n\n"
```

### 前端 ping 过滤 bug

`llmops-ui/src/views/space/apps/components/PreviewDebugChat.vue:124` 用外层 `event`（枚举名）判断 ping，导致 ping 事件无法被过滤：

```diff
- if (event !== QueueEvent.ping) {
+ if (event_name !== QueueEvent.ping) {
```

### 影响

- 业务功能零影响（前端判断都用 `data.event`）。
- 修复 ping 过滤 bug。
- 符合开放 API 文档规范（文档写的是 `event: agent_message`）。
