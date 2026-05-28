"""
# config.py

## 核心功能
应用配置管理中心。
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dataset-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    PORT = int(os.environ.get('PORT', '8081'))
    HOST = os.environ.get('HOST', '127.0.0.1')

    API_TOKEN = (os.environ.get('API_TOKEN') or '').strip()

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'webp'}
    ALLOWED_LABEL_EXTENSIONS = {'txt'}
    ALLOWED_CONFIG_EXTENSIONS = {'yaml', 'yml', 'json'}

    @classmethod
    def get_app_root(cls):
        return os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def get_previews_dir(cls):
        return os.path.join(cls.get_app_root(), 'static', 'previews')

    @classmethod
    def get_uploads_dir(cls):
        return os.path.join(cls.get_app_root(), 'uploads')

    @classmethod
    def init_folders(cls):
        os.makedirs(cls.get_previews_dir(), exist_ok=True)
        os.makedirs(cls.get_uploads_dir(), exist_ok=True)
        os.makedirs(os.path.join(cls.get_app_root(), 'logs'), exist_ok=True)
