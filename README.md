# Bandwidth Router Calc Backend

Овчинников Иван ИУ5-52Б

Тема:
- Определение необходимой пропускной способности Wi-Fi роутера. `Услуги` - виды активности устройств в сети (веб, стриминг, обновления и тд), `заявка` - расчет требуемой минимальной пропускной способности роутера (Мбит/с) для комфортной работы всех устройств одновременно.

---

## REST API Documentation

### Network Activities Domain (`/api/network-activities`)

| Method | Endpoint | Description | Request Body / Params | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/network-activities` | Get published activities list (optional filter by max traffic) | Query: `filter_traffic: int` (optional) | `200 OK`: `List[NetworkActivityResponse]` (`is_owner` set to 1 if created by current user, else 0) |
| `GET` | `/api/network-activities/feed` | Get video/reels feed of published activities with pagination wrap-around | Query: `activity_id: int` (optional) | `200 OK`: `{"activity": NetworkActivityResponse, "next_id": int, "next_activity_id": int}` |
| `GET` | `/api/network-activities/draft` | Get the current draft for the current user (max 1 record) | None | `200 OK`: `NetworkActivityResponse` or `null` |
| `POST` | `/api/network-activities` | Create a new draft with uploaded media files via MinIO | Form: `activity_title: str`, Files: `pic: UploadFile`, `video: UploadFile` | `201 Created`: `NetworkActivityResponse` |
| `PUT` | `/api/network-activities/{id}/publish` | Publish an existing draft activity owned by current user | JSON: `NetworkActivityPublish` (`description`, `average_traffic_mbps`, `max_latency_ms`) | `200 OK`: `NetworkActivityResponse` (status set to `PUBLISHED`) |
| `DELETE` | `/api/network-activities/{id}` | Soft-delete an activity owned by current user | None | `200 OK`: `{"message": "deleted", "id": id}` (status set to `DELETED`) |
| `POST` | `/api/network-activities/{id}/like` | Toggle like for activity by current user | None | `200 OK`: `{"status": 1}` if like added, `{"status": 0}` if like removed |

### Users Domain (`/api/users`)

| Method | Endpoint | Description | Request Body / Params | Response |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/users/register` | Register a new user | JSON: `{"username": str, "password": str}` | `201 Created`: `UserResponse` (`id`, `username`) |
| `POST` | `/api/users/auth` | User login stub | JSON: `{"username": str, "password": str}` | `200 OK`: `{"message": "success", "token": "stub"}` |
| `POST` | `/api/users/logout` | User logout stub | None | `200 OK`: `{"message": "logged out"}` |

---

## Database Schema & Tables

### 1. `network_activities`
Represents network activity profiles and their requirements.
- `id` (`Integer`, PK, index): Unique identifier.
- `activity_title` (`String(100)`, not null): Activity name/title.
- `activity_description` (`String(500)`, nullable): Detailed description of the network activity.
- `average_traffic_mbps` (`Integer`, nullable): Average traffic bandwidth consumed in Mbps.
- `max_latency_ms` (`Integer`, nullable): Maximum tolerable network latency in ms.
- `preview_image_url` (`String(255)`, not null): Absolute URL to preview image stored in MinIO.
- `preview_video_url` (`String(255)`, not null): Absolute URL to preview video stored in MinIO.
- `status` (`Enum: ActivityStatus`, not null): Status of the activity (`DRAFT`, `PUBLISHED`, `DELETED`).
- `creator_id` (`Integer`, FK to `users.id`, nullable): Reference to user who created the activity.
- `created_at` (`DateTime(timezone=True)`): Timestamp when record was created.
- `updated_at` (`DateTime(timezone=True)`): Timestamp when record was last updated.

### 2. `users`
Represents registered users in the application.
- `id` (`Integer`, PK, index): Unique user identifier.
- `username` (`String(50)`, unique, not null): Unique username.

### 3. `likes`
Represents likes placed by users on network activities.
- `id` (`Integer`, PK, index): Unique like identifier.
- `user_id` (`Integer`, FK to `users.id`, not null): Reference to user.
- `activity_id` (`Integer`, FK to `network_activities.id`, not null): Reference to network activity.
