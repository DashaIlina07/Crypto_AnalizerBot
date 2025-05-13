from aiogram import types, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from services.crypto import (
    get_crypto_price,
    generate_price_chart,
    get_token_description
)
from services.calculator import calculate_position

user_private_router = Router()

# Популярные токены для меню
popular_tokens = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binancecoin',
    'DOGE': 'dogecoin'
}


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я крипто-бот. Введи /menu чтобы увидеть, что я умею.")


@user_private_router.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await message.answer(
        "📋 Меню команд:\n"
        "/crypto [токен] — Курсы криптовалют\n"
        "/calc <цена_входа> <плечо> <баланс> — Калькулятор позиции\n"
        "/chart — Выбор токена и просмотр графика\n"
        "/help — Помощь"
    )


@user_private_router.message(Command("crypto"))
async def crypto_cmd(message: types.Message):
    try:
        parts = message.text.split()
        tokens = [t.lower() for t in parts[1:]] if len(parts) > 1 else ['bitcoin', 'ethereum', 'tether']
        prices = get_crypto_price(symbols=tokens)
        await message.answer(f"💱 Актуальные курсы:\n{prices}")
    except Exception as e:
        await message.answer(f"Ошибка получения курса: {e}")


@user_private_router.message(Command("calc"))
async def calc_cmd(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 4:
            raise ValueError("Неверный формат. Используй: /calc <цена_входа> <плечо> <баланс>")

        entry = float(parts[1])
        leverage = float(parts[2])
        balance = float(parts[3])

        result = calculate_position(entry, leverage, balance)
        await message.answer(
            f"📈 Размер позиции: {result['position_size']}\n"
            f"⚠️ Ликвидация: {result['liquidation_price']:.2f}"
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@user_private_router.message(Command("chart"))
async def chart_menu(message: types.Message):
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"chart_{token}")]
        for name, token in popular_tokens.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери криптовалюту для графика:", reply_markup=keyboard)


@user_private_router.callback_query(lambda c: c.data.startswith("chart_"))
async def send_chart(callback: CallbackQuery):
    token = callback.data.split("_", 1)[1]
    try:
        chart_buf = generate_price_chart(token)
        description = get_token_description(token, lang='ru')

        await callback.message.answer_photo(photo=chart_buf, caption=f"📈 График {token.title()} за 7 дней")
        await callback.message.answer(f"🧾 Описание:\n{description}")
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении информации: {e}")


@user_private_router.message()
async def echo_handler(message: types.Message):
    text = message.text.lower()

    if text in ['привет', 'приветик', 'hello', 'hi', 'хэлоу']:
        await message.answer('И тебе привет!')
    elif text in ['пока', 'до свидания', 'bye', 'пакеда']:
        await message.answer('И тебе пока!')
    else:
        await message.answer("Не понимаю. Напиши /menu для списка команд.")