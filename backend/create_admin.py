"""
创建初始管理员账户脚本
使用方法：python create_admin.py
"""

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.user_model import User, UserRole
from app.services.auth.security import get_password_hash

def create_initial_admin():
    # 创建数据库表
    from app.db.user_model import Base
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已有管理员
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if admin:
            print(f"已存在管理员账户：{admin.username}")
            return
        
        # 创建默认管理员账户
        admin_user = User(
            username="admin",
            email="admin@tcm-kg.com",
            hashed_password=get_password_hash("admin123"),  # 默认密码
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("=" * 50)
        print("✓ 初始管理员账户创建成功！")
        print("=" * 50)
        print(f"用户名：admin")
        print(f"密码：admin123")
        print("=" * 50)
        print("⚠️  首次登录后请立即修改密码！")
        print("=" * 50)
        
    except Exception as e:
        print(f"创建失败：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()
