import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from admin import router as admin_router
from database import init_db

# Render port talabini qondirish uchun mini HTTP server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ishlamoqda...")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    await init_db()
    dp.include_router(admin_router)
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Web serverni alohida thread'da yurgizish
    threading.Thread(target=run_http_server, daemon=True).start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
