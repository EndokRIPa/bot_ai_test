import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import (Message, ReplyKeyboardMarkup, 
                           KeyboardButton, ContentType)
from aiogram.dispatcher.filters import Text
from aiogram.enums import ParseMode
from aiogram.filters import Command
import requests
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)

conn = sqlite3.connect('history.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                 (user_id INTEGER, username TEXT, message TEXT, 
                 response TEXT, date TEXT)''')
conn.commit()

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("Ask a question"))
main_menu.row(KeyboardButton("History"), KeyboardButton("Help"))

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "I am a smart bot with DeepSeek API!\n"
        "Send me a text or an image for analysis.",
        reply_markup=main_menu
    )

@dp.message(commands=['help'])
async def help(message: Message):
    await show_help(message)

@dp.message(Text(equals="Help"))
async def show_help(message: Message):
    help_text = (
       "<b>Available commands:</b>\n"
       "Write a text - get a response from AI\n"
       "Send an image - image analysis\n"
       "<b>Buttons:</b>\n"
       "Ask a question - start a dialogue\n"
       "History - last 5 requests\n"
       "Help - this is a message" 
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Text(equals="History"))
async def show_history(message: Message):
    cursor.execute(
        "SELECT message, response, date FROM messages "
        "WHERE user_id = ? ORDER BY date DESC LIMIT 5",
        (message.from_user.id,)
    )
    history = cursor.fetchall()
    
    if not history:
        await message.answer("The query history is empty")
        return
    
    response = "<b>Last 5 requests:</b>\n\n"
    for i, (msg, res, date) in enumerate(history, 1):
        response += (
            f"{i}. <i>{date}</i>\n"
            f"<b>You:</b> {msg[:50]}...\n"
            f"<b>Bot:</b> {res[:50]}...\n\n"
        )
    await message.answer(response, parse_mode="HTML")

@dp.message_handler(content_types=ContentType.TEXT)
async def handle_text(message: Message):
    user_text = message.text
    
    ai_response = f"You asked: {user_text}\n\n" \
                  "I'm still emulating the API response. Connect the real DeepSeek API!"
    
    save_to_db(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=user_text,
        response=ai_response
    )
    
    await message.answer(ai_response)

@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: Message):

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    
    analysis = (
        "<b>Image analysis:</b>\n"
        f"Size: {photo.width}x{photo.height}\n"
        f"File ID: {file_info.file_id}\n"
        "<i>The real API can identify objects in the photo</i>"
    )
    
    save_to_db(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message="[Photo]",
        response=analysis
    )
    
    await message.answer(analysis, parse_mode="HTML")

@dp.message_handler(content_types=ContentType.DOCUMENT)
async def handle_document(message: Message):
    doc = message.document
    response = (
        "<b>Document received:</b>\n"
        f"Name: {doc.file_name}\n"
        f"Type: {doc.mime_type}\n"
        f"Size: {doc.file_size // 1024} KB"
    )
    await message.answer(response, parse_mode="HTML")

def save_to_db(user_id: int, username: str, message: str, response: str):
    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
        (user_id, username, message, response, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())