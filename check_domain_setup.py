#!/usr/bin/env python3
"""Проверка структуры проекта перед выкладкой на хостинг."""

import os
import sys


def check_setup():
    print("Проверка структуры проекта")
    print("=" * 50)

    issues = []
    warnings = []

    for dir_name in ("static", "templates", "tmp"):
        if os.path.isdir(dir_name):
            print("OK  %s/" % dir_name)
        else:
            print("FAIL %s/ — нет каталога" % dir_name)
            issues.append("mkdir -p %s" % dir_name)

    if not os.path.isdir("static/uploads"):
        warnings.append("mkdir -p static/uploads (загрузки пользователей)")

    for file_name in ("app.py", "passenger_wsgi.py", "requirements.txt"):
        if os.path.isfile(file_name):
            print("OK  %s" % file_name)
        else:
            print("FAIL %s" % file_name)
            issues.append("Отсутствует файл %s" % file_name)

    if os.path.isfile(".htaccess"):
        print("OK  .htaccess (локальная конфигурация Passenger)")
    elif os.path.isfile(".htaccess.example"):
        print("OK  .htaccess.example (на сервере: cp .htaccess.example .htaccess)")
        warnings.append("На сервере создайте .htaccess из .htaccess.example")
    else:
        issues.append("Нет .htaccess.example")

    if os.path.isfile("tmp/restart.txt"):
        print("OK  tmp/restart.txt")
    else:
        warnings.append("touch tmp/restart.txt для перезапуска Passenger")

    if os.path.isfile("passenger_wsgi.py"):
        with open("passenger_wsgi.py", "r", encoding="utf-8") as f:
            body = f.read()
        if "from app import app as application" not in body:
            warnings.append("В passenger_wsgi.py должен быть импорт: from app import app as application")

    print("=" * 50)
    if issues:
        print("Критично:")
        for i, msg in enumerate(issues, 1):
            print("  %d. %s" % (i, msg))
    if warnings:
        print("Рекомендации:")
        for i, msg in enumerate(warnings, 1):
            print("  %d. %s" % (i, msg))
    if not issues and not warnings:
        print("Все основные проверки пройдены.")
        print("Дальше: см. HOSTING.md (venv, pip, Passenger, rsync).")
        return 0
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(check_setup())
