#!/bin/bash
# 检查 Celery 服务状态和任务执行

echo "========================================="
echo "1. 检查 Celery Worker 容器状态"
echo "========================================="
docker ps | grep celery

echo ""
echo "========================================="
echo "2. 检查 Celery Worker 日志（最近50条）"
echo "========================================="
docker logs yk_vos_celery_worker --tail 50

echo ""
echo "========================================="
echo "3. 检查 Celery Beat 容器状态"
echo "========================================="
docker ps | grep celery_beat

echo ""
echo "========================================="
echo "4. 进入 Celery Worker 检查任务注册"
echo "========================================="
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect registered | head -50

echo ""
echo "========================================="
echo "5. 检查 Redis 连接"
echo "========================================="
docker exec -it yk_vos_redis redis-cli ping

echo ""
echo "========================================="
echo "6. 检查 Redis 中的任务队列"
echo "========================================="
docker exec -it yk_vos_redis redis-cli llen celery

echo ""
echo "完成！"

