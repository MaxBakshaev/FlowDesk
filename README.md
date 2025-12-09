# FlowDesk

FlowDesk — учебный проект по автоматизации обработки лидов с использованием **FastAPI**, **Telegram-бота**, **n8n** и **Google Sheets**.

Проект демонстрирует, как можно:
- централизованно собирать лиды из разных источников,
- логировать их,
- отправлять уведомления менеджеру,
- строить простую аналитику (еженедельный отчёт).



## Архитектура

Основные компоненты:

- **FastAPI backend**
  - Эндпоинт `/lead` для приёма лидов по API.
  - Веб-форма `/lead-form` для создания лида из браузера.
  - Пересылает лиды в n8n Webhook.

- **Telegram-бот (aiogram)**
  - Команда `/lead`: диалог (имя + email).
  - Отправляет лиды в n8n Webhook (или в backend, в зависимости от конфигурации).

- **n8n workflows**
  1. `FlowDesk – New Lead to Google Sheets`
     - Webhook → Append row in Google Sheets → Telegram notification.
  2. `FlowDesk – Weekly Leads Report`
     - Cron → Read from Google Sheets → Code in Python (Beta) → Telegram report.

- **Google Sheets**
  - Таблица `FlowDesk Leads`:
    - `timestamp`, `name`, `email`, `source`, `client_ip`.


## Потоки данных

### 1. Лид из веб-формы

1. Пользователь открывает `/lead-form` (FastAPI).
2. Заполняет имя и email.
3. FastAPI формирует payload и отправляет в n8n Webhook.
4. n8n:
   - добавляет строку в Google Sheets,
   - отправляет уведомление в Telegram.

### 2. Лид из Telegram-бота

1. Пользователь пишет боту `/lead`.
2. Бот задаёт вопросы (имя, email).
3. Бот отправляет payload в n8n Webhook.
4. n8n:
   - добавляет строку в Google Sheets,
   - отправляет уведомление в Telegram.

### 3. Еженедельный отчёт

1. Cron-нода в n8n раз в неделю запускает workflow.
2. Google Sheets нода читает все лиды.
3. Нода **Code in Python (Beta)**:
   - фильтрует за последние 7 дней,
   - считает общее количество,
   - группирует по источникам (`source`),
   - формирует текст отчёта.
4. Telegram-нода отправляет отчёт в личный чат.


## Технологии

- **Языки:** Python 3.12 (FastAPI, aiogram), Python in n8n (Code node)
- **Backend:** FastAPI, httpx, Jinja2
- **Bot:** aiogram 3
- **Automation:** n8n
- **Storage:** Google Sheets
- **Интеграции:** Telegram Bot API, Google API
- **Прочее:** Docker (для n8n на сервере), python-dotenv


## Локальный запуск backend

```bash
git clone https://github.com/<your-username>/FlowDesk.git
cd FlowDesk

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Скопировать env-файлы
cp backend/fastapi_app/.env.example backend/fastapi_app/.env
# отредактировать N8N_WEBHOOK_URL

# Запуск FastAPI
python -m uvicorn backend.fastapi_app.main:app --reload