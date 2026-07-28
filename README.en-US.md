# AI Agent Development Platform

#### API Overview

*https://ptrb24jefd.apifox.cn/*

> "LLMOps Platform: AI App Builder" is a next-generation AI-native application development service platform. It allows users to build various Q&A and workflow applications based on AI models, ranging from simple question-answering to handling complex logical tasks. AI applications can be deployed with one click to corresponding social platforms, Web pages, MCP services for third-party calls, or even developed further using the platform's open APIs.

---

## 🛠️ Core Tech Stack

### 1. AI & Fundamentals

- **Prompt Engineering**: Prompt design and optimization.
- **LangChain / LangGraph**: LLM application development frameworks.
- **RAG Knowledge Base & Optimization**: Retrieval-Augmented Generation techniques.
- **Vector Database**: Embeddings storage and retrieval.
- **LLM Providers**: Integration with major model interfaces.
- **Fine-tuning Basics**: Model fine-tuning.

### 2. Agents & Protocols

- **Single/Multi-Agent**: Agent architecture design.
- **Workflow**: Business process orchestration.
- **MCP Protocol**: Model Context Protocol standard.
- **Celery Message Queue**: Asynchronous task processing.

### 3. Full-Stack Development

- **Frontend**: VUE / TypeScript / acro.
- **Backend**: Flask (Python).
- **Deployment**: Local/Cloud service deployment.
- **Database**: postgres / Weaviate.

---

## ️ LLMOps Platform Capabilities

### Core Platform Features

- **Visual Orchestration + Intelligent Customization**: Drag-and-drop development interface.
- **Workflow Orchestration**: Graphical construction of complex logic.
- **Custom Plugins**: Extend system functionality.
- **Knowledge Base Integration**: Rapid access to RAG capabilities.
- **One-Click Multi-Platform Publishing**: Multi-channel deployment.
- **Rapid Multi-LLM Access**: Support for easy model switching.
- **Single/Multi-Agent Custom Development**: Flexible agent configuration.
- **Publish Agents as MCP Services**: Standardized service output.
- **Multimodal**: Support for text, image, audio, and video processing.

---

## 🚀 Implementation Scenarios

Various AI applications orchestrated via the self-developed LLM platform:

1. **Intelligent Customer Service System**: Automated customer support.
2. **Automatic PPT Generation Tool**: Convert documents to presentations.
3. **DataAgent**: Data visualization.
4. **Law**: PDF/Word material auditing.
5. 

### env config

```
OPENAI_API_KEY=<your-api-key>
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

FLASK_ENV=development
FLASK_DEBUG=1

# sql congig

SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/llmops?client_encoding=utf8
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_ECHO=True
WTF_CSRF_ENABLED=False



#### LangSmith
# https://smith.langchain.com/
> There is a risk of information leakage with official LangSmith; local deployment is not friendly.
> Switching to Langfuse; callbacks will be integrated upon project completion.
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=<your-api-key>
LANGSMITH_PROJECT="llmops" # project name


# redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_USERNAME=
REDIS_USE_SSL=False

#celery
CELERY_BROKER_DB=1
CELERY_RESULT_BACKEND_DB=1
CELERY_TASK_IGNORE_RESULT=False
CELERY_RESULT_EXPIRES=3600
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True


# Gaode Tools
GAODE_API_KEY=

# Google Serper Search https://serper.dev/api-keys
SERPER_API_KEY=


# Tencent Cloud
COS_SECRET_ID=
COS_SECRET_KEY=
COS_BUCKET=
COS_REGION=
COS_SCHEME=https
COS_DOMAIN=


EMBEDDING_MODEL=qwen3-embedding:0.6b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

#### docker postgres

```bash
docker run  --name postgres-dev -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -d postgres
```

#### docker Weaviate

```bash
 docker run -d --name weaviate-dev  -p 8080:8080 -p 50051:50051 cr.weaviate.io/semitechnologies/weaviate:1.35.3
```

#### docker redis

```bash
docker run  --name redis-dev -d -p 6379:6379 redis
```

#### embedding local

> In the development environment, use Ollama to run qw3-embedding:0.6b; choose the model based on actual needs.

#### run project

```bash
# celery asynchronous task processing
celery -A app.http.app.celery worker -l info --pool eventlet --logfile storage/log/celery.log

# dev
 uv run python app\http\app.py
```

##### Initialize migration scripts

```bash
flask --app app.http.app db init 
flask --app app.http.app db migrate 
# -m "msg"

# upgrade
flask --app app.http.app db upgrade

# rollback
flask --app app.http.app db downgrade
```

#### Database Relationship Diagram

```
                                 ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                                 │   UploadFile    │◄────│    Document     │◄────│     Segment     │
                                 │ (Uploaded File)  │ 1:1 │   (Document)    │ 1:N│    (Segment)    │
                                 └─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                                                  │                       │
                                                                  │                       │
                                                      ┌────────────┘                       │
                                                      │                                    │
                                                      ▼                                    ▼
                                             ┌─────────────────┐                 ┌─────────────────┐
                                             │     Dataset     │◄────────────────│  KeywordTable   │
                                             │  (Knowledge Base)│ 1:1             │  (Keyword Table) │
                                             └────────┬────────┘                 └─────────────────┘
                                                      │
                                                      │ N:M
                                                      ▼
                                             ┌─────────────────┐
                                             │ AppDatasetJoin  │
                                             │ (App-KB Link)   │
                                             └─────────────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │       App       │
                                             │    (AI App)     │
                                             └─────────────────┘
