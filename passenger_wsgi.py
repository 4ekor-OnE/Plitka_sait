# -*- coding: utf-8 -*-
import sys
import os

# Отключаем SocketIO для хостинга (WebSocket не работает через Passenger)
os.environ['DISABLE_SOCKETIO'] = '1'

# Добавляем путь до проекта
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Определяем версию Python
import platform
python_version = platform.python_version_tuple()
python_version_str = f"{python_version[0]}.{python_version[1]}"

# Добавляем путь до библиотек (для виртуального окружения)
venv_path = os.path.join(project_dir, 'venv', 'lib', f'python{python_version_str}', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(1, venv_path)
else:
    # Альтернативный путь для локальной установки
    user_home = os.path.expanduser('~')
    local_site_packages = os.path.join(user_home, '.local', 'lib', f'python{python_version_str}', 'site-packages')
    if os.path.exists(local_site_packages):
        sys.path.insert(1, local_site_packages)

# Импортируем приложение Flask
from app import app

# Инициализация базы данных при первом запуске
with app.app_context():
    from app import db, init_categories, create_admin
    try:
        db.create_all()
        init_categories()
        create_admin()
    except Exception as e:
        # Если БД уже создана, игнорируем ошибку
        pass

# WSGI application
application = app

# Опционально: подключение модуля отладки (отключено для продакшена)
# from werkzeug.debug import DebuggedApplication
# application.wsgi_app = DebuggedApplication(application.wsgi_app, True)
# application.debug = False
