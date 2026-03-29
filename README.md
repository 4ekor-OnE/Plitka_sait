# AVITA — площадка объявлений

Маркетплейс для объявлений (в духе Avito): пользователи, категории, объявления, чат, вакансии, админка.

## Требования

- **Python 3.10+** (рекомендуется 3.11)
- pip

## Установка и локальный запуск

```bash
git clone https://github.com/4ekor-OnE/Plitka_sait.git
cd Plitka_sait
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Откройте в браузере: `http://localhost:5000`

## Хостинг и выгрузка на сервер

Краткая инструкция для поддержки хостинга, FTP/SFTP к статике и загрузкам, команды **rsync** и настройка **Passenger** — в файле **[HOSTING.md](HOSTING.md)**.

Перед выкладкой скопируйте `.htaccess.example` в `.htaccess` на сервере и укажите путь к `venv/bin/python3`.

Проверка структуры проекта (опционально):

```bash
python3 check_domain_setup.py
```

## Администратор по умолчанию

- Email: `admin@avita.ru`
- Пароль: `admin123`

Смените пароль после первого входа.

## Структура проекта

```
Plitka_sait/
├── app.py
├── passenger_wsgi.py
├── requirements.txt
├── .htaccess.example
├── static/
│   ├── css/  js/  images/
│   └── uploads/     # пользовательские файлы
├── templates/
└── instance/        # SQLite (создаётся при работе приложения)
```

## Лицензия

Проект в демонстрационных целях.

## Автор

4ekor-OnE
