import aiosqlite
import math

DB_NAME = "smart_nazorat.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Xodimlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                department TEXT,
                rate REAL DEFAULT 0,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        # Keldi-ketdi va geolokatsiya jurnali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                action TEXT,
                lat REAL,
                lon REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Sozlamalar jadvali (Ishxona koordinatalari)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('office_lat', '40.5286')")
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('office_lon', '70.9425')")
        await db.commit()

async def add_employee(full_name: str, department: str, rate: float, username: str, password: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO employees (full_name, department, rate, username, password) VALUES (?, ?, ?, ?, ?)",
            (full_name, department, rate, username, password)
        )
        await db.commit()

async def delete_employee(emp_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
        await db.commit()

async def get_employees_sorted():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, full_name, department, rate, username, password FROM employees ORDER BY full_name ASC") as cursor:
            return await cursor.fetchall()

async def check_employee_credentials(username: str, password: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, full_name FROM employees WHERE username = ? AND password = ?", (username, password)) as cursor:
            return await cursor.fetchone()

async def get_recent_logs():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT full_name, action, timestamp FROM logs ORDER BY id DESC LIMIT 20") as cursor:
            return await cursor.fetchall()

async def set_office_location(lat: float, lon: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('office_lat', ?)", (str(lat),))
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('office_lon', ?)", (str(lon),))
        await db.commit()

async def get_office_location():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'office_lat'") as cursor_lat:
            lat = await cursor_lat.fetchone()
        async with db.execute("SELECT value FROM settings WHERE key = 'office_lon'") as cursor_lon:
            lon = await cursor_lon.fetchone()
        return float(lat[0]) if lat else 40.5286, float(lon[0]) if lon else 70.9425

# Masofani hisoblash (Haversine formulasi)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 # Yer radiusi (metrda)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
