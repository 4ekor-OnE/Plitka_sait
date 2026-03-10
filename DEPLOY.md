# Инструкция по развертыванию на хостинге Beget

## Шаг 1: Загрузка проекта

1. Загрузите все файлы проекта в каталог вашего сайта через FTP или SSH
2. Рекомендуемый путь: `~/yourdomain.com/` или `~/public_html/`

## Шаг 2: Подключение к Docker окружению

Подключитесь к серверу по SSH:
```bash
ssh username@yourdomain.beget.tech
```

Затем подключитесь к Docker-контейнеру:
```bash
ssh localhost -p222
```

## Шаг 3: Установка зависимостей

Перейдите в каталог проекта:
```bash
cd ~/yourdomain.com
```

### Вариант А: Использование виртуального окружения (рекомендуется)

Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

Активируйте его:
```bash
source venv/bin/activate
```

Установите зависимости:
```bash
pip install -r requirements.txt --ignore-installed
```

### Вариант Б: Локальная установка

Если виртуальное окружение не используется:
```bash
pip3 install -r requirements.txt --user --ignore-installed
```

После установки нужно добавить путь в `passenger_wsgi.py`:
```python
sys.path.append('/home/u/username/.local/lib/python3.X/site-packages')
```

## Шаг 4: Настройка файлов для хостинга

### 4.1. Создание симлинка public

Для корректной отдачи статического контента создайте симлинк:
```bash
ln -s public_html public
```

### 4.2. Настройка .htaccess

Откройте файл `.htaccess` и укажите правильный путь к Python:

**Если используете виртуальное окружение:**
```apache
PassengerEnabled On
PassengerPython /home/u/username/yourdomain.com/venv/bin/python3
```

**Если используете системный Python:**
```apache
PassengerEnabled On
PassengerPython /usr/bin/python3
```

**Если используете локально собранный Python:**
```apache
PassengerEnabled On
PassengerPython /home/u/username/.local/bin/python3
```

### 4.3. Настройка passenger_wsgi.py

Откройте `passenger_wsgi.py` и при необходимости измените пути:

1. Если используете виртуальное окружение - пути должны автоматически определиться
2. Если используете локальную установку - раскомментируйте и укажите путь:
```python
user_home = os.path.expanduser('~')
local_site_packages = os.path.join(user_home, '.local', 'lib', 'python3.X', 'site-packages')
sys.path.insert(1, local_site_packages)
```

### 4.4. Создание каталога tmp

Каталог `tmp` уже создан в проекте. Если его нет:
```bash
mkdir tmp
touch tmp/restart.txt
```

## Шаг 5: Настройка прав доступа

Для работы приложения необходимо настроить права доступа через Файловый менеджер в панели управления Beget:

1. Войдите в панель управления
2. Откройте Файловый менеджер
3. Настройте общий доступ к каталогам `.local` (если используется локальная установка)

## Шаг 6: Настройка базы данных

База данных SQLite будет создана автоматически при первом запуске в каталоге `instance/`.

Если нужно использовать другую БД, измените настройки в `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///avita.db'
```

## Шаг 7: Перезапуск приложения

После всех изменений перезапустите приложение:
```bash
touch tmp/restart.txt
```

Или через панель управления Beget в разделе "Управление сайтами".

## Шаг 8: Проверка работы

Откройте ваш сайт в браузере. Должна открыться главная страница AVITA.

### Администратор по умолчанию:
- **Email**: admin@avita.ru
- **Пароль**: admin123

## Решение проблем

### Ошибка "No module named 'flask'"
- Проверьте путь к Python в `.htaccess`
- Убедитесь, что зависимости установлены в правильное окружение
- Проверьте пути в `passenger_wsgi.py`

### Ошибка "Permission denied"
- Настройте права доступа через Файловый менеджер
- Проверьте права на каталоги: `chmod 755` для каталогов, `chmod 644` для файлов

### Статические файлы не загружаются
- Убедитесь, что создан симлинк `public -> public_html`
- Проверьте настройки Nginx в панели управления

### База данных не создается
- Проверьте права на запись в каталог `instance/`
- Убедитесь, что каталог существует: `mkdir -p instance`

## Дополнительные настройки

### Изменение SECRET_KEY

Для безопасности измените `SECRET_KEY` в `app.py`:
```python
app.config['SECRET_KEY'] = 'ваш-случайный-секретный-ключ'
```

### Настройка домена

В `app.py` можно добавить проверку домена (опционально):
```python
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

## Поддержка

При возникновении проблем обращайтесь в поддержку Beget через тикет из панели управления.
