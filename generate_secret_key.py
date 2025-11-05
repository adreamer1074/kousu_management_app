#!/usr/bin/env python3
"""
Django SECRET_KEY生成スクリプト
"""

def generate_secret_key():
    """
    Django用のSECRET_KEYを生成します
    """
    try:
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()
    except ImportError:
        # Djangoがインストールされていない場合の代替方法
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(alphabet) for i in range(50))

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Django SECRET_KEY Generator")
    print("=" * 60)
    
    secret_key = generate_secret_key()
    
    print(f"生成されたSECRET_KEY:")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("⚠️  このキーをRender.comの環境変数に設定してください！")
    print("⚠️  このキーは秘密にして、他人と共有しないでください！")
    print("=" * 60)