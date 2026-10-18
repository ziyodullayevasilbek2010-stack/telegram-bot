import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip

TOKEN = "BU_YERGA_BOT_TOKENINGizNI_YOZING"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. Start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n"
        "Menga YouTube yoki Instagram havolasini yuboring (videoni yuklab beraman) "
        "yoki tayyor video fayl yuboring (orqa foniga rang berib beraman)."
    )

# 2. Havolalarni qabul qilish va video yuklash (YouTube, Instagram)
@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    if text and (("http://" in text) or ("https://" in text)):
        await message.answer("⏳ Video yuklab olinmoqda, biroz kuting...")
        
        output_template = "downloaded_video.mp4"
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
            
            if os.path.exists(output_template):
                video_file = types.FSInputFile(output_template)
                await message.answer_video(video=video_file, caption="Mana siz istagan video! 📥")
                os.remove(output_template)
            else:
                await message.answer("❌ Videoni yuklab bo'lmadi.")
        except Exception as e:
            await message.answer(f"❌ Xatolik yuz berdi: {e}")
    else:
        await message.answer("Iltimos, yaroqli havola yuboring yoki video fayl tashlang!")

# Botni ishga tushirish
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 

# Video faylni qabul qilish uchun handler
@dp.message(lambda message: message.content_type == types.ContentType.VIDEO)
async def handle_video_background(message: types.Message):
    await message.answer("🎨 Videoga orqa fon rangi berilmoqda...")
    
    # Videoni yuklab olish
    file_id = message.video.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    input_video = "input.mp4"
    output_video = "output.mp4"
    
    await bot.download_file(file_path, input_video)
    
    try:
        # MoviePy yordamida fon rangini berish (masalan: 1080x1920 Vertikal format, qora yoki chiroyli rang)
        clip = VideoFileClip(input_video)
        
        # Misol uchun fon o'lchami va rangi (RGB: Masalan, To'q binafsha yoki qora)
        bg_width, bg_height = 1080, 1920
        background = ColorClip(size=(bg_width, bg_height), color=(20, 20, 30), duration=clip.duration)
        
        # Videoni markazga joylash
        clip_resized = clip.resize(height=1200) # Videoni kichraytirib markazga qo'yish
        final_clip = CompositeVideoClip([background, clip_resized.set_position("center")])
        
        final_clip.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")
        
        # Yuborish
        video_result = types.FSInputFile(output_video)
        await message.answer_video(video=video_result, caption="✨ Mana, orqa foni yangilangan video!")
        
        # Fayllarni tozalash
        clip.close()
        final_clip.close()
        os.remove(input_video)
        os.remove(output_video)
        
    except Exception as e:
        await message.answer(f"❌ Videoni qayta ishlashda xatolik: {e}")
