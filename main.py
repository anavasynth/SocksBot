import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart

# Токен
from config import TOKEN

# Увімкнення логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обробник команди /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🌐 Відкрити веб-застосунок",
                web_app=WebAppInfo(url="https://parik24.new")
            )]
        ]
    )

    # Відповідь на стартове повідомлення з кнопкою
    await message.answer(
        f"Привіт, {message.from_user.first_name}! 👋\nНатисни кнопку нижче, щоб відкрити веб-застосунок:",
        reply_markup=keyboard
    )

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
