"""
迁移脚本：删除 users 表中的 is_email_verified 和 email_verified_at 字段

运行方式：
    python migrate_remove_email_verified.py
"""

import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    database_url = settings.database_url
    print(f"连接到数据库: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    engine = create_engine(database_url, echo=False)
    
    with engine.connect() as conn:
        # 检查 is_email_verified 列是否存在
        check_is_email_verified_sql = """
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'is_email_verified'
        """
        result = conn.execute(text(check_is_email_verified_sql))
        has_is_email_verified = result.fetchone() is not None
        
        # 检查 email_verified_at 列是否存在
        check_email_verified_at_sql = """
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'email_verified_at'
        """
        result = conn.execute(text(check_email_verified_at_sql))
        has_email_verified_at = result.fetchone() is not None
        
        if not has_is_email_verified and not has_email_verified_at:
            print("is_email_verified 和 email_verified_at 列都不存在，无需迁移")
            return
        
        # 删除 is_email_verified 列
        if has_is_email_verified:
            print("正在删除 is_email_verified 列...")
            alter_sql = """
                ALTER TABLE users 
                DROP COLUMN is_email_verified
            """
            conn.execute(text(alter_sql))
            conn.commit()
            print("成功删除 is_email_verified 列")
        
        # 删除 email_verified_at 列
        if has_email_verified_at:
            print("正在删除 email_verified_at 列...")
            alter_sql = """
                ALTER TABLE users 
                DROP COLUMN email_verified_at
            """
            conn.execute(text(alter_sql))
            conn.commit()
            print("成功删除 email_verified_at 列")

if __name__ == "__main__":
    try:
        migrate()
        print("\n迁移完成！")
        sys.exit(0)
    except Exception as e:
        print(f"\n迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

