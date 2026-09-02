# 1. 使用 alpine 版本，体积减小 60% 以上，拉取和构建更快
FROM node:20-alpine as builder

WORKDIR /app/web

# 2. 仅拷贝依赖文件，充分利用 Docker 缓存机制
# 只要 package.json 和 yarn.lock 不变，后续构建这一步会“秒过”
COPY package.json yarn.lock ./

# 3. 合并 RUN 指令，配置国内源，并增加防超时和冻结参数
# --frozen-lockfile 确保安装版本严格一致，--network-timeout 防止国内网络波动卡死
RUN yarn config set registry https://registry.npmmirror.com/ && \
    yarn install --frozen-lockfile --network-timeout 100000

# 4. 最后拷贝源代码 (必须配合 .dockerignore 使用，否则极慢)
COPY . .

# 5. 建议使用 ARG 传入环境变量，避免硬编码 IP，提高多环境部署灵活性
ARG VITE_API_PREFIX=/api
ENV VITE_API_PREFIX=${VITE_API_PREFIX}

# 构建项目
RUN yarn build

# ================= 生产阶段 =================
FROM nginx:1.22.1 as production

# 【修正】把 /run/nginx.pid 替换为 /tmp/nginx.pid
RUN sed -i 's|/run/nginx.pid|/tmp/nginx.pid|g' /etc/nginx/nginx.conf

COPY --from=builder /app/web/dist /usr/share/nginx/html
COPY --from=builder /app/web/docker/nginx.conf /etc/nginx/conf.d/default.conf

# 设置权限 (可选)
RUN find /usr/share/nginx/html -type d -exec chmod 755 {} \;
RUN find /usr/share/nginx/html -type f -exec chmod 644 {} \;

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
