# telegram-verification

Phone number verification for a Django REST API using the **Telegram Gateway API**. Verification codes are delivered to the user's Telegram account through the official **Verification Codes** chat instead of SMS.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [API Documentation](#api-documentation)
- [Data Model](#data-model)
- [Notes](#notes)
- [License](#license)

## Features

- Registration with a phone number and password
- Verification code (6 digits) delivered via Telegram's **Verification Codes** chat
- Code validity window of 5 minutes (300 seconds)
- Only one active verification request per user (enforced by a database constraint)
- Login allowed only for users with a verified phone number
- Custom user model that uses the phone number as the username
- Interactive API documentation (Swagger UI and ReDoc) generated with drf-spectacular

## Tech Stack

- Python
- Django 6.1
- Django REST Framework
- drf-spectacular (OpenAPI 3 schema, Swagger UI, ReDoc)
- django-environ
- requests
- SQLite3 (default database)

## How It Works

```
Client                    API                         Telegram Gateway
  |  POST /register/       |                                 |
  |----------------------->|  sendVerificationMessage        |
  |                        |-------------------------------->|
  |  201 + request_id      |                                 |
  |<-----------------------|     code -> "Verification Codes" chat
  |                        |                                 |
  |  POST /verify/         |                                 |
  |  request_id + code     |  checkVerificationStatus        |
  |----------------------->|-------------------------------->|
  |  200 verified          |                                 |
  |<-----------------------|                                 |
  |                        |                                 |
  |  POST /login/          |                                 |
  |----------------------->|  (session login)                |
  |  200 login successful  |                                 |
  |<-----------------------|                                 |
```

1. **Register**: the user is created with `phone_number_verified = False`. The API asks Telegram Gateway to send a 6-digit code and stores the returned `request_id` together with an expiration time.
2. **Verify**: the client sends the `request_id` and the code. The API checks that the request is active and not expired, validates the code with Telegram Gateway, and marks the user's phone number as verified.
3. **Login**: the user authenticates with phone number and password. Unverified users are rejected. On success a Django session is created.

## Project Structure

```
telegram-verification/
├── config/                     # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── user/                       # Authentication and verification app
│   ├── migrations/
│   ├── services/
│   │   └── telegram_gateway.py # Telegram Gateway API client
│   ├── admin.py
│   ├── models.py               # User, PhoneNumberVerification
│   ├── serializers.py          # Register, Verify, Login serializers
│   ├── urls.py
│   └── views.py
├── .env.example
├── LICENSE
├── manage.py
├── README.md
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.12 or newer (the project was developed with Python 3.14)
- A Telegram Gateway API token (see [Environment Variables](#environment-variables))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/turdialixasanbayev/telegram-verification.git
cd telegram-verification

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the environment file
cp .env.example .env
# then open .env and fill in the values

# 5. Apply migrations
python manage.py migrate

# 6. (Optional) Create an admin user
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`.

## Environment Variables

Configuration is read from a `.env` file in the project root (see `.env.example`).

| Variable                 | Description                                                   |
| ------------------------ | ------------------------------------------------------------- |
| `SECRET_KEY`             | Django secret key                                             |
| `TELEGRAM_GATEWAY_TOKEN` | API token issued by Telegram Gateway (https://gateway.telegram.org) |

Never commit the `.env` file. It is already listed in `.gitignore`.

## API Reference

Base path: `/api/v1/auth/`

### `POST /api/v1/auth/register/`

Creates a user and sends a verification code to the phone number via Telegram.

Request body:

```json
{
  "phone_number": "+998901234567",
  "password": "strong-password"
}
```

- `password` must be at least 8 characters long.

Response `201 Created`:

```json
{
  "message": "Verification code sent.",
  "request_id": "<request_id>",
  "redirect_url": "/api/v1/auth/verify/"
}
```

### `POST /api/v1/auth/verify/`

Confirms the phone number with the code received in the **Verification Codes** chat.

Request body:

```json
{
  "request_id": "<request_id>",
  "code": "123456"
}
```

- `code` must be exactly 6 characters.

Response `200 OK`:

```json
{
  "message": "Phone number verified successfully.",
  "redirect_url": "/api/v1/auth/login/"
}
```

Validation errors (`400 Bad Request`):

- `Invalid or inactive verification request.`
- `Verification request has expired.`
- `Invalid verification code.`

### `POST /api/v1/auth/login/`

Authenticates a user with a verified phone number and starts a session.

Request body:

```json
{
  "phone_number": "+998901234567",
  "password": "strong-password"
}
```

Response `200 OK`:

```json
{
  "message": "Login successful."
}
```

Validation errors (`400 Bad Request`):

- `Invalid phone number or password.`
- `Phone number is not verified.`

### Example (cURL)

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+998901234567", "password": "strong-password"}'

# Verify
curl -X POST http://127.0.0.1:8000/api/v1/auth/verify/ \
  -H "Content-Type: application/json" \
  -d '{"request_id": "<request_id>", "code": "123456"}'

# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+998901234567", "password": "strong-password"}'
```

## API Documentation

Interactive documentation is generated automatically:

| URL                    | Description          |
| ---------------------- | -------------------- |
| `/api/v1/docs/`        | Swagger UI           |
| `/api/v1/redoc/`       | ReDoc                |
| `/api/v1/schema/`      | Raw OpenAPI schema   |

The Django admin panel is available at `/admin/`.

## Data Model

**User** (custom user model, `AUTH_USER_MODEL = 'user.User'`)

| Field                   | Type              | Notes                          |
| ----------------------- | ----------------- | ------------------------------ |
| `phone_number`          | `CharField(20)`   | Unique, used as the username   |
| `phone_number_verified` | `BooleanField`    | Defaults to `False`            |
| `is_active`             | `BooleanField`    | Defaults to `True`             |
| `is_staff`              | `BooleanField`    | Defaults to `False`            |

**PhoneNumberVerification**

| Field        | Type                | Notes                                              |
| ------------ | ------------------- | -------------------------------------------------- |
| `user`       | `ForeignKey(User)`  | Related name: `phone_number_verifications`         |
| `request_id` | `CharField(255)`    | Unique, returned by Telegram Gateway               |
| `created_at` | `DateTimeField`     | Set automatically                                  |
| `expires_at` | `DateTimeField`     | 5 minutes after creation                           |
| `is_active`  | `BooleanField`      | Only one active record per user (unique constraint) |

## Notes

- The default configuration is intended for local development: `DEBUG = True` and `ALLOWED_HOSTS = ['*']` are set in `config/settings.py`. Adjust these (and use a production database, HTTPS, and a strong `SECRET_KEY`) before deploying.
- The user must have a Telegram account registered with the phone number that receives the code.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
