# Bandwidth Router Calc Backend

Овчинников Иван ИУ5-52Б

Тема:
- Определение необходимой пропускной способности Wi-Fi роутера. `Услуги` — виды активности устройств в сети (веб, стриминг, обновления и т. д.), `заявка` — расчет требуемой минимальной пропускной способности роутера (Мбит/с) для комфортной работы всех устройств одновременно.

---

## Документация REST API

### Домен сетевых активностей (`/api/network-activities`)

| Метод | Эндпоинт | Описание | Тело запроса / Параметры | Ответ |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/network-activities` | Получение списка опубликованных активностей (опциональная фильтрация по максимальному трафику) | Query: `filter_traffic: int` (опционально) | `200 OK`: `List[NetworkActivityResponse]` (`is_owner` равен 1, если создано текущим пользователем, иначе 0) |
| `GET` | `/api/network-activities/feed` | Получение ленты опубликованных активностей с циклической пагинацией | Query: `activity_id: int` (опционально) | `200 OK`: `{"activity": NetworkActivityResponse, "next_id": int, "next_activity_id": int}` |
| `GET` | `/api/network-activities/draft` | Получение текущего черновика текущего пользователя (максимум 1 запись) | Нет | `200 OK`: `NetworkActivityResponse` или `null` |
| `POST` | `/api/network-activities` | Создание нового черновика с загрузкой медиафайлов через MinIO | Form: `activity_title: str`, Files: `pic: UploadFile`, `video: UploadFile` | `201 Created`: `NetworkActivityResponse` |
| `PUT` | `/api/network-activities/{id}/publish` | Публикация существующего черновика текущего пользователя | JSON: `NetworkActivityPublish` (`description`, `average_traffic_mbps`, `max_latency_ms`) | `200 OK`: `NetworkActivityResponse` (статус меняется на `PUBLISHED`) |
| `DELETE` | `/api/network-activities/{id}` | Мягкое удаление активности текущего пользователя | Нет | `200 OK`: `{"message": "deleted", "id": id}` (статус меняется на `DELETED`) |
| `POST` | `/api/network-activities/{id}/like` | Переключение лайка для активности текущим пользователем | Нет | `200 OK`: `{"status": 1}`, если лайк добавлен; `{"status": 0}`, если лайк удален |

### Домен пользователей (`/api/users`)

| Метод | Эндпоинт | Описание | Тело запроса / Параметры | Ответ |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/users/register` | Регистрация нового пользователя | JSON: `{"username": str, "password": str}` | `201 Created`: `UserResponse` (`id`, `username`) |
| `POST` | `/api/users/auth` | Заглушка аутентификации (входа) | JSON: `{"username": str, "password": str}` | `200 OK`: `{"message": "success", "token": "stub"}` |
| `POST` | `/api/users/logout` | Заглушка выхода из системы | Нет | `200 OK`: `{"message": "logged out"}` |

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

### 3. `likes`
Хранит отметки «нравится» от пользователей к сетевым активностям.
- `id` (`Integer`, PK, index): Уникальный идентификатор лайка.
- `user_id` (`Integer`, FK к `users.id`, not null): Ссылка на пользователя.
- `activity_id` (`Integer`, FK к `network_activities.id`, not null): Ссылка на сетевую активность.
