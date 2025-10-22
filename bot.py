import os
from dotenv import load_dotenv
import telebot
from googletrans import Translator
from telebot import types
import requests
import threading
import time
import datetime

print(os.environ)

translator = Translator()
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)


# Start
@bot.message_handler(commands=["start"])
def start(message):
    # Создаём клавиатуру с кнопками
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_translate = types.KeyboardButton("Перевести текст")
    btn_weather = types.KeyboardButton("Погода")
    btn_quote = types.KeyboardButton("Цитата дня")
    btn_remind = types.KeyboardButton("Напоминание")
    btn_news = types.KeyboardButton("Новости Израиля")
    btn_currency = types.KeyboardButton("Курс валют 💰")
    btn_help = types.KeyboardButton("Помощь")

    # Добавляем кнопки на клавиатуру
    keyboard.add(
        btn_translate,
        btn_weather,
        btn_quote,
        btn_remind,
        btn_news,
        btn_currency,
        btn_help,
    )

    bot.send_message(
        message.chat.id,
        "Привет! Я твой помощник, выбери действие 👇",
        reply_markup=keyboard,
    )

    # Обработка нажатий кнопок


@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "Перевести текст":
        bot.send_message(message.chat.id, "Отправь текст для перевода...")
    elif message.text == "Погода":
        bot.send_message(message.chat.id, "Введите город для погоды...")
    elif message.text == "Цитата дня":
        bot.send_message(message.chat.id, "Вот твоя цитата на сегодня...")
    elif message.text == "Напоминание":
        bot.send_message(message.chat.id, "Когда и что напомнить?")
    elif message.text == "Новости Израиля":
        bot.send_message(message.chat.id, "Вот последние новости...")
    elif message.text == "Курс валют 💰":
        bot.send_message(message.chat.id, "Курс валют на сегодня...")
    elif message.text == "Помощь":
        bot.send_message(
            message.chat.id, "Я могу помочь с переводом, погодой, новостями и др."
        )
    else:
        bot.send_message(message.chat.id, "Я не понимаю, выбери кнопку 👆")

    # text = (
    #     "Привет! Я твой помощник, вот что я умею 🤖\n"
    #     "/translate – Перевести текст\n"
    #     "/weather – Погода\n"
    #     "/quote – Цитата дня\n"
    #     "/remind – Напоминание\n"
    #     "/news - Новости Израиля\n"
    #     "/currency - Курс валют 💰"
    #     "/help - Помощь\n",
    # )
    # bot.send_message(message.chat.id, text)


# Help
@bot.message_handler(commands=["help"])
def help_command(message):
    help_text = (
        "🤖 Я твой помощник, вот что я умею:\n\n"
        "/translate — Перевести текст на Русский / Английский / Иврит\n"
        "/weather — Узнать погоду (и прогноз) для города\n"
        "/quote — Получить цитату дня\n"
        "/remind — Установить напоминание через N минут\n"
        "/news — Новостями из мира и  Израиля\n"
        "/currency - Посмотреть курс доллара, шекеля и сума 💵\n"
        "/help — Показать это сообщение\n"
    )
    bot.send_message(message.chat.id, help_text)


currency_cache = {"timestamp": None, "data": {"ILS": None, "UZS": None}}


