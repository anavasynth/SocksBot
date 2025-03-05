from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
import asyncio
import logging
import base64
import json
import os

# Токен та паролі
from config import TOKEN, ADMIN_PASSWORD

# Увімкнення логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словник для зберігання корзини користувачів
user_cart = {}

# Абсолютний шлях до файлу для збереження chat_id
CHAT_IDS_FILE = "/home/dengromko/SocksWebApp/chat_ids.json"

# Функція для перевірки існування файлу та створення його, якщо немає
def ensure_file_exists():
    os.makedirs(os.path.dirname(CHAT_IDS_FILE), exist_ok=True)
    if not os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, "w", encoding="utf-8") as file:
            json.dump([], file)

# Функція для збереження chat_id у JSON-файл
def save_chat_id(chat_id):
    ensure_file_exists()
    try:
        with open(CHAT_IDS_FILE, "r", encoding="utf-8") as file:
            chat_ids = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        chat_ids = []
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        with open(CHAT_IDS_FILE, "w", encoding="utf-8") as file:
            json.dump(chat_ids, file, indent=4)

# Функція для завантаження асортименту з JSON файлу
def load_products_from_json():
    with open('/home/dengromko/SocksWebApp/products.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Клавіатура головного меню з кнопкою "Корзина" та "Асортимент"
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📋 Асортимент")]
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_cart[message.from_user.id] = []  # Ініціалізація корзини для нового користувача
    save_chat_id(message.from_user.id)  # Збереження chat_id у JSON
    await message.answer(
        "👋 Привіт я бот Катюня!\n"
        "Тут шкарпетки в яких почуєшся здатним змінити світ. "
        "В мене можна замовити мерч, який є в наявності. "
        "Купуючи цей мерч ти змінюєш життя покращуєш життя молоді із синдромом Дауна. "
        "Доставка Новою поштою по Україні протягом тижня.",
        reply_markup=main_keyboard
    )

    await asyncio.sleep(2)  # Очікуємо 5 секунд перед відображенням асортименту

    products = load_products_from_json()  # Оновлюємо список товарів при кожному запиті

    for product in products:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"Розмір {size}", callback_data=f"add_to_cart:{product['id']}:{size}")]
                for size in product["sizes"]
            ]
        )

        await message.answer_photo(
            photo=product["photo"],
            caption=f"**{product['name']}**\n{product['description']}\n\nЦіна: {product['price']}",
            reply_markup=keyboard
        )

        await asyncio.sleep(0.4)  # Очікуємо 2 секунди перед відправкою наступного товару

# Обробник кнопки "📋 Асортимент"
@dp.message(F.text == "📋 Асортимент")
async def show_products(message: Message):
    products = load_products_from_json()
    for product in products:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"Розмір {size}", callback_data=f"add_to_cart:{product['id']}:{size}")]
                for size in product["sizes"]
            ]
        )

        await message.answer_photo(
            photo=product["photo"],
            caption=f"**{product['name']}**\n{product['description']}\nЦіна: {product['price']} грн",
            reply_markup=keyboard
        )

@dp.callback_query(F.data.startswith("add_to_cart"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, product_id, size = callback.data.split(":")
    products = load_products_from_json()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await callback.answer("❌ Товар не знайдено!", show_alert=True)
        return

    # Перевіряємо, чи є товар у кошику
    if user_id not in user_cart:
        user_cart[user_id] = []

    for item in user_cart[user_id]:
        if item["name"] == product["name"] and item["size"] == size:
            item["quantity"] += 1
            await callback.answer(f"✅ {product['name']} ({size}) додано ще одну одиницю!", show_alert=True)
            await update_cart_message(user_id)  # Додано оновлення кошика навіть при повторному натисканні
            return

    # Додаємо товар у кошик, якщо його там ще немає
    user_cart[user_id].append({"name": product["name"], "size": size, "quantity": 1, "price": int(product["price"])})
    await callback.answer(f"✅ {product['name']} ({size}) додано в корзину!", show_alert=True)

    await update_cart_message(user_id)  # Завжди оновлюємо повідомлення про кошик


async def update_cart_message(user_id):
    cart = user_cart.get(user_id, [])

    if not cart:
        return

    text = "🛍️ **Ваша корзина:**\n\n"
    total_price = 0
    for item in cart:
        text += f"• {item['name']} - {item['size']} x {item['quantity']}\n"
        total_price += item["price"] * item["quantity"]

    text += f"\n**Загальна сума:** {total_price} грн"

    # Формуємо URL з параметрами
    cart_data = {
        "total_price": total_price,
        "items": [{"name": item["name"], "size": item["size"], "quantity": item["quantity"], "price": item["price"]} for item in cart]
    }
    cart_data_json = json.dumps(cart_data)
    encoded_cart_data = base64.urlsafe_b64encode(cart_data_json.encode()).decode()
    url = f"https://dengromko.pythonanywhere.com/?cart_data={encoded_cart_data}"

    # Оновлення повідомлення
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Оформити замовлення", web_app=WebAppInfo(url=url), hide="False")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🗑️ Очистити корзину")]
        ],
        resize_keyboard=True
    )

    # Відправлення повідомлення користувачу
    await bot.send_message(user_id, text, reply_markup=keyboard)

