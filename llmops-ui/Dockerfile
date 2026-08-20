FROM node:24 AS builder
WORKDIR /app
COPY . .
RUN npm install



FROM node:24
WORKDIR /app
COPY --form=builder /app /app
CMD ["npm", "start"]

#构建 镜像
# docker build -f llmops-ui/Dockerfile -t llmops-ui:1.0.0 llmops-ui

# 运行
# docker run -d -p 5173:80 --name llmops-ui llmops-ui:1.0.0

# 进入容器
# docker exec -it llmops-ui /bin/sh




