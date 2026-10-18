from moviepy.editor import VideoFileClip
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# TOKEN va obyektlarni birinchi bo'lib e'lon qilamiz:
TOKEN = "8672087286:AAHemPB_MZ1e2Nxs1NjbdWeJOFDNYW9bUI8"  # tokeningizni yozasiz
bot = Bot(token=TOKEN)
dp = Dispatcher()
import sqlite3

# Ma'lumotlar bazasini yaratish/ulash
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY
    )
""")
conn.commit()


# Har safar /start bosilganda foydalanuvchini saqlash
@dp.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
    )
    conn.commit()
    await message.answer("Xush kelibsiz! Video havolasini yuboring.")


# Faqat admin uchun statistikani ko'rish buyrug'i
@dp.message(Command("stat"))
async def stat_cmd(message: Message):
    # Faqat siz ko'ra olishingiz uchun Telegram ID ingizni kiriting
    ADMIN_ID = M.M.G  # <--- Shu yerga o'zingizning Telegram ID ingizni yozasiz

    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await message.answer(f"📊 Botingizdan foydalanuvchilar soni: {count} ta")
       
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp



# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

API_TOKEN = '8672087286:AAHemPB_MZ1e2Nxs1NjbdWeJOFDNYW9bUI8'

from aiogram.client.session.aiohttp import AiohttpSession

session = AiohttpSession()
bot = Bot(token=API_TOKEN, session=session)
dp = Dispatcher()

# Holatlar (FSM)
class BotState(StatesGroup):
    waiting_for_video_url = State()
    waiting_for_background_video = State()

# Asosiy menyu tugmalari
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Video yuklab olish (Instagram/YouTube)", callback_data="download_video")],
        [InlineKeyboardButton(text="🎨 Videoga ideal rang berish", callback_data="change_bg")]
    ])
    return keyboard

# Rang tanlash tugmalari
def get_color_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Sunset (Qizg'ish/Tilla)", callback_data="color_sunset")],
        [InlineKeyboardButton(text="💎 Cyberpunk (Moviy/Neon)", callback_data="color_cyber")],
        [InlineKeyboardButton(text="🌿 Cinematic (Tabiiy/Yashil)", callback_data="color_cinematic")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")]
    ])
    return keyboard

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Assalomu alaykum! 👋\n"
        "Men video yuklab beruvchi va ularning ranglarini o'zgartiruvchi botman.\n\n"
        "Quyidagi imkoniyatlardan birini tanlang:"
    )
    await message.answer(text, reply_markup=get_main_menu())

# Menuga qaytish
@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bosh menyu:", reply_markup=get_main_menu())
    await callback.answer()

# --- 1. VIDEO YUKLAB OLISH QISMI ---
@dp.callback_query(F.data == "download_video")
async def start_download(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Iltimos, Instagram yoki boshqa saytdagi video havolasini (linkini) yuboring:")
    await state.set_state(BotState.waiting_for_video_url)
    await callback.answer()

@dp.message(BotState.waiting_for_video_url)
async def download_video_process(message: Message, state: FSMContext):
    url = message.text
    processing_msg = await message.answer("⏳ Video yuklab olinmoqda, biroz kuting...")
    
    output_path = "downloaded_video.mp4"
    
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': output_path,
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Videoni foydalanuvchiga yuborish
        video_file = types.FSInputFile(output_path)
        await message.answer_video(video_file, caption="Mana siz so'ragan video! 🚀")
        
        # Faylni o'chirib tashlash
        if os.path.exists(output_path):
            os.remove(output_path)
            
        await processing_msg.delete()
        await state.clear()
        await message.answer("Yana nima qilamiz?", reply_markup=get_main_menu())
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Videoni yuklab olishda xatolik yuz berdi. Havolani tekshirib qaytadan urinib ko'ring.\nXato: {str(e)}")
        await state.clear()

# --- 2. VIDEOGA RANG BERISH QISMI ---
@dp.callback_query(F.data == "change_bg")
async def start_color_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Iltimos, rangini o'zgartirmoqchi bo'lgan videongizni yuboring:")
    await state.set_state(BotState.waiting_for_background_video)
    await callback.answer()

@dp.message(BotState.waiting_for_background_video, F.video)
async def receive_video_for_color(message: Message, state: FSMContext):
    # Videoni yuklab olish
    video_file = await bot.get_file(message.video.file_id)
    input_path = "input_video.mp4"
    await bot.download_file(video_file.file_path, input_path)
    
    # Ma'lumotni state'da saqlash
    await state.update_data(video_path=input_path)
    
    await message.answer("Ideal rang turini tanlang:", reply_markup=get_color_menu())

# Ranglarni qayta ishlash
@dp.callback_query(F.data.startswith("color_"))
async def apply_color_filter(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    video_path = data.get("video_path")

    if not video_path or not os.path.exists(video_path):
        await callback.message.answer("Xatolik! Video topilmadi. Iltimos boshidan boshlang.")
        await callback.answer()
        return

    action = callback.data
    processing_msg = await callback.message.answer("⚡ Video ranglari Modal bulutida ishlanmoqda, biroz kuting...")
    output_path = "output_colored.mp4"

  try:
        # Videoni o'qiymiz
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        # Filtr nomini aniqlaymiz
        if action == "color_sunset":
            filter_name = "sunset"
        elif action == "color_cyber":
            filter_name = "cyberpunk"
        else:
            filter_name = "cinematic"

        # Modal orqali videoni qayta ishlaymiz
        result_bytes = apply_color_filter.remote(video_bytes, filter_name)

        with open(output_path, "wb") as f_out:
            f_out.write(result_bytes)

        video_result = types.FSInputFile(output_path)
        await callback.message.answer_video(video_result, caption="✨ Mana, ideal rang berilgan video tayyor!")

    except Exception as e:
        await callback.message.answer(f"Videoni qayta ishlashda xatolik yuz berdi: {e}")

    finally:
        await processing_msg.delete()
        await state.clear()
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(video_path):
            os.remove(video_path)
    try:
        # Videoni o'qiymiz
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        # Filtr nomini aniqlaymiz
        if action == "color_sunset":
            filter_name = "sunset"
        elif action == "color_cyber":
            filter_name = "cyberpunk"
        else:
            filter_name = "cinematic"

        import modal
        process_video_remote = modal.Function.from_name("video-processor", "apply_color_filter")
        result_bytes = process_video_remote.remote(video_bytes, filter_name)

        with open(output_path, "wb") as f_out:
            f_out.write(result_bytes)

        video_result = types.FSInputFile(output_path)
        await callback.message.answer_video(video_result, caption="✨ Mana, ideal rang berilgan video tayyor!")

    except Exception as e:
        await callback.message.answer(f"Videoni qayta ishlashda xatolik yuz berdi: {e}")

    finally:
        await processing_msg.delete()
        await state.clear()
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(video_path):
            os.remove(video_path)
# Botni ishga tushirish
import asyncio
import os

async def main():
    # Render ishga tushganda Modal ilovasini ham avtomatik deploy qilamiz:
    os.system("modal deploy modal_app.py")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
