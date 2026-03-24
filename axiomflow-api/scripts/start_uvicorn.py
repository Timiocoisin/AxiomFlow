#!/usr/bin/env python3
"""
启动 Uvicorn 服务器的 Python 脚本

使用方法:
    python scripts/start_uvicorn.py
    或指定参数:
    python scripts/start_uvicorn.py --host 0.0.0.0 --port 8000 --reload
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import logging
    import sys
    import uvicorn
    
    # 在启动 Uvicorn 之前配置日志
    from app.core.config import settings
    from app.core.observability import setup_logging
    
    # 配置主程序日志到文件，禁用控制台输出
    setup_logging(json_logs=bool(getattr(settings, "log_json", False)), log_type="app")
    
    # 获取命令行参数
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # 解析参数
    host = "0.0.0.0"
    port = 8000
    reload = True
    
    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--reload":
            reload = True
            i += 1
        elif args[i] == "--no-reload":
            reload = False
            i += 1
        else:
            i += 1
    
    # 配置 Uvicorn，使用我们自己的日志配置
    # 通过 log_config=None 禁用 Uvicorn 的默认日志配置
    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,  # 仍然记录访问日志，但会写入文件
        log_config=None,  # 不使用默认日志配置，使用我们自己的
    )
    
    # 创建服务器并启动
    server = uvicorn.Server(config)
    server.run()

