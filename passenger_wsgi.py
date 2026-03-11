# -*- coding: utf-8 -*-
import sys
import os

# Отключаем SocketIO для хостинга (WebSocket не работает через Passenger)
os.environ['DISABLE_SOCKETIO'] = '1'

# Определяем путь до проекта (корневой каталог сайта)
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)  # указываем директорию с проектом

# Определяем версию Python
import platform
python_version = platform.python_version_tuple()
python_version_str = f"{python_version[0]}.{python_version[1]}"

# Добавляем путь до библиотек
# Сначала проверяем виртуальное окружение
venv_path = os.path.join(project_dir, 'venv', 'lib', f'python{python_version_str}', 'site-packages')
if os.path.exists(venv_path):
    sys.path.append(venv_path)  # путь до библиотек в venv
else:
    # Альтернативный путь для локальной установки (--user)
    user_home = os.path.expanduser('~')
    local_site_packages = os.path.join(user_home, '.local', 'lib', f'python{python_version_str}', 'site-packages')
    if os.path.exists(local_site_packages):
        sys.path.append(local_site_packages)  # путь до библиотек, куда поставили Flask

# Импортируем приложение Flask
# когда Flask стартует, он ищет application. Если не указать 'as application', сайт не заработает
from app import app as application

# Инициализация базы данных при первом запуске
with application.app_context():
    from app import db, init_categories, create_admin
    try:
        db.create_all()
        init_categories()
        create_admin()
    except Exception as e:
        # Если БД уже создана, игнорируем ошибку
        pass

# Опционально: подключение модуля отладки (отключено для продакшена)
# from werkzeug.debug import DebuggedApplication
# application.wsgi_app = DebuggedApplication(application.wsgi_app, True)  # Опционально: включение модуля отладки
# application.debug = False  # Опционально: True/False устанавливается по необходимости в отладке
