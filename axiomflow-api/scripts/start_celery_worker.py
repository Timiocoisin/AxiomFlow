#!/usr/bin/env python3
"""
启动 Celery Worker 的 Python 脚本

使用方法:
    python scripts/start_celery_worker.py worker --loglevel=info
    或直接运行（使用默认参数）:
    python scripts/start_celery_worker.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from app.celery_app import celery_app

    # 获取命令行参数（排除脚本名称）
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # 检查是否提供了 Celery 命令（worker, beat, flower 等）
    celery_commands = ["worker", "beat", "flower", "shell", "inspect", "control"]
    has_command = len(args) > 0 and args[0] in celery_commands
    
    if not has_command:
        # 没有提供命令，使用默认参数启动 worker
        # Windows上使用solo pool避免"not enough values to unpack"错误
        import platform
        pool_type = "solo" if platform.system() == "Windows" else "prefork"
        # argv 格式: [命令, ...参数]
        argv = ["worker", "--loglevel=info", f"--pool={pool_type}"] + args
    else:
        # 已经提供了命令，直接使用
        # 如果是worker命令且没有指定pool，Windows上自动添加solo
        import platform
        if platform.system() == "Windows" and args[0] == "worker":
            # 检查是否已经指定了pool
            has_pool = any("--pool" in arg or "-P" in arg for arg in args)
            if not has_pool:
                args.append("--pool=solo")
        argv = args
    
    # 启动 Celery
    # start() 方法的 argv 参数应该包含命令和参数，不包括程序名
    celery_app.start(argv=argv)