```

### Agent Concept and Workflow

```
In LLM applications, if we know the specific sequence of tools required for a user input, using LCEL expressions to build a chain is very useful. However, in certain cases, the number and order of tool usage depend on the input. In these instances, we want the LLM itself to decide the frequency and sequence of tool use, which is exactly what an Agent can do.

In LangChain, an Agent is a core concept representing a system capable of utilizing a language model (LLM) and other tools to execute complex tasks. Agents are designed to handle problems that an LLM might not be able to solve directly, especially when tasks involve multiple steps or require external data sources.

Regardless of how complex an Agent's design or architecture is, the basic workflow is quite simple, consisting of 5 steps:
1. Input Understanding: The Agent first parses the user input to understand the intent and requirements.
2. Plan Customization: Based on the understanding of the input, the Agent formulates an execution plan, deciding which tools to use and in what order.
3. Tool Invocation: The Agent calls the corresponding tools according to the plan to perform the necessary operations.
4. Result Integration: All results returned by the tools are collected, integrated, and parsed to form the final output.
5. Feedback Loop: If the task is not complete or further information is needed, the Agent can iterate through the above process until the completion conditions are met.

┌─────────────┐     ┌─────┐     ┌─────────────┐     ┌─────────┐
│ Initial Quest│────▶│ LLM │────▶│ Formatted Out│────▶│ Tool Select│
└─────────────┘     └──┬──┘     └─────────────┘     └────┬────┘
                       │                                    │
                      Function Call                        Tool List
                                                              │
                        ←───────────────────────────────────┘
                        │        Observation/Loop Execution     │
                        │    (Until completion conditions met)  ↓
                        ▼                              ┌──────────────┐
                    ┌──────────┐                       │ Tool Result   │
                    │   LLM    │ ◀────────────────────┤              │
                    │(Re-invoked)│                       └──────────────┘
                    └──────────┘                          │
                            │                           │ Final Call
                            │                           ↓
                            └────────────────────────►┌──────────────┐
                                                      │ Final Answer   │
                                                      └──────────────┘
```

---

![image](./v2-de187d0b3ac4b7975731b2f1229d67f5_1440w.png)

---

#### PARSING Error

> he words “dog”, “cat” and “banana” are all pretty common in English, so they’re part of the pipeline’s vocabulary, and come with a vector. The word “afskfsd” on the other hand is a lot less common and out-of-vocabulary – so its vector representation consists of 300 dimensions of `0`, which means it’s practically nonexistent. If your application will benefit from a large vocabulary with more vectors, you should consider using one of the larger pipeline packages or loading in a full vector package, for example, [`en_core_web_lg`](https://spacy.io/models/en#en_core_web_lg), which includes 685k unique vectors.
>
> [spacy](https://release-assets.githubusercontent.com/github-production-release-asset/84940268/15132ab6-4050-4914-8fe8-ac2c2fdcb9cf?sp=r&sv=2018-11-09&sr=b&spr=https&se=2026-04-21T16%3A41%3A16Z&rscd=attachment%3B+filename%3Den_core_web_sm-3.8.0-py3-none-any.whl&rsct=application%2Foctet-stream&skoid=96c2d410-5711-43a1-aedd-ab1947aa7ab0&sktid=398a6654-997b-47e9-b12b-9515b896b4de&skt=2026-04-21T15%3A41%3A12Z&ske=2026-04-21T16%3A41%3A16Z&sks=b&skv=2018-11-09&sig=aHrTt9wj8TfEgObDEoIzzNVlpSij42nozL%2BwdsAW34c%3D&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmVsZWFzZS1hc3NldHMuZ2l0aHVidXNlcmNvbnRlbnQuY29tIiwia2V5Ijoia2V5MSIsImV4cCI6MTc3Njc4Nzg3MiwibmJmIjoxNzc2Nzg2MDcyLCJwYXRoIjoicmVsZWFzZWFzc2V0cHJvZHVjdGlvbi5ibG9iLmNvcmUud2luZG93cy5uZXQifQ.ZhgBi8DhMZDGxlME2M_MlPB7iubVUKFXdStaeWcZwd0&response-content-disposition=attachment%3B%20filename%3Den_core_web_sm-3.8.0-py3-none-any.whl&response-content-type=application%2Foctet-stream)

```
pip install en_core_web_sm-3.8.0-py3-none-any.whl
```

#### Reference Documentation

[Hello-Agents](https://datawhalechina.github.io/hello-agents/#/)

[langchain Docs(TS) ](https://docs.langchain.com/oss/javascript/langchain/quickstart)

[langchain Docs(py) ](https://docs.langchain.com/oss/python/langchain/quickstart)

[langchain Docs Chinese](https://langchain-doc.cn/)

[uv/pip](https://uv.oaix.tech/blog/2025/06/17/quickly-set-uv-package-index-is-china-mirror/#__tabbed_1_3)

[weaviate](https://docs.weaviate.org.cn/deploy)

[flask](https://flask.org.cn/en/stable/)

[llm-action](https://github.com/liguodongiot/llm-action)
