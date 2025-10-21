FROM docker.1ms.run/node:20-alpine
WORKDIR /usr/src/app

# 配置 npm 镜像源（加速安装）
RUN npm config set registry https://registry.npmmirror.com

# 复制 package.json
COPY package.json ./

# 安装依赖
RUN npm install --legacy-peer-deps || npm install --force

# 复制所有文件
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"] 
