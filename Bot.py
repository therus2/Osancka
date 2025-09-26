import asyncio
import os
import logging
import time

import cv2
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import beck.beck
import on_side.on_side

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8064118647:AAFsng1xffS7J-MgsWwVi8wFZo0eqAiLjRY"  # вставь сюда свой токен

BUTTONS_CONFIG = {
    "📏 Анализ со спины (Сколиоз)": {
        "script": beck.beck.main,
        "upload_folder": os.path.join("beck", "beck_foto"),
        "result_folder": os.path.join("beck", "beck_result")
    },
    "🧍 Анализ сбоку (Кифоз/Лордоз)": {
        "script": on_side.on_side.main,
        "upload_folder": os.path.join("on_side", "side_foto"),
        "result_folder": os.path.join("on_side", "side_result")
    }
}

user_choice = {}

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_keyboard = [[btn] for btn in BUTTONS_CONFIG.keys()]
    reply_keyboard.append(["ℹ️ О проекте"])
    await update.message.reply_text(
        "👋 Привет! Я бот для анализа осанки.\n\n"
        "Выбери тип анализа:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    )

# --- Обработка кнопок ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    button_text = update.message.text

    if button_text in BUTTONS_CONFIG:
        user_choice[user_id] = button_text
        await update.message.reply_text(
            f"✅ Ты выбрал: *{button_text}*.\n\n📷 Теперь пришли фото для анализа.",
            parse_mode='Markdown'
        )
    elif button_text == "ℹ️ О проекте":
        await update.message.reply_text(
            "ℹ️ Этот бот использует *MediaPipe* для анализа позы.\n\n"
            "⚠️ Результаты носят ознакомительный характер и не являются медицинским диагнозом.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Пожалуйста, используй кнопки для выбора анализа.")

# --- Обработка фото ---
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_choice:
        await update.message.reply_text("Сначала выбери тип анализа в меню.")
        return

    choice = user_choice[user_id]
    config = BUTTONS_CONFIG[choice]

    filename = f"{user_id}_{int(time.time())}.jpg"
    upload_path = os.path.join(config["upload_folder"], filename)
    result_path = os.path.join(config["result_folder"], f"result_{filename}")

    os.makedirs(config["upload_folder"], exist_ok=True)
    os.makedirs(config["result_folder"], exist_ok=True)

    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(upload_path)
        logger.info(f"Фото сохранено: {upload_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении фото: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке фото. Попробуй ещё раз.")
        return

    await update.message.reply_text("📊 Анализ начался, подожди несколько секунд...")

    try:
        # Запускаем анализ
        result_path, results_text = config["script"](upload_path, result_path)

        # Отправляем картинку
        await update.message.reply_photo(
            photo=open(result_path, "rb"),
            caption="✅ Анализ завершён!"
        )

        # Формируем текстовый отчёт
        report = "📊 *Результаты анализа:*\n\n"

        if "shoulder_angle" in results_text:  # beck.py
            report += f"• Наклон плеч: {results_text['shoulder_angle']}°\n"
            report += f"• Искривление позвоночника: {results_text['spine_angle']}°\n"
            report += f"• Диагноз: *{results_text['diagnosis']}*\n"

        if "back_angle" in results_text:  # on_side.py
            report += f"• Угол спины: {results_text['back_angle']}°\n"
            report += f"• Угол тела: {results_text['body_angle']}°\n"
            report += f"• {results_text['kyphosis']}\n"
            report += f"• {results_text['lordosis']}\n"

        report += "\n⚠️ *Внимание:* результат не является медицинским диагнозом!"

        await update.message.reply_text(report, parse_mode="Markdown")

        # Кнопка для нового анализа
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Новый анализ", callback_data="restart")]]
        )
        await update.message.reply_text("Хочешь попробовать ещё раз?", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        await update.message.reply_text(f"❌ Ошибка во время анализа: {str(e)}")

# --- Inline кнопки ---
async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "restart":
        await start(query, context)

# --- Запуск ---
def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.ALL, start))

    app.run_polling()

if __name__ == "__main__":
    run_bot()