# Currency
@bot.message_handler(commands=["currency"])
def currency(message):
    global currency_cache

    now = datetime.datetime.now()

    # Проверяем — нужно ли обновить (если кеш пустой или старше 24 часов)
    need_update = (
        currency_cache["timestamp"] is None
        or (now - currency_cache["timestamp"]).total_seconds() > 24 * 3600
    )

    if need_update:
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url, timeout=10).json()

            ils = response["rates"].get("ILS")
            uzs = response["rates"].get("UZS")

            if not ils or not uzs:
                bot.send_message(message.chat.id, "Не удалось получить курсы валют 😢")
                return

            currency_cache = {
                "timestamp": now,
                "data": {"ILS": ils, "UZS": uzs},
            }

        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка при обновлении курса валют 😢")
            print("Error /currency:", e)
            return

    ils = currency_cache["data"]["ILS"]
    uzs = currency_cache["data"]["UZS"]
    timestamp = currency_cache["timestamp"]

    text = (
        "💰 <b>Курсы валют (по отношению к доллару):</b>\n\n"
        f"🇮🇱 1 USD = {ils:.2f} ILS\n"
        f"🇺🇿 1 USD = {uzs:,.2f} UZS\n\n"
        f"📅 Обновлено: {timestamp.strftime('%d.%m.%Y %H:%M')}"
    )

    bot.send_message(message.chat.id, text, parse_mode="HTML")


# Функция перевода текста с английского на русский
def translate_to_ru(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "ru", "dt": "t", "q": text}
        response = requests.get(url, params=params, timeout=10)
        result = response.json()[0]
        translated_text = "".join([t[0] for t in result if t[0]])
        return translated_text
    except Exception:
        return text


# news
@bot.message_handler(commands=["news"])
def news(message):
    bot.send_message(message.chat.id, "📰 Подгружаю новости из Израиля...")
    try:
        all_articles = []

        # --- GNews ---
        gnews_url = "https://gnews.io/api/v4/search?q=israel+OR+jerusalem+OR+middle+east&lang=en&max=5&apikey=32a04004804c2be8a16e4521c8d2ecac"
        gresp = requests.get(gnews_url, timeout=10).json()
        g_articles = gresp.get("articles", [])
        for art in g_articles:
            all_articles.append(
                {
                    "title": art.get("title", "Без заголовка"),
                    "description": art.get("description", "Без описания"),
                    "url": art.get("url", ""),
                    "source": art.get("source", {}).get("name", "GNews"),
                }
            )

        # --- NewsAPI ---
        newsapi_url = "https://newsapi.org/v2/top-headlines?country=il&apiKey=eebec6e6245041aa8f288ee502467561&pageSize=5"
        nresp = requests.get(newsapi_url, timeout=10).json()
        n_articles = nresp.get("articles", [])
        for art in n_articles:
            all_articles.append(
                {
                    "title": art.get("title", "Без заголовка"),
                    "description": art.get("description", "Без описания"),
                    "url": art.get("url", ""),
                    "source": art.get("source", {}).get("name", "NewsAPI"),
                }
            )

        # --- Оставляем только 5 ---
        all_articles = all_articles[:5]

        if not all_articles:
            bot.send_message(message.chat.id, "😢 Не удалось получить новости.")
            return

        # --- Отправляем красиво ---
        for art in all_articles:
            title = translate_to_ru(art["title"])
            desc = translate_to_ru(art["description"])
            url = art["url"]
            source = art["source"]

            text = f"📰 <b>{title}</b>\n\n💬 {desc}\n\n📍 Источник: {source}"

            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("📖 Читать полностью", url=url)
            markup.add(btn)

            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup,
                disable_web_page_preview=True,
            )

    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка при получении новостей.")
        print("Error /news:", e)


# Reminder
@bot.message_handler(commands=["remind"])
def remind(message):
    bot.send_message(
        message.chat.id, "🕒 Напиши, через сколько минут напомнить (например: 5): "
    )
    bot.register_next_step_handler(message, get_time)


def get_time(message):
    try:
        minutes = int(message.text)
        bot.send_message(message.chat.id, "✍️ Теперь напиши текст напоминания:")
        bot.register_next_step_handler(message, lambda msg: set_reminder(msg, minutes))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи число, например: 5")


def set_reminder(message, minutes):
    reminder_text = message.text
    bot.send_message(message.chat.id, f"✅ Напоминание: {minutes}")

    def send_reminder():
        time.sleep(minutes * 60)
        bot.send_message(message.chat.id, f"⏰ Напоминание: {reminder_text}")

    threading.Thread(target=send_reminder).start()


