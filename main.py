import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from yt_dlp import YoutubeDL
from aiohttp import web

TOKEN = "8672087286:AAHemPB_MZ1eNxs1NjbdWeJOFDNYW9bUI8"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n"
        "Menga YouTube yoki Instagram havolasini yuboring, videoni yuklab beraman!"
    )

@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    if text and ("http://" in text or "https://" in text):
        await message.answer("⏳ Video yuklab olinmoqda, biroz kuting...")
        
        output_template = "downloaded_video.mp4"
        ydl_opts = {'format': 'best', 'outtmpl': output_template}
        
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

async def handle_http(request):
    return web.Response(text="Bot ishlayapti!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_http)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("Bot va veb-server ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
