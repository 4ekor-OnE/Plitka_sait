# -*- coding: utf-8 -*-
import sys
import os

# Добавляем путь до проекта
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Добавляем путь до библиотек (для виртуального окружения)
venv_path = os.path.join(project_dir, 'venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(1, venv_path)
else:
    # Альтернативный путь для локальной установки
    user_home = os.path.expanduser('~')
    local_site_packages = os.path.join(user_home, '.local', 'lib', 'python3.12', 'site-packages')
    if os.path.exists(local_site_packages):
        sys.path.insert(1, local_site_packages)

# Импортируем приложение Flask
from app import app as application

# Опционально: подключение модуля отладки (отключено для продакшена)
# from werkzeug.debug import DebuggedApplication
# application.wsgi_app = DebuggedApplication(application.wsgi_app, True)
# application.debug = False
