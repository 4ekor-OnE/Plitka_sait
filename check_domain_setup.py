#!/usr/bin/env python3
"""
Скрипт для проверки готовности проекта к работе с доменом avito.site
"""

import os
import sys

def check_setup():
    print("=" * 60)
    print("Проверка готовности проекта к работе с доменом avito.site")
    print("=" * 60)
    print()
    
    issues = []
    warnings = []
    
    # Проверка структуры каталогов
    print("📁 Проверка структуры каталогов...")
    required_dirs = ['static', 'templates', 'tmp']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - отсутствует")
            issues.append(f"Создайте каталог: mkdir -p {dir_name}")
    
    # Проверка файлов
    print("\n📄 Проверка необходимых файлов...")
    required_files = ['app.py', 'passenger_wsgi.py', '.htaccess', 'requirements.txt']
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} - отсутствует")
            issues.append(f"Файл {file_name} отсутствует")
    
    # Проверка симлинка public
    print("\n🔗 Проверка симлинка public...")
    if os.path.exists('public'):
        if os.path.islink('public'):
            target = os.readlink('public')
            if 'public_html' in target:
                print(f"  ✅ public -> {target}")
            else:
                print(f"  ⚠️  public -> {target} (должен указывать на public_html)")
                warnings.append("Симлинк public должен указывать на public_html")
        else:
            print("  ⚠️  public существует, но это не симлинк")
            warnings.append("Удалите каталог public и создайте симлинк: ln -s public_html public")
    else:
        print("  ❌ public - отсутствует")
        issues.append("Создайте симлинк: ln -s public_html public")
    
    # Проверка tmp/restart.txt
    print("\n🔄 Проверка файла перезапуска...")
    if os.path.exists('tmp/restart.txt'):
        print("  ✅ tmp/restart.txt")
    else:
        print("  ⚠️  tmp/restart.txt - отсутствует (создастся автоматически)")
        if not os.path.exists('tmp'):
            issues.append("Создайте каталог: mkdir -p tmp")
    
    # Проверка .htaccess
    print("\n⚙️  Проверка .htaccess...")
    if os.path.exists('.htaccess'):
        with open('.htaccess', 'r') as f:
            content = f.read()
            if 'PassengerEnabled On' in content:
                print("  ✅ PassengerEnabled On")
            else:
                warnings.append("В .htaccess должна быть директива PassengerEnabled On")
            
            if 'PassengerPython' in content:
                print("  ✅ PassengerPython настроен")
            else:
                warnings.append("В .htaccess должна быть директива PassengerPython")
    else:
        issues.append("Создайте файл .htaccess")
    
    # Проверка passenger_wsgi.py
    print("\n🐍 Проверка passenger_wsgi.py...")
    if os.path.exists('passenger_wsgi.py'):
        with open('passenger_wsgi.py', 'r') as f:
            content = f.read()
            if 'from app import app as application' in content:
                print("  ✅ Правильный импорт application")
            else:
                warnings.append("В passenger_wsgi.py должен быть: from app import app as application")
            
            if 'DISABLE_SOCKETIO' in content:
                print("  ✅ SocketIO отключен для хостинга")
            else:
                warnings.append("Рекомендуется отключить SocketIO для хостинга")
    else:
        issues.append("Файл passenger_wsgi.py отсутствует")
    
    # Проверка зависимостей
    print("\n📦 Проверка зависимостей...")
    if os.path.exists('requirements.txt'):
        print("  ✅ requirements.txt найден")
        print("  💡 Установите зависимости: pip3 install -r requirements.txt --user --ignore-installed")
    else:
        issues.append("Файл requirements.txt отсутствует")
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ПРОВЕРКИ")
    print("=" * 60)
    
    if not issues and not warnings:
        print("\n✅ Все проверки пройдены! Проект готов к работе.")
        print("\n📋 Следующие шаги:")
        print("  1. Добавьте домен avito.site в панели управления Beget")
        print("  2. Установите SSL сертификат через панель управления")
        print("  3. Установите зависимости: pip3 install -r requirements.txt --user --ignore-installed")
        print("  4. Перезапустите: touch tmp/restart.txt")
        print("  5. Откройте https://avito.site в браузере")
        return 0
    else:
        if issues:
            print("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ (требуют исправления):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        if warnings:
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЯ (рекомендуется исправить):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        return 1

if __name__ == '__main__':
    sys.exit(check_setup())
