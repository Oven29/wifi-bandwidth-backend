# Bandwidth Router Calc Backend

Овчинников Иван ИУ5-52Б

**Тема:**
Определение необходимой пропускной способности Wi-Fi роутера. `Услуги` — виды активности устройств в сети (веб, стриминг, обновления и т. д.), `заявка` — расчет требуемой минимальной пропускной способности роутера (Мбит/с) для комфортной работы всех устройств одновременно.

---

## Инструкция по запуску

### 1. Предварительные требования
Для локального запуска бэкенда необходимы:
- **Python 3.10+**
- **Docker** и **Docker Compose**
- **Git**

---

### 2. Клонирование и переход в репозиторий
```bash
git clone git@github.com:Oven29/wifi-bandwidth-backend.git
cd wifi-bandwidth-backend
```

---

### 3. Настройка переменных окружения
Скопируйте пример файла конфигурации `.env.example` в `.env`:
```bash
cp .env.example .env
```

Параметры окружения по умолчанию:
```ini
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=qwerty
DB_NAME=wifi_bandwidth

# MinIO (S3 Object Storage)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=root
MINIO_SECRET_KEY=Dina@0606
MINIO_BUCKET_NAME=media

# Redis (Сессии и кэш)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

---

### 4. Запуск инфраструктуры (Docker Compose)
В проекте настроен `docker-compose.yml`, разворачивающий базу данных PostgreSQL, хранилище MinIO, кэш Redis и веб-интерфейс Adminer:

```bash
docker compose up -d
```

Доступные сервисы:
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **MinIO API**: `http://localhost:9000`
- **MinIO Web Console**: `http://localhost:9001` (логин: `root`, пароль: `Dina@0606`)
- **Adminer (UI для БД)**: `http://localhost:8081`

> **Примечание по MinIO:** При первом запуске перейдите в веб-консоль MinIO (`http://localhost:9001`) и создайте бакет с именем `media`, либо настройте ему публичный доступ на чтение, если требуется прямое скачивание превью.

---

### 5. Виртуальное окружение и установка зависимостей
Создайте и активируйте виртуальное окружение Python:

**Windows (PowerShell / cmd):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Установите необходимые зависимости:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 6. Применение миграций базы данных
Примените миграции Alembic для создания таблиц:
```bash
alembic upgrade head
```

---

### 7. Запуск приложения FastAPI
Запустите сервер с автоперезагрузкой (hot reload):
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: `http://localhost:8000`

---

