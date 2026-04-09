# llm-ops

```
# api-doc
>https://ptrb24jefd.apifox.cn/

```

# env config
```
OPENAI_API_KEY=
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

FLASK_ENV=development
FLASK_DEBUG=1

# sql congig

SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/llmops?client_encoding=utf8
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_ECHO=True
WTF_CSRF_ENABLED=False




# LangSmith
# https://smith.langchain.com/

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=<your-api-key>
LANGSMITH_PROJECT="llmops" # project name


```






# run project
```bash
# dev
 uv run python app\http\app.py
```

## docker postgres 

> docker run  --name postgres-dev -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -d postgres


# 初始化生成迁移脚本
```bash
flask --app app.http.app db init 
flask --app app.http.app db migrate 
# -m "msg"

# 升级
flask --app app.http.app db upgrade

#回退
flask --app app.http.app db downgrade

```


### Agent 概念和运行流程
```
在 LLM 应用中，如果我们知道用户输入所需的工具使用特定顺序时，使用 LCEL 表达式构建链应用非常有用，但是对于某一些特例，我们使用工具的次数与顺序取决于输入，在这种情况下，我们希望让 LLM 本身决定使用工具的次数和顺序，而 Agent 智能体 能做到这一点。
在 LangChain 中，Agent 是一个核心概念，它代表了一种能够利用语言模型（LLM）和其他工具来执行复杂任务的系统，Agent 设计的目的是为了处理那些语言模型可能无法直接解决的问题，尤其是当这些任务涉及到多个步骤或者需要外部数据源的情况。
无论一个 Agent 设计得多么复杂，使用什么架构，最基础的工作流程其实都非常简单，只有 5 个步骤：
输入理解：Agent 首先解析用户输入，理解其意图和需求。
计划定制：基于对输入的理解，Agent 会制定一个执行计划，决定使用哪些工具和执行的顺序。
工具调用：Agent 按照计划调用相应的工具，执行必要的操作。
结果整合：收集所有工具返回的结果，进行整合和解析，形成最终的输出。
反馈循环：如果任务没有完成或者需要进一步的消息，Agent 可以迭代上述过程直到满足条件为止。
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
                                                      └──────────────┘```