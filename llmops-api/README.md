
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