# Обробник натискання на кнопку "🛒 Корзина"
@dp.message(F.text == "🛒 Корзина")
async def view_cart(message: Message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])

    if not cart:
        await message.answer("🛒 Ваша корзина порожня.")
        return

    text = "🛍️ **Ваша корзина:**\n\n"
    total_price = 0
    for item in cart:
        text += f"• {item['name']} - {item['size']} x {item['quantity']}\n"
        total_price += item["price"] * item["quantity"]

    text += f"\n**Загальна сума:** {total_price} грн"

    # Формуємо URL з параметрами
    cart_data = {
        "total_price": total_price,
        "items": [{"name": item["name"], "size": item["size"], "quantity": item["quantity"], "price": item["price"]} for item in cart]
    }
    cart_data_json = json.dumps(cart_data)
    encoded_cart_data = base64.urlsafe_b64encode(cart_data_json.encode()).decode()
    url = f"https://dengromko.pythonanywhere.com/?cart_data={encoded_cart_data}"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Оформити замовлення", web_app=WebAppInfo(url=url))],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🗑️ Очистити корзину")]
        ],
        resize_keyboard=True
    )

    await message.answer(text, reply_markup=keyboard)

# Обробник кнопки "🗑️ Очистити корзину"
@dp.message(F.text == "🗑️ Очистити корзину")
async def clear_cart(message: Message):
    user_id = message.from_user.id
    user_cart[user_id] = []  # Очищаємо корзину
    await message.answer("✅ Ваша корзина очищена.", reply_markup=main_keyboard)

# Обробник кнопки "🔙 Назад"
@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: Message):
    await message.answer("👋 Повертаємось у головне меню.", reply_markup=main_keyboard)


# Видалення кнопок після оплати
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = json.loads(message.web_app_data.data)
    if data.get("action") == "clear_cart":
        user_id = message.from_user.id
        user_cart[user_id] = []

        # Відправляємо повідомлення та прибираємо клавіатуру
        await message.answer("✅ Дякуємо, оплата пройшла успішно! Очікуйте доставку.", reply_markup=main_keyboard)


# Флаг для перевірки чи ввів користувач пароль
waiting_for_password = {}

# Команда для доступу до адмін панелі
@dp.message(F.text == "/adminpanel")
async def adminpanel_handler(message: Message):
    user_id = message.from_user.id
    waiting_for_password[user_id] = True  # Встановлюємо очікування пароля
    await message.answer("🔑 Введіть пароль для доступу до адмін панелі:")

# Обробник пароля для адмін панелі
@dp.message(F.text)
async def handle_admin_password(message: Message):
    user_id = message.from_user.id

    if waiting_for_password.get(user_id, False):  # Якщо очікується пароль
        if message.text == ADMIN_PASSWORD:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Адмін панель: Змінити асортимент",
                                          web_app=WebAppInfo(url="https://dengromko.pythonanywhere.com/admin"))]
                ]
            )
            await message.answer("✅ Пароль вірний! Ось адмін панель для зміни асортименту:", reply_markup=keyboard)
            waiting_for_password[user_id] = False  # Скидаємо флаг після успішного входу
        else:
            await message.answer("❌ Невірний пароль! Спробуйте ще раз.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
