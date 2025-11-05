"""
Render.com用のDjango設定ファイル
"""

import os
import dj_database_url
from .settings import *

# デバッグモードを無効化
DEBUG = False

# シークレットキーを環境変数から取得
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-fallback-secret-key')

# 許可されたホストの設定
ALLOWED_HOSTS = [
    '.onrender.com',  # Renderのドメイン
    'localhost',
    '127.0.0.1',
]

# データベース設定
# Renderでは無料プランでPostgreSQLが利用可能
if 'DATABASE_URL' in os.environ:
    # PostgreSQL設定（Renderから自動で設定される）
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # ローカル開発用にSQLiteを維持
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# セキュリティ設定
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 静的ファイル設定
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoiseを使用して静的ファイルを配信
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# WhiteNoise設定
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ログ設定
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}