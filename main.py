from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from master import master_track, get_preview_samples
import os
from flask import Flask
from threading import Thread

app = Flask("")

@app.route("/")
def index():
    return "<h1>Bot is running</h1>"

Thread(target=app.run, args=("0.0.0.0", 8080)).start()

API_TOKEN = '6600087856:AAGyteDw1H4Qi9kaI9dydyZ7Jeq6LL1UTDw'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
options_data = {}

style_buttons = InlineKeyboardMarkup(row_width=3).add(
    InlineKeyboardButton("Warm", callback_data="PS1"),
    InlineKeyboardButton("Balanced", callback_data="PS2"),
    InlineKeyboardButton("Open", callback_data="PS3")
)

volume_buttons = InlineKeyboardMarkup(row_width=3).add(
    InlineKeyboardButton("Low", callback_data="Low"),
    InlineKeyboardButton("Medium", callback_data="Medium"),
    InlineKeyboardButton("High", callback_data="High")
)

preview_button = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Preview", callback_data="Preview")
)

processing_button = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Processing", callback_data="Processing")
)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Welcome! Please send an audio file to start.")

@dp.message_handler(content_types=['audio'])
async def process_audio(message: types.Message):
    user_id = message.from_user.id
    file_id = message.audio.file_id

    options_data[user_id] = {'volume': 'Medium', 'style': 'PS2'}  # Default options

    input_file_path = f"{user_id}_input.mp3"
    output_file_path = f"{user_id}_output.mp3"

    await message.reply("⏬ Downloading file...", reply=False)
    await bot.download_file_by_id(file_id, input_file_path)

    await message.reply("👀 Generating previews...", reply=False)
    samples = get_preview_samples(input_file_path)
    options_data[user_id].update({'samples': samples})

    await message.reply("Please choose the style and volume for processing or preview:", reply_markup=style_buttons)
    await message.reply("Select volume:", reply_markup=volume_buttons)

@dp.callback_query_handler(lambda c: c.data in ('PS1', 'PS2', 'PS3'))
async def process_style(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    options_data[user_id]['style'] = callback_query.data
    await bot.answer_callback_query(callback_query.id, "Style selected!")
    await bot.send_message(user_id, "Press Preview to listen to the sample or Processing to process the whole track.", reply_markup=preview_button)

@dp.callback_query_handler(lambda c: c.data in ('Low', 'Medium', 'High'))
async def process_volume(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    options_data[user_id]['volume'] = callback_query.data
    await bot.answer_callback_query(callback_query.id, "Volume selected!")
    await bot.send_message(user_id, "Press Preview to listen to the sample or Processing to process the whole track.", reply_markup=preview_button)

@dp.callback_query_handler(lambda c: c.data == 'Preview')
async def process_preview(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    file_path = f"{user_id}_input.mp3"

    samples = options_data[user_id]['samples']
    selected_sample = next((sample for sample in samples if sample['intensity'] == options_data[user_id]['volume'] and sample['style'] == options_data[user_id]['style']), None)

    if selected_sample:
        await bot.send_audio(user_id, selected_sample['mp3Url'], caption="Here is your preview.")
    else:
        await bot.answer_callback_query(callback_query.id, "No preview available for the selected options.")

@dp.callback_query_handler(lambda c: c.data == 'Processing')
async def process_processing(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    input_file_path = f"{user_id}_input.mp3"
    output_file_path = f"{user_id}_output.mp3"

    try:
        await bot.send_message(user_id, "🎚 Processing your track...", reply=False)
        master_track(input_file_path, output_file_path, volume=options_data[user_id]['volume'], style=options_data[user_id]['style'])

        with open(output_file_path, 'rb') as audio:
            await bot.send_audio(user_id, audio, caption="✨ Your track has been processed!")
    except Exception as e:
        await bot.send_message(user_id, f"❗ An error occurred: {e}")
    finally:
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

@dp.message_handler(lambda message: message.content_type != 'audio')
async def handle_not_audio(message: types.Message):
    await message.reply("🚫 Please send an audio file!", reply=False)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