# Citate
@bot.message_handler(commands=["remind"])
@bot.message_handler(commands=["quote"])
def quote(message):
    response = requests.get("https://zenquotes.io/api/random").json()
    text = response[0]["q"]
    author = response[0]["a"]

    # translate to russia
    translated_text = translator.translate(text, dest="ru").text
    translated_author = translator.translate(author, dest="ru").text

    bot.send_message(message.chat.id, f"💬 {translated_text}\n- {translated_author}")


# Weather
@bot.message_handler(commands=["weather"])
def weather(message):
    msg = bot.send_message(message.chat.id, "🌆 Напиши город:")
    bot.register_next_step_handler(msg, get_weather)


def get_weather(message):
    city_ru = message.text.strip()
    api_key = "466ee64b8510909cc4e57e39db8c6866"

    # Переводим русский город в английский
    city_en = translator.translate(city_ru, src="ru", dest="en").text

    # Получаем текущую погоду
    url_now = f"http://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={api_key}&units=metric&lang=ru"
    response_now = requests.get(url_now).json()

    # Получаем прогноз на 3 дня
    url_forecast = f"http://api.openweathermap.org/data/2.5/forecast?q={city_en}&appid={api_key}&units=metric&lang=ru"
    response_forecast = requests.get(url_forecast).json()

    if response_now.get("main"):
        temp = response_now["main"]["temp"]
        desc = response_now["weather"][0]["description"]
        emoji = get_weather_emoji(desc)

        text = (
            f"{emoji} В {city_ru} сейчас {temp}°C, {desc}.\n\n📅 Прогноз на три дня:\n"
        )

        # Берём данные каждые 8 интервалов (8×3 = 24 часа)
        for i in range(0, 24, 8):
            day = response_forecast["list"][i]
            date = day["dt_txt"].split(" ")[0]
            temp_day = day["main"]["temp"]
            desc_day = day["weather"][0]["description"]
            emoji_day = get_weather_emoji(desc_day)
            text += f"• {date}: {temp_day}°C, {desc_day} {emoji_day}\n"

        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "❌ Город не найден 😢")


def get_weather_emoji(description):
    description = description.lower()
    if "дожд" in description:
        return "🌧️"
    elif "ясно" in description:
        return "☀️"
    elif "облач" in description:
        return "☁️"
    elif "снег" in description:
        return "❄️"
    elif "гроза" in description:
        return "🌩️"
    else:
        return "🌤️"


# Translator
@bot.message_handler(commands=["translate"])
def translate_text(message):
    # создаем кнопки выбора языка
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("🇷🇺 Русский", "🇬🇧 Английский", "🇮🇱 Иврит")

    msg = bot.send_message(
        message.chat.id,
        "Выбери язык, на который хочешь перевести:",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, select_language)


def select_language(message):
    # logic
    if "Рус" in message.text:
        dest_lang = "ru"
    elif "Англ" in message.text:
        dest_lang = "en"
    elif "Иврит" in message.text:
        dest_lang = "he"
    else:
        bot.send_message(message.chat.id, "Язык не распознан, попробуйте снова.")
        return

    # сохраняем выбор пользователя (в message.chat.id можно хранить состояние)
    bot.send_message(message.chat.id, "Отправь мне текст для перевода:")
    bot.register_next_step_handler(message, handle_translate, dest_lang)


def handle_translate(message, dest_lang):
    text = message.text
    detected_lang = translator.detect(text).lang
    translated = translator.translate(text, dest=dest_lang)

    bot.send_message(
        message.chat.id,
        f"🌍 Определен язык: {detected_lang}\n"
        f"🔁 Перевод на {dest_lang}:\n\n{translated.text}",
        reply_markup=types.ReplyKeyboardRemove(),
    )


print("Бот запущен...")
bot.polling(none_stop=True)
