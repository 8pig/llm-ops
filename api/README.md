
# api-doc
>https://ptrb24jefd.apifox.cn/

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
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=
LANGSMITH_PROJECT="llmops"



# Weaviate向量数据库配置
WEAVIATE_HOST=127.0.0.1
WEAVIATE_PORT=8080


# 高德工具
GAODE_API_KEY=

# 谷歌serper搜索 https://serper.dev/api-keys
SERPER_API_KEY=


# 腾讯云
COS_SECRET_ID=
COS_SECRET_KEY=
COS_BUCKET=
COS_REGION=
COS_SCHEME=https
COS_DOMAIN=



TAVILY_API_KEY=

```






# run project
```bash
# dev
 uv run python app\http\app.py
```

## docker postgres 
```bash
docker run  --name postgres-dev -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -d postgres
```

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
