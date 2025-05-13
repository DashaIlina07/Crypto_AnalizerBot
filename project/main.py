import os
import asyncio
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile

from dotenv import load_dotenv, find_dotenv

# Загрузка токена из .env
load_dotenv(find_dotenv())
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()

# Популярные токены
popular_tokens = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binancecoin',
    'DOGE': 'dogecoin'
}

faq_data = {
    "q1": {
        "question": "Что такое криптовалюта?",
        "answer": "Криптовалюта — это разновидность цифровой валюты, не имеющей физического воплощения и единого центра, который бы ее контролировал. Работает в так называемом «блокчейне» или цепочке блоков с информацией."
    },
    "q2": {
        "question": "Что такое блокчейн?",
        "answer": "Блокчейн (от англ. block — «блок, модуль» и chain — «цепочка») — это непрерывная цепочка блоков с данными. Каждый из блоков содержит информацию и ссылку на предыдущий. Это помогает, например, проследить историю покупок и продаж актива."
    },
    "q3": {
        "question": "Что такое майнинг?",
        "answer": "Майнинг — это процесс добычи криптовалют с помощью вычислительных устройств, решающих задачи для подтверждения транзакций. Майнеры получают награду за добавление блоков в блокчейн, что обеспечивает безопасность сети."
    },
    "q4": {
        "question": "Что такое токены и их типы?",
        "answer": "Токен — цифровой актив на основе блокчейна. В отличие от коина, токен не имеет собственного блокчейна. Типы токенов: альткоин, стейблкоин, токен управления, невзаимозаменяемый токен (NFT)."
    }
}

# Получение курсов криптовалют
def get_crypto_price(symbols=('bitcoin', 'ethereum', 'tether'), currency='usd'):
    url = "https://api.coingecko.com/api/v3/simple/price"
    response = requests.get(url, params={'ids': ','.join(symbols), 'vs_currencies': currency})
    data = response.json()

    result = []
    for symbol in symbols:
        price = data.get(symbol, {}).get(currency)
        if price:
            result.append(f"{symbol.upper()}: {price} {currency.upper()}")
    return '\n'.join(result)

# Калькулятор позиции и ликвидации
def calculate_position(entry_price: float, leverage: float, balance: float):
    position_size = balance * leverage
    liquidation_price = entry_price - (entry_price * (1 / leverage)) if leverage != 0 else 0
    return {
        "position_size": position_size,
        "liquidation_price": liquidation_price
    }

# История цены и график
def get_price_history(symbol='bitcoin', currency='usd', days=7):
    url = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart'
    params = {'vs_currency': currency, 'days': days}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    return [(x[0], x[1]) for x in data['prices']]

def generate_price_chart(symbol='bitcoin', currency='usd'):
    history = get_price_history(symbol, currency)
    timestamps = [datetime.fromtimestamp(ts / 1000).strftime('%b %d') for ts, _ in history]
    prices = [price for _, price in history]

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, prices, label=f"{symbol.upper()}", color='blue')
    plt.xticks(rotation=45)
    plt.title(f"{symbol.upper()} Цена за 7 дней")
    plt.xlabel("Дата")
    plt.ylabel(f"Цена в {currency.upper()}")
    plt.tight_layout()
    plt.grid(True)
    plt.legend()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# Получение описания токена
def get_token_description(symbol='bitcoin', lang='ru'):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
    res = requests.get(url, params={"localization": "true"})
    res.raise_for_status()
    data = res.json()

    desc = data.get("description", {}).get(lang) or data.get("description", {}).get("en", "")
    return desc.strip()[:1000] + "..." if desc else "Описание недоступно."

# Хендлеры

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Открыть меню", callback_data="open_menu")]
        ]
    )
    await message.answer(
        "👋 Привет! Я крипто-бот. Помогу узнать курсы, построить графики и рассчитать позиции.\n\n"
        "Нажми кнопку ниже или введи /menu для списка команд.",
        reply_markup=keyboard
    )

