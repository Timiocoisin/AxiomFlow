"""
数据库迁移脚本：将 documents 表的 json_data 列从 TEXT 改为 LONGTEXT

运行方式：
    python migrate_json_data_to_longtext.py
"""

import sys
from sqlalchemy import create_engine, text
from app.core.config import settings


def migrate():
    """将 json_data 列从 TEXT 改为 LONGTEXT"""
    database_url = settings.database_url
    print(f"连接到数据库: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    if not database_url.startswith("mysql"):
        print("此迁移脚本仅适用于 MySQL 数据库")
        return
    
    engine = create_engine(database_url, echo=False)
    
    with engine.connect() as conn:
        # 检查列是否存在
        check_sql = """
            SELECT COLUMN_TYPE 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'documents' 
            AND COLUMN_NAME = 'json_data'
        """
        result = conn.execute(text(check_sql))
        row = result.fetchone()
        
        if not row:
            print("json_data 列不存在，请先运行 migrate_add_json_data.py")
            return
        
        current_type = row[0].upper()
        if 'LONGTEXT' in current_type:
            print(f"json_data 列已经是 LONGTEXT 类型（当前: {current_type}），无需迁移")
            return
        
        # 修改列类型为 LONGTEXT（MySQL 不允许 TEXT/LONGTEXT 有默认值）
        print(f"当前 json_data 列类型: {current_type}")
        print("正在将 json_data 列改为 LONGTEXT...")
        alter_sql = """
            ALTER TABLE documents 
            MODIFY COLUMN json_data LONGTEXT
        """
        conn.execute(text(alter_sql))
        conn.commit()
        print("成功将 json_data 列改为 LONGTEXT")


if __name__ == "__main__":
    try:
        migrate()
        print("\n迁移完成！")
    except Exception as e:
        print(f"\n迁移失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

