"""
Poway Recovery Center API - entry point (same role as Open Coding Society flask main.py)

Run it with:
    python main.py

On start it creates the user management database (instance/volumes/user_management.db),
adds the default users, and serves the API on http://localhost:8587
"""
from flask import jsonify

from __init__ import app, db
from api.user import user_api
from model.user import initUsers


# Register URIs for API endpoints
app.register_blueprint(user_api)


@app.route('/')
def index():
    return jsonify({"service": "Poway Recovery Center API", "status": "ok"})


# Create the database and default users whenever the app starts (python main.py or gunicorn)
initUsers()

if __name__ == "__main__":
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Server running: http://localhost:{app.config['FLASK_PORT']}")
    app.run(debug=True, host="0.0.0.0", port=app.config['FLASK_PORT'], use_reloader=False)
