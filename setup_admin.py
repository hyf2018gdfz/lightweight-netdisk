#!/usr/bin/env python
"""
管理员账户设置脚本
用于首次部署时设置管理员账户密码
"""

import os
import sys
import getpass
import asyncio
from app.database import get_db_context
from app.models.user import User
from app.config import settings


def generate_secure_password(length=16):
    """生成安全的随机密码"""
    import secrets
    import string
    
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


async def setup_admin():
    """设置管理员账户"""
    print("🔐 个人网盘系统 - 管理员账户设置")
    print("=" * 50)
    
    with get_db_context() as db:
        admin_username = settings.DEFAULT_ADMIN_USERNAME
        
        # 检查是否已存在管理员用户
        existing_user = db.query(User).filter(User.username == admin_username).first()
        
        if existing_user:
            print(f"⚠️ 管理员用户 '{admin_username}' 已存在")
            choice = input("是否要重置密码? (y/N): ").lower().strip()
            if choice not in ['y', 'yes']:
                print("操作已取消")
                return
        
        # 获取新密码
        print(f"\n设置管理员用户 '{admin_username}' 的密码:")
        print("1. 手动输入密码")
        print("2. 生成随机密码")
        
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "2":
            new_password = generate_secure_password()
            print(f"\n🔑 生成的随机密码: {new_password}")
            print("⚠️ 请务必保存此密码！")
        else:
            while True:
                new_password = getpass.getpass("请输入新密码: ")
                if len(new_password) < 8:
                    print("❌ 密码长度至少8位，请重新输入")
                    continue
                
                confirm_password = getpass.getpass("请确认密码: ")
                if new_password != confirm_password:
                    print("❌ 两次输入的密码不一致，请重新输入")
                    continue
                
                break
        
        # 更新或创建用户
        if existing_user:
            existing_user.hashed_password = User.hash_password(new_password)
            db.commit()
            print(f"✅ 管理员用户 '{admin_username}' 密码已更新")
        else:
            new_user = User(
                username=admin_username,
                hashed_password=User.hash_password(new_password),
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print(f"✅ 管理员用户 '{admin_username}' 已创建")
        
        # 生成环境变量配置
        print("\n📋 为了安全，建议设置以下环境变量:")
        print(f"export DEFAULT_ADMIN_USERNAME={admin_username}")
        print(f"export DEFAULT_ADMIN_PASSWORD={new_password}")
        
        # 询问是否创建 .env 文件
        create_env = input("\n是否创建 .env 文件保存配置? (y/N): ").lower().strip()
        if create_env in ['y', 'yes']:
            env_content = f"""# 个人网盘系统配置
# 生产环境配置示例

# 应用配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 安全配置
SECRET_KEY={generate_secure_password(32)}
CORS_ORIGINS=*
TRUSTED_HOSTS=*

# 管理员配置
DEFAULT_ADMIN_USERNAME={admin_username}
DEFAULT_ADMIN_PASSWORD={new_password}

# 文件配置
MAX_FILE_SIZE=104857600
STORAGE_PATH=./storage
TRASH_PATH=./trash

# 数据库配置
DATABASE_URL=sqlite:///./database.db
"""
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print("✅ .env 文件已创建")
            print("⚠️ 请确保 .env 文件的权限安全 (chmod 600 .env)")
        
        print("\n🚀 管理员设置完成！现在可以启动系统了:")
        print("python main.py")


def main():
    """主函数"""
    try:
        # 确保数据库初始化
        from app.database import init_db
        
        print("正在初始化数据库...")
        asyncio.run(init_db())
        
        # 设置管理员
        asyncio.run(setup_admin())
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()