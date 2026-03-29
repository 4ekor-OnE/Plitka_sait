# Размещение на хостинге (для поддержки и владельца сайта)

## Кратко для специалиста поддержки

1. Корень сайта — каталог с `app.py`, `passenger_wsgi.py`, `passenger_wsgi` экспортирует WSGI-объект **`application`** (Flask `app`).
2. Создать **`venv`**: `python3.11 -m venv venv` → `./venv/bin/pip install -r requirements.txt`.
3. В **`.htaccess`**: `PassengerEnabled On` и **`PassengerPython`** = абсолютный путь к **`venv/bin/python3`** (шаблон — `.htaccess.example`).
4. Каталоги веб-процесса должны иметь **право прохода и чтения** до этого пути; **`venv`** и **`venv/bin`** — **755**.
5. Перезапуск: **`touch tmp/restart.txt`**. БД SQLite: **`instance/avita.db`** (создаётся сама). SocketIO на хостинге отключён (`DISABLE_SOCKETIO` в `passenger_wsgi.py`).

---

Приложение: **Flask 3**, **Python 3.10+** (рекомендуется **3.11**). WSGI через **Phusion Passenger** (типично для shared-хостинга).

## Структура каталога на сервере

Корень сайта (document root = каталог с приложением):

- `app.py` — приложение Flask, объект `app`
- `passenger_wsgi.py` — точка входа WSGI, экспортирует `application` (это `app`)
- `.htaccess` — включение Passenger и путь к интерпретатору (см. ниже)
- `requirements.txt` — зависимости
- `venv/` — виртуальное окружение (создаётся на сервере, **не** заливается с ПК)
- `templates/`, `static/` — шаблоны и статика
- `static/uploads/` — загрузки пользователей (через FTP/SFTP можно докладывать резервные копии)
- `instance/` — SQLite `avita.db` и при необходимости `app_errors.log` (создаётся приложением)
- `tmp/restart.txt` — обновить время файла для перезапуска Passenger: `touch tmp/restart.txt`

## Запуск для специалиста поддержки

1. **Интерпретатор**  
   Создать venv от Python **3.10+** в корне сайта:
   ```bash
   cd /путь/к/сайту
   python3.11 -m venv venv
   ./venv/bin/python -m pip install --upgrade pip
   ./venv/bin/pip install -r requirements.txt
   ```

2. **Права**  
   Каталоги **755**, файлы **644**; каталог **`venv/bin`** — выполнение для процесса веб-сервера (часто нужны **755** на `venv`, `venv/bin`).  
   Процесс Passenger должен иметь право **читать** весь код и **выполнять** `venv/bin/python3`.

3. **`.htaccess`** (скопировать из `.htaccess.example`, подставить пути):
   ```apache
   PassengerEnabled On
   PassengerPython /полный/путь/к/сайту/venv/bin/python3
   ```
   Опционально, если БД и логи должны лежать не в `instance/`, а в `tmp/`:
   ```apache
   SetEnv AVITA_DATA_DIR /полный/путь/к/сайту/tmp
   ```

4. **Перезапуск**
   ```bash
   touch /полный/путь/к/сайту/tmp/restart.txt
   ```

5. **Проверка**
   ```bash
   ./venv/bin/python -c "import app; print(app.app.config['SQLALCHEMY_DATABASE_URI'])"
   ```

**Важно:** в `passenger_wsgi.py` выставляется `DISABLE_SOCKETIO=1` (чат в реальном времени через WebSocket на типичном shared-хостинге не используется).

## FTP / SFTP для статики и загрузок

- Подключение: данные FTP/SFTP из панели хостинга (хост, логин, пароль, порт).
- Каталог на сервере: **корень сайта** (тот же, где `app.py`).
- **Статические ресурсы сайта:** `static/css/`, `static/js/`, `static/images/` — можно обновлять по FTP.
- **Загрузки пользователей:** `static/uploads/` — приложение пишет сюда файлы; через FTP можно просматривать, бэкапить, при необходимости восстанавливать.  
  После заливки с локального ПК выставить права, чтобы веб-сервер мог писать:
  ```bash
  chmod 755 static/uploads
  ```

Не выкладывать по FTP: `venv/`, `instance/*.db` (если не намеренный бэкап), секреты `.env`.

## Выгрузка сайта с компьютера разработчика (rsync)

Замените `USER`, `HOST`, `/путь/к/Plitka_sait` и удалённый каталог сайта.

```bash
cd /путь/к/Plitka_sait

rsync -avz --progress \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '*.py[cod]' \
  --exclude '.git/' \
  --exclude 'instance/' \
  --exclude '*.db' \
  --exclude '.env' \
  --exclude '.htaccess' \
  ./ USER@HOST:~/сайт/
```

Файл **`.htaccess`** в репозитории не хранится (локальные пути); после первой выгрузки на сервере выполните: `cp .htaccess.example .htaccess` и отредактируйте `PassengerPython`.

После выгрузки на сервере (SSH):

```bash
cd ~/сайт
mkdir -p tmp instance static/uploads
touch tmp/restart.txt
python3.11 -m venv venv
./venv/bin/pip install -r requirements.txt
cp -n .htaccess.example .htaccess
# отредактировать .htaccess
touch tmp/restart.txt
```

## Локальный запуск (без Passenger)

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Браузер: `http://localhost:5000`
