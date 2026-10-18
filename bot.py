import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# TOKEN va sozlamalar
TOKEN = os.getenv("8672087286:AAHemPB_MZ1e2Nxs1NjbdWeJOFDNYW9bUI8")
bot = Bot(token=TOKEN)
dp = Dispatcher()

class VideoState(StatesGroup):
    waiting_for_video = State()
    choosing_filter = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Salom! Menga video yuboring va uni ideal tarzda rang-barang qilib beraman.")
    await state.set_state(VideoState.waiting_for_video)

@dp.message(VideoState.waiting_for_video, lambda m: m.video is not None)
async def handle_video(message: types.Message, state: FSMContext):
    file_id = message.video.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    os.makedirs("downloads", exist_ok=True)
    video_path = f"downloads/{message.from_user.id}.mp4"
    await bot.download_file(file_path, destination=video_path)

    await state.update_data(video_path=video_path)

    # Tugmalarni chiqaramiz
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔥 Sunset (Qizg'ish/Tilla)", callback_data="color_sunset")],
        [types.InlineKeyboardButton(text="💎 Cyberpunk (Moviy/Neon)", callback_data="color_cyber")],
        [types.InlineKeyboardButton(text="🌿 Cinematic (Tabiiy/Yashil)", callback_data="color_cinematic")]
    ])

    await message.answer("Ideal rang turini tanlang:", reply_markup=keyboard)
    await state.set_state(VideoState.choosing_filter)

@dp.callback_query(VideoState.choosing_filter)
async def process_color_filter(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data
    data = await state.get_data()
    video_path = data.get("video_path")
    output_path = f"downloads/output_{callback.from_user.id}.mp4"

    processing_msg = await callback.message.answer("⏳ Video yuqori unumdorlikdagi bulutda qayta ishlanmoqda, biroz kuting...")

    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()

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

async def main():
    # Render ishga tushganda Modal ilovasini ham avtomatik deploy qilamiz
    os.system("modal deploy modal_app.py")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
