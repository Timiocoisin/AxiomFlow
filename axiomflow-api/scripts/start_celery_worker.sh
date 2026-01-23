#!/bin/bash
# 启动 Celery Worker 脚本

cd "$(dirname "$0")/.."

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 启动 Celery Worker
celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=translation,batch,default \
    --hostname=worker@%h

