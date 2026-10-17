import nest_asyncio

nest_asyncio.apply()
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
from moviepy.video.fx.all import colorx

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

API_TOKEN = '8672087286:AAGA3kjOKVkFylp6PeInqboWi29MdQnA-eU'

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
    await callback.message.answer("Iltimos, rangini o'zgartirmoqchi bo'lgan **videongizni (fayl ko'rinishida)** yuboring:")
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
    processing_msg = await callback.message.answer("🎨 Video ranglari moslashtirilmoqda, bu biroz vaqt olishi mumkin...")
    
    output_path = "output_colored.mp4"
    
    try:
        clip = VideoFileClip(video_path)
        
        # Tanlangan rang effektiga qarab ishlov berish
        if action == "color_sunset":
            # Sunset: qizg'ish/tilla tus berish
            processed_clip = colorx(clip, [1.2, 1.0, 0.8])
        elif action == "color_cyber":
            # Cyberpunk: moviy va neon tus berish
            processed_clip = colorx(clip, [0.8, 1.1, 1.4])
        else:
            # Cinematic: kontrast va tabiiy tus
            processed_clip = colorx(clip, [1.1, 1.1, 1.1])
            
        processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        
        # Natijani yuborish
        video_result = types.FSInputFile(output_path)
        await callback.message.answer_video(video_result, caption="✨ Mana, ideal rang berilgan video tayyor!")
        
        # Resurslarni tozalash
        clip.close()
        processed_clip.close()
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        
        await processing_msg.delete()
        await state.clear()
        await callback.message.answer("Bosh menyu:", reply_markup=get_main_menu())
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Videoni qayta ishlashda xatolik yuz berdi: {str(e)}")
        await state.clear()

    await callback.answer()

# Botni ishga tushirish
import asyncio

async def main():
  await dp.start_polling(bot)


await main()
