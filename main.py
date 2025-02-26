import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import CommandStart

# Токен
from config import TOKEN

# Увімкнення логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словник для зберігання корзини користувачів
user_cart = {}

# Каталог товарів
PRODUCTS = [
    {"id": "1", "name": "Шкарпетки 'Добро' 🧦", "photo": "https://dobra-para.com.ua/images/stories/virtuemart/product/konoplya-man.jpg", "description": "Бавовняні шкарпетки з принтом 'Добро'.", "sizes": ["M", "L"]},
    {"id": "2", "name": "Шкарпетки 'Серце' ❤️", "photo": "https://images.prom.ua/2245777328_w600_h600_2245777328.jpg", "description": "Теплі шкарпетки з вишивкою серця.", "sizes": ["M", "L"]},
    {"id": "3", "name": "Шкарпетки 'Сила' 💪", "photo": "https://images.prom.ua/3341671155_w200_h200_3341671155.jpg", "description": "Чорні спортивні шкарпетки з написом 'Сила'.", "sizes": ["M", "L"]},
    {"id": "4", "name": "Шкарпетки 'Україна' 🇺🇦", "photo": "https://image-thumbs.shafastatic.net/313131330_310_430", "description": "Шкарпетки у кольорах прапора України.", "sizes": ["M", "L"]},
    {"id": "5", "name": "Шкарпетки 'Зима' ❄️", "photo": "https://images.prom.ua/3341671155_w200_h200_noski-s-printom.jpg", "description": "Зимові теплі шкарпетки з візерунками.", "sizes": ["M", "L"]}
]


# Команда /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_cart[message.from_user.id] = []  # Ініціалізація корзини для нового користувача
    await message.answer("👋 Привіт! Ось наш асортимент шкарпеток:")

    for product in PRODUCTS:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                [InlineKeyboardButton(text = f"Розмір {size}" , callback_data = f"add_to_cart:{product['id']}:{size}")]
                for size in product["sizes"]
            ]
        )

        await message.answer_photo(
            photo = product["photo"] ,
            caption = f"**{product['name']}**\n{product['description']}" ,
            reply_markup = keyboard
        )


# Обробник додавання товару в корзину
@dp.callback_query(F.data.startswith("add_to_cart"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    _ , product_id , size = callback.data.split(":")

    product = next((p for p in PRODUCTS if p["id"] == product_id) , None)
    if not product:
        await callback.answer("❌ Товар не знайдено!" , show_alert = True)
        return

    user_cart[user_id].append({"name": product["name"] , "size": size})

    await callback.answer(f"✅ {product['name']} ({size}) додано в корзину!" , show_alert = True)


# Команда /cart для перегляду корзини
@dp.message(F.text == "/cart")
async def view_cart(message: Message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id , [])

    if not cart:
        await message.answer("🛒 Ваша корзина порожня.")
        return

    text = "🛍️ **Ваша корзина:**\n\n"
    for item in cart:
        text += f"• {item['name']} - {item['size']}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text = "✅ Оформити замовлення" ,
                                  web_app=WebAppInfo(url="https://sockswebapp.onrender.com/"))
             ]
        ]
    )

    await message.answer(text , reply_markup = keyboard)


# Обробник оформлення замовлення
@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart = user_cart.get(user_id , [])

    if not cart:
        await callback.answer("❌ Корзина порожня!" , show_alert = True)
        return

    text = "✅ **Ваше замовлення оформлене!**\nМи скоро зв'яжемось для підтвердження.\n\n🧦 Ваше замовлення:\n"
    for item in cart:
        text += f"• {item['name']} - {item['size']}\n"

    # Очищаємо корзину
    user_cart[user_id] = []

    await callback.message.answer(text)
    await callback.answer()


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
