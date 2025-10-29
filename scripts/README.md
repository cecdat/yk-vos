# YK-VOS 部署脚本说明

## 脚本列表

| 脚本名称 | 功能 | 适用场景 |
|----------|------|----------|
| `one_click_deploy.sh` | 一键部署脚本 | 自动检测环境，选择部署方式 |
| `fresh_install.sh` | 全新安装脚本 | 新服务器，无现有数据 |
| `upgrade_migration.sh` | 升级迁移脚本 | 已有数据，需要升级 |
| `backup_data.sh` | 数据备份脚本 | 定期备份数据 |
| `restore_data.sh` | 数据恢复脚本 | 从备份恢复数据 |

## 使用方法

### 1. 一键部署（推荐）

```bash
# 下载并执行一键部署脚本
wget https://raw.githubusercontent.com/your-repo/yk-vos/main/scripts/one_click_deploy.sh
chmod +x one_click_deploy.sh
sudo ./one_click_deploy.sh
```

### 2. 全新安装

```bash
# 下载并执行全新安装脚本
wget https://raw.githubusercontent.com/your-repo/yk-vos/main/scripts/fresh_install.sh
chmod +x fresh_install.sh
sudo ./fresh_install.sh
```

### 3. 升级迁移

```bash
# 下载并执行升级脚本
wget https://raw.githubusercontent.com/your-repo/yk-vos/main/scripts/upgrade_migration.sh
chmod +x upgrade_migration.sh
sudo ./upgrade_migration.sh
```

### 4. 数据备份

```bash
# 执行数据备份
cd /opt/yk-vos
sudo ./scripts/backup_data.sh
```

### 5. 数据恢复

```bash
# 从备份恢复数据
cd /opt/yk-vos
sudo ./scripts/restore_data.sh /opt/yk-vos-backups/backup-20240101-120000.tar.gz
```

## 脚本功能详解

### one_click_deploy.sh
- **自动检测**：检测现有安装、Docker环境、系统要求
- **智能选择**：自动选择全新安装或升级迁移
- **完整部署**：包含所有必要的安装和配置步骤
- **验证检查**：部署完成后自动验证服务状态

### fresh_install.sh
- **系统检查**：检查操作系统、内存、磁盘空间
- **Docker安装**：自动安装Docker和Docker Compose
- **项目部署**：下载代码、配置环境、启动服务
- **数据库初始化**：创建表结构、插入初始数据
- **服务管理**：创建系统服务、配置防火墙

### upgrade_migration.sh
- **数据备份**：自动备份现有数据
- **服务停止**：安全停止现有服务
- **代码更新**：从Git仓库更新代码
- **数据库迁移**：执行数据库升级脚本
- **服务启动**：启动升级后的服务
- **验证检查**：验证升级结果

### backup_data.sh
- **全量备份**：备份PostgreSQL、Redis、ClickHouse数据
- **配置备份**：备份环境变量、配置文件
- **压缩存储**：自动压缩备份文件
- **定期清理**：自动清理旧备份文件

### restore_data.sh
- **数据恢复**：从备份文件恢复所有数据
- **服务重启**：安全重启所有服务
- **验证检查**：验证恢复结果
- **错误处理**：完善的错误处理和回滚机制

## 环境要求

### 系统要求
- **操作系统**：Ubuntu 20.04+, CentOS 7+, Debian 10+
- **内存**：4GB以上
- **磁盘**：50GB以上可用空间
- **网络**：稳定的网络连接

### 软件要求
- **Docker**：20.10+
- **Docker Compose**：2.0+
- **Git**：2.0+（可选）

## 部署流程

### 全新安装流程
1. 检查系统要求
2. 安装Docker和Docker Compose
3. 创建项目目录
4. 下载项目代码
5. 配置环境变量
6. 初始化数据库
7. 启动应用服务
8. 创建系统服务
9. 配置防火墙
10. 验证部署结果

### 升级迁移流程
1. 检查现有安装
2. 备份现有数据
3. 停止现有服务
4. 更新项目代码
5. 更新Docker镜像
6. 执行数据库迁移
7. 更新环境配置
8. 启动升级服务
9. 验证升级结果

## 故障排除

### 常见问题

#### 1. 权限问题
```bash
# 确保脚本有执行权限
chmod +x scripts/*.sh

# 使用root权限执行
sudo ./scripts/one_click_deploy.sh
```

#### 2. 网络问题
```bash
# 检查网络连接
ping 8.8.8.8

# 检查DNS解析
nslookup github.com
```

#### 3. 磁盘空间不足
```bash
# 检查磁盘空间
df -h

# 清理无用文件
docker system prune -a
```

#### 4. 端口占用
```bash
# 检查端口占用
netstat -tlnp | grep :3000
netstat -tlnp | grep :3001

# 停止占用端口的服务
sudo kill -9 <PID>
```

### 日志查看

```bash
# 查看部署日志
tail -f /var/log/yk-vos-deploy.log

# 查看服务日志
docker compose logs -f

# 查看系统日志
journalctl -u yk-vos -f
```

## 安全注意事项

1. **修改默认密码**：首次登录后立即修改默认密码
2. **配置防火墙**：只开放必要的端口
3. **定期备份**：设置定期备份任务
4. **更新系统**：定期更新系统和依赖包
5. **监控日志**：定期检查系统和服务日志

## 支持与反馈

如遇到问题，请提供以下信息：

1. 操作系统版本
2. Docker版本
3. 错误日志
4. 服务状态
5. 网络配置

联系方式：
- 邮箱: support@example.com
- 文档: https://docs.example.com
- 问题反馈: https://github.com/your-repo/yk-vos/issues