### 8. Проверка и тестирование API
- **Интерактивная документация Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Альтернативная документация ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **HTML-интерфейс (шаблоны Jinja2)**: [http://localhost:8000/network-activities/feed](http://localhost:8000/network-activities/feed)

---

## Документация REST API

### Домен сетевых активностей (`/api/network-activities`)

| Метод | Эндпоинт | Описание | Тело запроса / Параметры | Ответ |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/network-activities` | Получение списка опубликованных активностей (опциональная фильтрация по максимальному трафику) | Query: `filter_traffic: int` (опционально) | `200 OK`: `List[NetworkActivityResponse]` (`is_owner` равен 1, если создано текущим пользователем, иначе 0) |
| `GET` | `/api/network-activities/feed` | Получение ленты опубликованных активностей с циклической пагинацией | Query: `activity_id: int` (опционально) | `200 OK`: `{"activity": NetworkActivityResponse, "next_id": int, "next_activity_id": int}` (`is_owner` и `is_liked` равны 1 или 0) |
| `GET` | `/api/network-activities/draft` | Получение текущего черновика текущего пользователя (максимум 1 запись) | Нет | `200 OK`: `NetworkActivityResponse` или `null` |
| `POST` | `/api/network-activities` | Создание нового черновика с загрузкой медиафайлов через MinIO | Form: `activity_title: str`, Files: `pic: UploadFile`, `video: UploadFile` | `201 Created`: `NetworkActivityResponse` |
| `PUT` | `/api/network-activities/{id}/publish` | Публикация существующего черновика текущего пользователя | JSON: `NetworkActivityPublish` (`description`, `average_traffic_mbps`, `max_latency_ms`) | `200 OK`: `NetworkActivityResponse` (статус меняется на `PUBLISHED`) |
| `DELETE` | `/api/network-activities/{id}` | Мягкое удаление активности текущего пользователя | Нет | `200 OK`: `{"message": "deleted", "id": id}` (статус меняется на `DELETED`) |
| `POST` | `/api/network-activities/{id}/like` | Переключение лайка для активности текущим пользователем | Нет | `200 OK`: `{"status": 1}`, если лайк добавлен; `{"status": 0}`, если лайк удален |

### Домен пользователей (`/api/users`)

| Метод | Эндпоинт | Описание | Тело запроса / Параметры | Ответ |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/users/register` | Регистрация нового пользователя с хешированием пароля | JSON: `{"username": str, "password": str}` | `201 Created`: `UserResponse` (`id`, `username`) |
| `POST` | `/api/users/auth` | Аутентификация пользователя (проверка пароля, создание сессии в Redis, установка `session_id` в HttpOnly Cookie) | Form: `OAuth2PasswordRequestForm` (`username`, `password`) | `200 OK`: `{"message": "success", "session_id": str}` + Cookie `session_id` |
| `POST` | `/api/users/logout` | Выход из системы (удаление сессии из Redis и очистка Cookie) | Cookie: `session_id` | `200 OK`: `{"message": "logged out"}` |

---

## Архитектура приложения

Проект разделен на следующие слои:
- **`src/api/`** — Слой контроллеров/обработчиков (FastAPI routers). Отвечает исключительно за валидацию входящих запросов, внедрение зависимостей (DI) и формирование HTTP-ответов / куки.
- **`src/services/`** — Слой бизнес-логики (`UserService`, `ActivityService`). Инкапсулирует сценарии предметной области, правила валидации, взаимодействие с базой данных, MinIO и сессиями в Redis.
- **`src/models/`** — ORM-модели SQLAlchemy (`User`, `NetworkActivity`, `Like`).
- **`src/schemas/`** — Pydantic-схемы валидации и сериализации данных.
- **`src/core/`** — Настройки конфигурации (`config.py`), клиенты хранилищ (`redis_client.py`, `minio_client.py`), безопасность и хеширование паролей (`security.py`).
- **`src/db/`** — Подключение к базе данных и управление сессиями SQLAlchemy (`session.py`).

---

## Схема базы данных и таблицы

### 1. `network_activities`
Хранит профили сетевых активностей и их характеристики.
- `id` (`Integer`, PK, index): Уникальный идентификатор активности.
- `activity_title` (`String(100)`, not null): Название активности.
- `activity_description` (`String(500)`, nullable): Подробное описание сетевой активности.
- `average_traffic_mbps` (`Integer`, nullable): Средний потребляемый трафик в Мбит/с.
- `max_latency_ms` (`Integer`, nullable): Максимально допустимая задержка сети в мс.
- `preview_image_url` (`String(255)`, not null): Абсолютный URL изображения предпросмотра, хранящегося в MinIO.
- `preview_video_url` (`String(255)`, not null): Абсолютный URL видео предпросмотра, хранящегося в MinIO.
- `status` (`Enum: ActivityStatus`, not null): Статус активности (`DRAFT`, `PUBLISHED`, `DELETED`).
- `creator_id` (`Integer`, FK к `users.id`, nullable): Ссылка на пользователя, создавшего активность.
- `created_at` (`DateTime(timezone=True)`): Время создания записи.
- `updated_at` (`DateTime(timezone=True)`): Время последнего обновления записи.

### 2. `users`
Хранит данные зарегистрированных пользователей приложения.
- `id` (`Integer`, PK, index): Уникальный идентификатор пользователя.
- `username` (`String(50)`, unique, not null): Уникальное имя пользователя.
- `password` (`String(255)`, nullable): Хеш пароля пользователя (bcrypt).

### 3. `likes`
Хранит отметки «нравится» от пользователей к сетевым активностям.
- `id` (`Integer`, PK, index): Уникальный идентификатор лайка.
- `user_id` (`Integer`, FK к `users.id`, not null): Ссылка на пользователя.
- `activity_id` (`Integer`, FK к `network_activities.id`, not null): Ссылка на сетевую активность.
