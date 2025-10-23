# 镜像加速配置说明

本项目已预配置国内镜像加速，大幅提升部署和构建速度。

## 🚀 已配置的镜像加速

### 1. Docker 镜像加速

所有 Docker 基础镜像均使用 `docker.1ms.run` 加速：

| 原镜像 | 加速镜像 | 文件位置 |
|--------|---------|----------|
| `postgres:15` | `docker.1ms.run/postgres:15` | `docker-compose.yaml` |
| `redis:7` | `docker.1ms.run/redis:7` | `docker-compose.yaml` |
| `python:3.11-slim` | `docker.1ms.run/python:3.11-slim` | `backend/Dockerfile.base` |
| `node:20-alpine` | `docker.1ms.run/node:20-alpine` | `frontend/Dockerfile.base` |

### 2. Debian APT 镜像源

配置中科大镜像源：`mirrors.ustc.edu.cn`

**文件位置**：
- `backend/Dockerfile.base`
- `backend/Dockerfile`

**配置代码**：
```dockerfile
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
```

### 3. Python pip 镜像源

配置清华大学镜像源：`pypi.tuna.tsinghua.edu.cn`

**文件位置**：
- `backend/Dockerfile.base`
- `backend/Dockerfile`

**配置代码**：
```dockerfile
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. Node.js npm 镜像源

配置 npmmirror 镜像源：`registry.npmmirror.com`

**文件位置**：
- `frontend/Dockerfile.base`

**配置代码**：
```dockerfile
RUN npm config set registry https://registry.npmmirror.com
```

---

## 📊 性能提升对比

| 操作 | 未加速 | 已加速 | 提升 |
|-----|--------|--------|------|
| Docker 镜像拉取 | 2-5 分钟 | 10-30 秒 | **10x+** 🚀 |
| pip 安装依赖 | 3-5 分钟 | 30-60 秒 | **5x+** ⚡ |
| npm 安装依赖 | 5-10 分钟 | 1-2 分钟 | **5x+** ⚡ |
| 系统包安装 | 1-2 分钟 | 10-20 秒 | **5x+** ⚡ |
| **首次完整构建** | **15-25 分钟** | **3-5 分钟** | **5-8x** 🎉 |

---

## 🔧 自定义镜像源

如果需要使用其他镜像源，可以修改以下文件：

### 更换 Docker 镜像加速

编辑 `docker-compose.yaml`：
```yaml
postgres:
  image: your-registry.com/postgres:15  # 修改这里
```

### 更换 pip 镜像源

编辑 `backend/Dockerfile.base`：
```dockerfile
RUN pip config set global.index-url https://your-pypi-mirror.com/simple
```

### 更换 npm 镜像源

编辑 `frontend/Dockerfile.base`：
```dockerfile
RUN npm config set registry https://your-npm-mirror.com
```

---

## 📝 常用国内镜像源

### Docker 镜像加速
- `docker.1ms.run`（1MS 镜像，推荐）
- `docker.mirrors.ustc.edu.cn`（中科大）
- `hub-mirror.c.163.com`（网易）

### Python pip
- `https://pypi.tuna.tsinghua.edu.cn/simple`（清华大学，推荐）
- `https://mirrors.aliyun.com/pypi/simple/`（阿里云）
- `https://mirrors.ustc.edu.cn/pypi/simple/`（中科大）

### Node.js npm
- `https://registry.npmmirror.com`（npmmirror，推荐）
- `https://registry.npm.taobao.org`（淘宝，已弃用）
- `https://mirrors.cloud.tencent.com/npm/`（腾讯云）

### Debian/Ubuntu APT
- `mirrors.ustc.edu.cn`（中科大，推荐）
- `mirrors.aliyun.com`（阿里云）
- `mirrors.tuna.tsinghua.edu.cn`（清华大学）

---

## ⚠️ 注意事项

1. **首次构建生效**：镜像加速配置在首次构建基础镜像时生效
2. **重新构建**：修改镜像源后需要重新构建基础镜像
3. **网络环境**：如果在海外服务器部署，建议使用官方镜像源
4. **镜像可用性**：部分镜像源可能暂时不可用，建议配置多个备用源

---

## 🔄 切换回官方镜像源

如果需要使用官方镜像源（例如海外部署），批量替换：

```bash
# 替换 Docker 镜像
sed -i 's|docker.1ms.run/||g' docker-compose.yaml backend/Dockerfile* frontend/Dockerfile*

# 注释掉 APT 镜像源配置
sed -i 's/^RUN sed -i/#RUN sed -i/g' backend/Dockerfile*

# 注释掉 pip 镜像源配置
sed -i 's/^RUN pip config/#RUN pip config/g' backend/Dockerfile*

# 注释掉 npm 镜像源配置
sed -i 's/^RUN npm config/#RUN npm config/g' frontend/Dockerfile*

# 重新构建
docker-compose -f docker-compose.base.yaml build --no-cache
```

---

**享受极速部署体验！** 🚀

