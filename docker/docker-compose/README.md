# MLflow Docker Compose 部署

本目录包含 DSPyUI 的 MLflow 服务 Docker Compose 配置。

## 架构

```
┌─────────────────────────────────────────┐
│         MLflow Docker 服务              │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │    MinIO     │    │
│  │   (元数据)   │  │  (工件存储)  │    │
│  │    :5432     │  │  :9000/9001  │    │
│  └──────────────┘  └──────────────┘    │
│         │                  │            │
│         └────────┬─────────┘            │
│                  │                      │
│         ┌────────▼────────┐             │
│         │  MLflow Server  │             │
│         │     :5000       │             │
│         └─────────────────┘             │
└─────────────────────────────────────────┘
```

## 服务说明

### PostgreSQL
- **用途**: 存储 MLflow 实验元数据（运行记录、参数、指标等）
- **端口**: 5432
- **数据卷**: `pgdata`

### MinIO
- **用途**: S3 兼容的对象存储，用于存储模型工件
- **端口**: 
  - 9000: API 端口
  - 9001: Web 控制台
- **数据卷**: `minio-data`
- **默认凭证**:
  - 用户名: `minio`
  - 密码: `minio123`

### MLflow Server
- **用途**: MLflow 追踪服务器和 UI
- **端口**: 5000
- **依赖**: PostgreSQL + MinIO

## 快速开始

### 1. 启动服务

```bash
# 使用快速启动脚本（推荐）
bash start.sh

# 或使用 docker-compose 命令
docker-compose up -d
```

### 2. 验证服务

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mlflow
```

### 3. 访问服务

- **MLflow UI**: http://localhost:5000
- **MinIO 控制台**: http://localhost:9001
  - 用户名: `minio`
  - 密码: `minio123`

## 管理命令

### 使用快速启动脚本

```bash
# 启动服务
bash start.sh start

# 停止服务
bash start.sh stop

# 重启服务
bash start.sh restart

# 查看状态
bash start.sh status

# 查看日志
bash start.sh logs

# 清理所有数据
bash start.sh clean
```

### 使用 docker-compose

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f [service_name]

# 查看服务状态
docker-compose ps
```

## 配置

### 环境变量

配置文件: `.env`

```bash
# PostgreSQL 配置
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=mlflow
POSTGRES_DB=mlflow

# MinIO 配置
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_BUCKET=mlflow

# MLflow 配置
MLFLOW_HOST=0.0.0.0
MLFLOW_PORT=5000
MLFLOW_VERSION=latest
```

### 修改端口

如果默认端口被占用，可以修改 `.env` 文件：

```bash
# 修改 MLflow 端口
MLFLOW_PORT=5001

# 修改 MinIO 端口
MINIO_PORT=9002
```

然后重启服务：

```bash
docker-compose down
docker-compose up -d
```

## 数据持久化

### 数据卷

Docker Compose 使用命名卷存储数据：

- `pgdata`: PostgreSQL 数据库数据
- `minio-data`: MinIO 对象存储数据

### 查看数据卷

```bash
# 列出所有卷
docker volume ls | grep mlflow

# 查看卷详情
docker volume inspect docker-compose_pgdata
docker volume inspect docker-compose_minio-data
```

### 备份数据

```bash
# 备份 PostgreSQL
docker-compose exec postgres pg_dump -U mlflow mlflow > backup.sql

# 备份 MinIO（使用 mc 客户端）
docker run --rm -it --network mlflow-network \
  -v $(pwd)/backup:/backup \
  minio/mc:latest \
  mirror myminio/mlflow /backup
```

### 恢复数据

```bash
# 恢复 PostgreSQL
cat backup.sql | docker-compose exec -T postgres psql -U mlflow mlflow

# 恢复 MinIO
docker run --rm -it --network mlflow-network \
  -v $(pwd)/backup:/backup \
  minio/mc:latest \
  mirror /backup myminio/mlflow
```

## 故障排除

### 服务无法启动

**检查端口占用**:
```bash
lsof -i :5000  # MLflow
lsof -i :5432  # PostgreSQL
lsof -i :9000  # MinIO API
lsof -i :9001  # MinIO Console
```

**查看日志**:
```bash
docker-compose logs mlflow
docker-compose logs postgres
docker-compose logs minio
```

### 连接失败

**检查网络**:
```bash
docker network ls | grep mlflow
docker network inspect mlflow-network
```

**测试连接**:
```bash
# 测试 MLflow
curl http://localhost:5000/health

# 测试 MinIO
curl http://localhost:9000/minio/health/live
```

### 数据丢失

**检查数据卷**:
```bash
docker volume ls | grep mlflow
```

**注意**: 使用 `docker-compose down -v` 会删除所有数据卷！

### 性能问题

**增加 Docker 资源**:
- Docker Desktop > Settings > Resources
- 增加 CPU 和内存限制

**清理旧数据**:
```bash
# 进入 MLflow UI 删除旧实验
# 或使用 MLflow API
```

## 安全建议

### 生产环境

1. **修改默认密码**:
   ```bash
   # .env
   POSTGRES_PASSWORD=your_secure_password
   MINIO_ROOT_PASSWORD=your_secure_password
   ```

2. **限制端口暴露**:
   ```yaml
   # docker-compose.yml
   ports:
     - "127.0.0.1:5432:5432"  # 仅本地访问
   ```

3. **使用 HTTPS**:
   - 配置反向代理（Nginx/Caddy）
   - 添加 SSL 证书

4. **定期备份**:
   - 设置自动备份脚本
   - 测试恢复流程

## 升级

### 升级 MLflow 版本

```bash
# 修改 .env
MLFLOW_VERSION=v2.10.0

# 重新拉取镜像
docker-compose pull mlflow

# 重启服务
docker-compose up -d mlflow
```

### 升级其他服务

```bash
# 拉取最新镜像
docker-compose pull

# 重启所有服务
docker-compose up -d
```

## 监控

### 健康检查

所有服务都配置了健康检查：

```bash
# 查看健康状态
docker-compose ps
```

### 资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

## 相关文档

- [MLflow 集成指南](../../docs/mlflow_integration.md)
- [Docker 架构文档](../../docs/docker_architecture.md)
- [MLflow 官方文档](https://mlflow.org/docs/latest/index.html)
- [MinIO 文档](https://min.io/docs/minio/linux/index.html)
