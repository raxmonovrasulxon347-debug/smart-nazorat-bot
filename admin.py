from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, ADMIN_PASSWORD
from database import (
    get_employees_sorted, add_employee, delete_employee, 
    get_recent_logs, set_office_location, get_office_location
)
from reports import generate_word_report

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_password = State()
    adding_name = State()
    adding_dept = State()
    adding_rate = State()
    adding_username = State()
    adding_emp_password = State()
    deleting_id = State()
    waiting_for_location = State()

@admin_router.message(Command("admin"))
async def admin_cmd(message: types.Message, state: FSMContext):
    user_id = int(message.from_user.id)
    admin_id = int(ADMIN_ID)
    
    print(f"--> /admin buyrug'i keldi! Sizning ID: {user_id} | Config'dagi ID: {admin_id}")
    
    if user_id != admin_id:
        await message.answer(f"❌ Siz admin emassiz!\nSizning ID: <code>{user_id}</code>\nBaza ID: <code>{admin_id}</code>", parse_mode="HTML")
        return
        
    await state.set_state(AdminStates.waiting_for_password)
    await message.answer("🔑 Admin panelga kirish uchun PIN kodni kiriting:")

@admin_router.message(AdminStates.waiting_for_password)
async def check_password(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.clear()
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="👥 Xodimlar ro'yxati (A-Z)"), types.KeyboardButton(text="🕒 Keldi-ketdi vaqtlari")],
                [types.KeyboardButton(text="➕ Xodim qo'shish"), types.KeyboardButton(text="❌ Xodimni o'chirish")],
                [types.KeyboardButton(text="📍 Ishxona lokatsiyasi"), types.KeyboardButton(text="📄 Word hisobot")],
            ],
            resize_keyboard=True
        )
        await message.answer("✅ Admin paneliga xush kelibsiz:", reply_markup=kb)
    else:
        await message.answer("❌ Noto'g'ri PIN kod!")

@admin_router.message(F.text == "👥 Xodimlar ro'yxati (A-Z)")
async def list_emp(message: types.Message):
    if int(message.from_user.id) != int(ADMIN_ID):
        return
    employees = await get_employees_sorted()
    if not employees:
        await message.answer("Hozircha bazada xodimlar yo'q.")
        return
    text = "<b>👥 Xodimlar ro'yxati:</b>\n\n"
    for emp in employees:
        text += f"ID: <code>{emp[0]}</code> | <b>{emp[1]}</b>\nBo'lim: {emp[2]} | Stavkasi: {emp[3]} so'm\nLogin: <code>{emp[4]}</code> | Parol: <code>{emp[5]}</code>\n------------------\n"
    await message.answer(text, parse_mode="HTML")

@admin_router.message(F.text == "➕ Xodim qo'shish")
async def start_add(message: types.Message, state: FSMContext):
    if int(message.from_user.id) != int(ADMIN_ID):
        return
    await state.set_state(AdminStates.adding_name)
    await message.answer("Xodimning Ism va Familiyasini kiriting:")

@admin_router.message(AdminStates.adding_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminStates.adding_dept)
    await message.answer("Bo'lim nomini kiriting:")

@admin_router.message(AdminStates.adding_dept)
async def process_dept(message: types.Message, state: FSMContext):
    await state.update_data(dept=message.text)
    await state.set_state(AdminStates.adding_rate)
    await message.answer("Soatbay stavkasini kiriting (so'mda):")

@admin_router.message(AdminStates.adding_rate)
async def process_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text)
        await state.update_data(rate=rate)
        await state.set_state(AdminStates.adding_username)
        await message.answer("Xodim uchun <b>Login</b> kiriting:", parse_mode="HTML")
    except ValueError:
        await message.answer("Stavkani raqamlarda kiriting!")