@dp.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await message.answer(
        "📋 Меню команд:\n"
        "/crypto — курсы самых популярных криптовалют.\n"
        "/calc <цена_входа> <плечо> <баланс> — калькулятор позиции.\n"
        "/chart — выбор коина и его график.\n"
        "/faq — часто задаваемые вопросы и ответы на них.\n"
        "/help — помощь"
    )

@dp.message(Command("crypto"))
async def crypto_cmd(message: types.Message):
    try:
        parts = message.text.split()
        tokens = [t.lower() for t in parts[1:]] if len(parts) > 1 else ['bitcoin', 'ethereum', 'tether']
        prices = get_crypto_price(tokens)
        await message.answer(f"💱 Актуальные курсы:\n{prices}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("calc"))
async def calc_cmd(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 4:
            raise ValueError("Используй: /calc <вход> <плечо> <баланс>")
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

@dp.message(Command("faq"))
async def faq_cmd(message: types.Message):
    buttons = [
        [InlineKeyboardButton(text=faq_data[qid]["question"], callback_data=f"faq_{qid}")]
        for qid in faq_data
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("❓ Выберите вопрос:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("faq_"))
async def answer_faq(callback: CallbackQuery):
    qid = callback.data.split("_", 1)[1]
    faq = faq_data.get(qid)
    if faq:
        await callback.message.answer(f"📌 *{faq['question']}*\n\n{faq['answer']}", parse_mode="Markdown")
    else:
        await callback.message.answer("Вопрос не найден.")
    await callback.answer()

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Открыть меню", callback_data="open_menu")]
        ]
    )

    await message.answer(
        "ℹ️ <b>О боте</b>\n"
        "Я — крипто-бот, помогаю следить за курсами популярных токенов, строить графики и рассчитывать позиции.\n\n"
        "🚀 <b>Зачем нужен бот?</b>\n"
        "- Быстро узнать текущий курс BTC, ETH, SOL и др.\n"
        "- Построить 7-дневный график цены.\n"
        "- Рассчитать размер позиции и цену ликвидации с любым плечом.\n\n"
        "🧮 <b>Как работает /calc?</b>\n"
        "Отправьте <code>/calc &lt;цена_входа&gt; &lt;плечо&gt; &lt;баланс&gt;</code>:\n"
        "• <b>цена_входа</b> — цена, по которой вы вошли (например, 20000)\n"
        "• <b>плечо</b> — желаемое кредитное плечо (например, 10)\n"
        "• <b>баланс</b> — ваш депозит в USD (например, 100)\n"
        "Бот вернёт размер позиции и цену ликвидации.",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "open_menu")
async def open_menu_callback(callback: CallbackQuery):
    await menu_cmd(callback.message)
    await callback.answer()

@dp.message(Command("chart"))
async def chart_menu(message: types.Message):
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"chart_{token}")]
        for name, token in popular_tokens.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери токен для графика:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("chart_"))
async def send_chart(callback: CallbackQuery):
    token = callback.data.split("_", 1)[1]
    try:
        chart_buf = generate_price_chart(token)
        desc = get_token_description(token)

        photo = BufferedInputFile(chart_buf.read(), filename=f"{token}.png")
        await callback.message.answer_photo(photo=photo, caption=f"📈 График {token.upper()} за 7 дней")
        await callback.message.answer(f"🧾 Описание:\n{desc}")
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении данных: {e}")

@dp.message()
async def echo_handler(message: types.Message):
    text = message.text.lower()
    if text in ['привет', 'приветик', 'hello', 'hi', 'хэлоу']:
        await message.answer("И тебе привет!")
    elif text in ['пока', 'до свидания', 'bye', 'пакеда']:
        await message.answer("До встречи!")
    else:
        await message.answer("Не понял 😅 Напиши /menu для списка команд.")

# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
