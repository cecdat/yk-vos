# 生产环境 Dockerfile
# 使用多阶段构建，最终镜像更小更快

# 阶段 1: 依赖安装（基于基础镜像）
FROM yk-vos-frontend-base:latest AS deps
WORKDIR /usr/src/app

# 安装依赖（基础镜像已配置 npm）
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps || npm install --force

# 阶段 2: 构建应用
FROM docker.1ms.run/node:20-alpine AS builder
WORKDIR /usr/src/app

# 从 deps 阶段复制 node_modules
COPY --from=deps /usr/src/app/node_modules ./node_modules
COPY . .

# 确保 public 目录存在
RUN mkdir -p public

# 构建生产版本
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# 阶段 3: 运行应用
FROM docker.1ms.run/node:20-alpine AS runner
WORKDIR /usr/src/app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制必要文件
COPY --from=builder /usr/src/app/public ./public
COPY --from=builder --chown=nextjs:nodejs /usr/src/app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /usr/src/app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 使用 standalone 模式启动（更快）
CMD ["node", "server.js"]