@admin_router.message(AdminStates.adding_username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(AdminStates.adding_emp_password)
    await message.answer("Xodim uchun <b>Parol</b> kiriting:", parse_mode="HTML")

@admin_router.message(AdminStates.adding_emp_password)
async def process_emp_password(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    emp_password = message.text
    
    await add_employee(
        user_data['name'], 
        user_data['dept'], 
        user_data['rate'], 
        user_data['username'], 
        emp_password
    )
    await state.clear()
    await message.answer(
        f"✅ Xodim <b>{user_data['name']}</b> qo'shildi!\n"
        f"<b>Login:</b> <code>{user_data['username']}</code>\n"
        f"<b>Parol:</b> <code>{emp_password}</code>", 
        parse_mode="HTML"
    )

@admin_router.message(F.text == "❌ Xodimni o'chirish")
async def start_delete(message: types.Message, state: FSMContext):
    if int(message.from_user.id) != int(ADMIN_ID):
        return
    await state.set_state(AdminStates.deleting_id)
    await message.answer("O'chirmoqchi bo'lgan xodimingizning ID raqamini kiriting:")

@admin_router.message(AdminStates.deleting_id)
async def process_delete(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await delete_employee(int(message.text))
        await state.clear()
        await message.answer(f"✅ ID {message.text} bo'lgan xodim o'chirildi.")
    else:
        await message.answer("To'g'ri ID kiriting.")

@admin_router.message(F.text == "🕒 Keldi-ketdi vaqtlari")
async def show_logs(message: types.Message):
    if int(message.from_user.id) != int(ADMIN_ID):
        return
    logs = await get_recent_logs()
    if not logs:
        await message.answer("Hali keldi-ketdi ma'lumotlari yo'q.")
        return
    text = "<b>🕒 Oxirgi keldi-ketdi yozuvlari:</b>\n\n"
    for log in logs:
        status = "🟢 Keldi" if log[1] == "checked_in" else "🔴 Ketdi"
        text += f"{status} | <b>{log[0]}</b> | {log[2]}\n"
    await message.answer(text, parse_mode="HTML")

@admin_router.message(F.text == "📍 Ishxona lokatsiyasi")
async def change_location_start(message: types.Message, state: FSMContext):
    if int(message.from_user.id) != int(ADMIN_ID):
        return
    lat, lon = await get_office_location()
    await state.set_state(AdminStates.waiting_for_location)
    await message.answer(
        f"📍 Hozirgi koordinatalar: <code>{lat}, {lon}</code>\n\n"
        f"Yangi lokatsiyani Telegram Location (📎 Sprepka) orqali yuboring yoki text ko'rinishida kiriting (Masalan: <code>40.5286, 70.9425</code>):", 
        parse_mode="HTML"
    )

@admin_router.message(AdminStates.waiting_for_location)
async def process_location(message: types.Message, state: FSMContext):
    # Если локация отправлена через Telegram Location
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        await set_office_location(lat, lon)
        await state.clear()
        await message.answer(f"✅ Ishxona lokatsiyasi saqlandi!\nKoordinatalar: <code>{lat}, {lon}</code>", parse_mode="HTML")
    # Если координаты отправлены текстом (например: 40.5286, 70.9425)
    elif message.text:
        try:
            coords = message.text.split(',')
            lat = float(coords[0].strip())
            lon = float(coords[1].strip())
            await set_office_location(lat, lon)
            await state.clear()
            await message.answer(f"✅ Ishxona lokatsiyasi saqlandi!\nKoordinatalar: <code>{lat}, {lon}</code>", parse_mode="HTML")
        except Exception:
            await message.answer("❌ Noto'g'ri format! Lokatsiyani Telegram orqali yuboring yoki matn ko'rinishida kiriting (Masalan: <code>40.5286, 70.9425</code>):", parse_mode="HTML")

@admin_router.message(F.text == "📄 Word hisobot")
async def download_word(message: types.Message):
    if int(message.from_user.id) != int(ADMIN_ID):
        return
    await message.answer("📄 Word hisobot tayyorlanmoqda...")
    file_path = await generate_word_report()
    doc = types.FSInputFile(file_path)
    await message.answer_document(doc, caption="Hisobot (.docx)")
