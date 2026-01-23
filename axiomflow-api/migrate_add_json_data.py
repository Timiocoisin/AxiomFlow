"""
数据库迁移脚本：为 documents 表添加 json_data 列

运行方式：
    python migrate_add_json_data.py
"""

import sys
from sqlalchemy import create_engine, text
from app.core.config import settings


def migrate():
    """添加 json_data 列到 documents 表"""
    database_url = settings.database_url
    print(f"连接到数据库: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    engine = create_engine(database_url, echo=False)
    
    with engine.connect() as conn:
        # 检查列是否已存在
        check_sql = """
            SELECT COUNT(*) as count 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'documents' 
            AND COLUMN_NAME = 'json_data'
        """
        result = conn.execute(text(check_sql))
        count = result.fetchone()[0]
        
        if count > 0:
            print("json_data 列已存在，无需迁移")
            return
        
        # 添加 json_data 列
        print("正在添加 json_data 列...")
        alter_sql = """
            ALTER TABLE documents 
            ADD COLUMN json_data TEXT 
            AFTER json_path
        """
        conn.execute(text(alter_sql))
        conn.commit()
        print("成功添加 json_data 列")


if __name__ == "__main__":
    try:
        migrate()
        print("\n迁移完成！")
        sys.exit(0)
    except Exception as e:
        print(f"\n迁移失败: {e}")
        sys.exit(1)

