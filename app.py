"""
# app.py

## 核心功能
Easy Dataset Station 主应用入口，负责初始化 Flask 应用、SocketIO 服务和注册 API 蓝图。
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config
from routes import main_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config.from_object(Config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

Config.init_folders()

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

app.register_blueprint(main_bp)

from routes.main_routes import register_socketio_events
register_socketio_events(socketio)


def is_embedded_runtime():
    return os.environ.get('EASY_DATASET_EMBEDDED', '').lower() in {'1', 'true', 'yes'}


@app.route('/health')
def health_check():
    return {
        'status': 'ok',
        'message': 'Easy Dataset Station is running',
    }


@app.route('/previews/<path:filename>')
def serve_preview(filename):
    return send_from_directory(Config.get_previews_dir(), filename)


if __name__ == '__main__':
    debug_enabled = Config.DEBUG and not is_embedded_runtime()
    print("=" * 50)
    print("Easy Dataset Station - 启动信息")
    print("=" * 50)
    print(f"服务地址: http://{Config.HOST}:{Config.PORT}")
    print("=" * 50)
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=debug_enabled,
        use_reloader=debug_enabled,
    )
