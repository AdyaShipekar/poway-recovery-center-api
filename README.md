# Poway Recovery Center API

Flask backend for user accounts on the [Poway Recovery Center site](https://github.com/AdyaShipekar/poway-recovery-center). This is the same split as the Open Coding Society [pages](https://github.com/Open-Coding-Society/pages) (frontend) and [flask](https://github.com/Open-Coding-Society/flask) (backend) repos.

## Run locally
```bash
make            # creates .venv, installs requirements, starts the API on http://localhost:8587
make stop       # stops it
```
Then run `make` in the poway-recovery-center repo and visit `http://localhost:4000`.

To run it by hand:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py      # creates instance/volumes/user_management.db and starts the API
```

## Structure
- `main.py`: entry point; registers the API, creates the database and default users, runs the server
- `__init__.py`: Flask `app`, CORS (allowed frontend origins), settings, and `db`
- `model/user.py`: `User` model and `initUsers()` default users
- `api/jwt_authorize.py`: `@token_required` JWT cookie guard
- `api/user.py`: REST API for sign up, log in/out, profile, admin user list
- `.env`: secret key and passwords (not committed)
- `instance/volumes/user_management.db`: SQLite database (created on first run, not committed)
- `Dockerfile`, `docker-compose.yml`: production server (gunicorn on port 8587)

### Accounts
`initUsers()` creates these users when the API starts (the list is `MEMBERS` in `__init__.py`). Existing users keep their password and profile; only their role is updated to match the list.

| Name | Username | Role |
| --- | --- | --- |
| Adya Shipekar | `adyashipekar` (or adya.shipekar1@gmail.com) | Admin |
| Anika Seksaria | `anikaseksaria` | Admin |
| Jailene Tang | `jailenetang` | Admin |
| Joan Kim | `joankim` | User |
| Ainsley Albert | `ainsleyalbert` | User |
| Samanvi Yachareni | `samanviyachareni` | User |

Starting passwords come from `.env`: `ADMIN_PASSWORD` for the site admin and `<FIRSTNAME>_PASSWORD` for each member (e.g. `JOAN_PASSWORD`). Anyone can change their password, email, and phone number from their profile page.

## API
| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/authenticate` | Log in `{uid, password}` (uid can be the username or email); sets an httpOnly JWT cookie |
| DELETE | `/api/authenticate` | Log out |
| GET | `/api/id` | Current user's profile |
| POST | `/api/user` | Sign up `{name, uid, email?, phone?, password}` and log in |
| PUT | `/api/user` | Update `{name, email, phone}` and/or `{current_password, new_password}` |
| GET | `/api/user` | Admin only: list every user |
| DELETE | `/api/user` | Admin only: delete a user `{uid}` |

## Deploying
Deploy it like Open Coding Society flask, on a server with Docker:
```bash
git clone https://github.com/AdyaShipekar/poway-recovery-center-api.git
cd poway-recovery-center-api
cp /path/to/your/.env .env     # SECRET_KEY, ADMIN_PASSWORD, member passwords, IS_PRODUCTION=true
docker compose up -d --build   # serves the API on port 8587; database is kept in instance/
```
Put it behind HTTPS (e.g. nginx + certbot, as in OCS `nginx_flask_8587.conf`). `IS_PRODUCTION=true` is required there: the frontend is on a different domain (github.io), so the login cookie must be `SameSite=None; Secure`.

Then set that https address as `deployedPythonURI` in the frontend's `js/api/config.js`. `https://adyashipekar.github.io` is already an allowed CORS origin. Add any other frontend address to `ALLOWED_ORIGINS` in `.env`.
