from flask import Flask, request, jsonify
import pymysql
import os
import time

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "192.168.56.30"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "backend_user"),
    "password": os.environ.get("DB_PASSWORD", "1234"),
    "database": os.environ.get("DB_NAME", "backend_data"),
    "connect_timeout": 10,
    "read_timeout": 10,
    "write_timeout": 10,
    "autocommit": True,
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def wait_for_database(max_attempts=20, delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()

            print("Database is ready")
            return

        except Exception as e:
            print(f"Database not ready, attempt {attempt}/{max_attempts}: {e}")

        time.sleep(delay)

    raise RuntimeError("Database did not become ready in time")


@app.route("/")
def home():
    return "Hello from backend VM\n"


@app.route("/health")
def health():
    return "OK\n"


@app.route("/headers")
def headers():
    return jsonify(dict(request.headers))


@app.route("/db-health")
def db_health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0] == 1:
            return "DB OK\n"

        return "DB ERROR\n", 500

    except Exception as e:
        app.logger.error("DB health check failed: %s", e)
        return "DB ERROR\n", 500


@app.route("/visits")
def visits():
    try:
        client_ip = request.headers.get("X-Real-IP", request.remote_addr)
        user_agent = request.headers.get("User-Agent", "")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                client_ip VARCHAR(255),
                user_agent TEXT
            )
        """)

        cur.execute(
            "INSERT INTO visits (client_ip, user_agent) VALUES (%s, %s)",
            (client_ip, user_agent)
        )

        cur.execute("SELECT COUNT(*) FROM visits")
        count = cur.fetchone()[0]

        cur.close()
        conn.close()

        return f"Visit recorded.\nTotal visits: {count}\n"

    except Exception as e:
        app.logger.error("Visit insert failed: %s", e)
        return "DB ERROR\n", 500


if __name__ == "__main__":
    wait_for_database()
    app.run(host="0.0.0.0", port=8080)
