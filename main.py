from aiogram import Bot, Dispatcher, executor, types
from master import master_track
import os
from flask import Flask
from threading import Thread

app=Flask("")

@app.route("/")
def index():
    return "<h1>Bot is running</h1>"

Thread(target=app.run,args=("0.0.0.0",8080)).start()

API_TOKEN = '6600087856:AAGyteDw1H4Qi9kaI9dydyZ7Jeq6LL1UTDw'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(content_types=['audio'])
async def process_audio(message: types.Message):
    user_id = message.from_user.id
    file_id = message.audio.file_id

    input_file_path = f"{user_id}_input.mp3"
    output_file_path = f"{user_id}_output.mp3"

    await message.reply("⏬ Загружаю файл...", reply=False)
    await bot.download_file_by_id(file_id, input_file_path)

    try:
        await message.reply("🎚 Обрабатываю трек...", reply=False)
        master_track(input_file_path, output_file_path)

        with open(output_file_path, 'rb') as audio:
            await message.reply_audio(audio, caption="✨ Ваш трек обработан!")

    except Exception as e:
        await message.reply(f"❗ Произошла ошибка: {e}")

    finally:
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
        
        if os.path.exists(output_file_path):
            os.remove(output_file_path)


@dp.message_handler(lambda message: message.content_type != 'audio')
async def handle_not_audio(message: types.Message):
    await message.reply("🚫 Пожалуйста, отправьте аудиофайл!", reply=False)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)