import logging
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, CREATOR_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Хранилище ожидающих подтверждения платежей
pending_payments = {}

PROXY_PRICES = {
    "usa": 149,      # США
    "russia": 99,    # Россия
    "turkey": 199,    # Турция
    "brazil": 199,    # Бразилия
    "india": 249,     # Индия
    "germany": 299,   # Германия
    "italy": 299,     # Италия
    "poland": 249,    # Польша
    "japan": 299      # Япония
}

COUNTRY_NAMES = {
    "usa": "🇺🇸 США",
    "russia": "🇷🇺 Россия",
    "turkey": "🇹🇷 Турция",
    "brazil": "🇧🇷 Бразилия",
    "india": "🇮🇳 Индия",
    "germany": "🇩🇪 Германия",
    "italy": "🇮🇹 Италия",
    "poland": "🇵🇱 Польша",
    "japan": "🇯🇵 Япония"
}

def generate_proxy(country):
    """Генерация случайного прокси с IP в формате x.x.x.x"""
    ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
    
    return {
        "ip": ip,
        "port": str(random.randint(1000, 9999)),
        "login": f"user_{random.randint(1000, 9999)}",
        "password": f"pass_{random.randint(10000, 99999)}"
    }

def create_country_keyboard():
    """Создаем клавиатуру с кнопками для выбора страны"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = [
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['usa']} ({PROXY_PRICES['usa']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['russia']} ({PROXY_PRICES['russia']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['turkey']} ({PROXY_PRICES['turkey']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['brazil']} ({PROXY_PRICES['brazil']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['india']} ({PROXY_PRICES['india']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['germany']} ({PROXY_PRICES['germany']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['italy']} ({PROXY_PRICES['italy']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['poland']} ({PROXY_PRICES['poland']} руб)"),
        KeyboardButton(f"Купить прокси {COUNTRY_NAMES['japan']} ({PROXY_PRICES['japan']} руб)")
    ]
    
    markup.add(*buttons)
    return markup

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать в бота для покупки резидентских прокси!\n"
        "Выберите страну прокси:",
        reply_markup=create_country_keyboard()
    )

@dp.message_handler(lambda message: message.text.startswith("Купить прокси"))
async def buy_proxy(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет username"
    
    country = None
    price = None
    
    # Определяем страну по тексту кнопки
    for code, name in COUNTRY_NAMES.items():
        if name in message.text:
            country = code
            price = PROXY_PRICES[code]
            break
    
    if country:
        # Генерируем уникальный ID платежа
        payment_id = f"pay_{random.randint(100000, 999999)}"
        
        # Сохраняем информацию о платеже
        pending_payments[payment_id] = {
            "user_id": user_id,
            "username": username,
            "country": country,
            "price": price,
            "status": "waiting"
        }
        
        # Отправляем реквизиты пользователю
        await message.answer(
            f"Для покупки прокси из {COUNTRY_NAMES[country]}:\n"
            f"Сумма: {price} руб\n\n"
            f"Реквизиты для оплаты:\n"
            f"Т-БАНК: 2200 7005 0226 1372\n\n"
            f"В комментарии к платежу укажите количество купленных прокси и их страны.\n"
            f"Ваш ID платежа: {payment_id}"
        )
        
        # Отправляем уведомление создателю
        await bot.send_message(
            CREATOR_ID,
            f"🛒 Новый заказ прокси:\n"
            f"User ID: {user_id}\n"
            f"Username: @{username}\n"
            f"Страна: {COUNTRY_NAMES[country]}\n"
            f"Сумма: {price} руб\n"
            f"ID платежа: {payment_id}",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(
                    "✅ Подтвердить оплату",
                    callback_data=f"confirm_{payment_id}"
                ),
                InlineKeyboardButton(
                    "❌ Отклонить",
                    callback_data=f"reject_{payment_id}"
                )
            )
        )

@dp.callback_query_handler(lambda c: c.data.startswith('confirm_'))
async def confirm_payment(callback_query: types.CallbackQuery):
    payment_id = callback_query.data.split('_')[1]
    
    if payment_id in pending_payments:
        payment = pending_payments[payment_id]
        
        # Генерируем прокси
        proxy_data = generate_proxy(payment["country"])
        
        # Отправляем прокси пользователю
        await bot.send_message(
            payment["user_id"],
            f"✅ Ваш платеж подтвержден!\n"
            f"Прокси из {COUNTRY_NAMES[payment['country']]}:\n"
            f"IP: {proxy_data['ip']}\n"
            f"Порт: {proxy_data['port']}\n"
            f"Логин: {proxy_data['login']}\n"
            f"Пароль: {proxy_data['password']}\n\n"
            f"Срок действия: 30 дней"
        )
        
        # Уведомляем создателя
        await callback_query.message.edit_text(
            f"✅ Платеж подтвержден:\n"
            f"User ID: {payment['user_id']}\n"
            f"Username: @{payment['username']}\n"
            f"ID платежа: {payment_id}\n"
            f"Выданы прокси: {proxy_data['ip']}:{proxy_data['port']}"
        )
        
        # Удаляем из ожидающих
        del pending_payments[payment_id]
        
        await callback_query.answer("Платеж подтвержден")
    else:
        await callback_query.answer("Платеж не найден")

@dp.callback_query_handler(lambda c: c.data.startswith('reject_'))
async def reject_payment(callback_query: types.CallbackQuery):
    payment_id = callback_query.data.split('_')[1]
    
    if payment_id in pending_payments:
        payment = pending_payments[payment_id]
        
        # Уведомляем пользователя
        await bot.send_message(
            payment["user_id"],
            f"❌ Ваш платеж {payment_id} отклонен администратором.\n"
            f"Если вы уже оплатили, свяжитесь с @creator_username"
        )
        
        # Уведомляем создателя
        await callback_query.message.edit_text(
            f"❌ Платеж отклонен:\n"
            f"User ID: {payment['user_id']}\n"
            f"Username: @{payment['username']}\n"
            f"ID платежа: {payment_id}"
        )
        
        # Удаляем из ожидающих
        del pending_payments[payment_id]
        
        await callback_query.answer("Платеж отклонен")
    else:
        await callback_query.answer("Платеж не найден")

@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id == CREATOR_ID:
        text = "⚙️ Админ-панель:\n"
        text += f"Ожидают подтверждения: {len(pending_payments)} платежей\n\n"
        
        if pending_payments:
            text += "Последние 5 платежей:\n"
            for payment_id, payment in list(pending_payments.items())[:5]:
                text += (f"ID: {payment_id}\n"
                        f"User: @{payment['username']}\n"
                        f"Страна: {COUNTRY_NAMES[payment['country']]}\n"
                        f"Сумма: {payment['price']} руб\n\n")
        
        await message.answer(text)
    else:
        await message.answer("Доступ запрещен")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
