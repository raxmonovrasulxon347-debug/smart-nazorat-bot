import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from config import BOT_TOKEN, WEBAPP_URL, ALLOWED_RADIUS_METERS
from database import init_db, check_employee_credentials, get_office_location, calculate_distance, aiosqlite, DB_NAME
from admin import admin_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Keldim", web_app=WebAppInfo(url=f"{WEBAPP_URL}?action=in")),
                KeyboardButton(text="🔴 Ketdim", web_app=WebAppInfo(url=f"{WEBAPP_URL}?action=out"))
            ]
        ],
        resize_keyboard=True
    )
    await message.answer("Xush kelibsiz! Ishga kelganingizni yoki ketganingizni belgilash uchun tugmani bosing:", reply_markup=kb)

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        username = data.get("username")
        password = data.get("password")
        user_lat = data.get("lat")
        user_lon = data.get("lon")

        # 1. Login va parol tekshiruvi
        emp = await check_employee_credentials(username, password)
        if not emp:
            await message.answer("❌ Noto'g'ri login yoki parol kiritildi!")
            return

        emp_id, full_name = emp

        # 2. Geolokatsiyani tekshirish (Agar WebApp’dan yuborilgan bo'lsa)
        if user_lat and user_lon:
            office_lat, office_lon = await get_office_location()
            distance = calculate_distance(float(user_lat), float(user_lon), office_lat, office_lon)
            if distance > ALLOWED_RADIUS_METERS:
                await message.answer(f"❌ Siz ishxona hududida emassiz! (Masofa: {int(distance)} metr. Ruxsat berilgan: {ALLOWED_RADIUS_METERS}m)")
                return

        # 3. Bazaga yozish
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO logs (user_id, full_name, action, lat, lon) VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, full_name, action, user_lat, user_lon)
            )
            await db.commit()

        status_str = "🟢 Ishga kelganingiz" if action == "checked_in" else "🔴 Ishdan ketganingiz"
        await message.answer(f"✅ Xush kelibsiz, <b>{full_name}</b>!\n{status_str} muvaffaqiyatli belgilandi.", parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

async def main():
    await init_db()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
