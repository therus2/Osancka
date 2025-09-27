import asyncio
import os
import logging
import time

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

import beck.beck
import on_side.on_side

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8064118647:AAFsng1xffS7J-MgsWwVi8wFZo0eqAiLjRY"  # 🔴 замени на свой токен

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
            f"✅ Ты выбрал: *{button_text}*.\n\n📷 Теперь пришли фото для анализа.\n Фото должно быть сделано при хорошем освещении(можно со всыпшкой) и с монотонным фоном",
            parse_mode='Markdown'
        )
    elif button_text == "ℹ️ О проекте":
        about_text = (
            "ℹ️ *О проекте*\n\n"
            "Наш бот создан, чтобы помочь выявлять изменения осанки на ранних стадиях, "
            "поскольку искривления позвоночника сегодня очень распространены среди подростков "
            "из-за малоподвижного образа жизни и долгого сидения.\n\n"
            "📊 *Некоторые факты:*\n"
            "• Около *3,1 %* детей и подростков имеют сколиоз по данным крупных исследований.\n"
            "• В подростковом возрасте (11–18 лет) в разных регионах выявляют *0,6–5,7 %* случаев, "
            "особенно у школьников старших классов.\n"
            "• У девочек риск сколиоза примерно в *3 раза выше*, чем у мальчиков.\n"
            "• Подростки *высокого роста и худощавого телосложения чаще подвержены искривлениям*, "
            "чем невысокие сверстники.\n"
            "• Сидячий образ жизни (учёба, гаджеты, игры) усиливает риск нарушений осанки.\n\n"
            "🔍 *Почему это важно:*\n"
            "• Раннее выявление позволяет начать профилактику и упражнения, "
            "что снижает риск болей, прогрессирования искривлений и проблем с дыханием.\n"
            "• Чем раньше начато вмешательство, тем выше шанс скорректировать осанку "
            "и избежать серьёзного лечения.\n\n"
            "⚠️ Результаты анализа бота носят ознакомительный характер "
            "и *не являются медицинским диагнозом*. "
            "Если есть подозрения на искривление — обратитесь к специалисту."
        )
        await update.message.reply_text(about_text, parse_mode="Markdown")
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
        # Загружаем фото
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(upload_path)
        logger.info(f"Фото сохранено: {upload_path}")

        await update.message.reply_text("📊 Анализ начался, подожди несколько секунд...")

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

        # Базовое предупреждение
        report += "\n⚠️ *Внимание:* результат не является медицинским диагнозом!"

        # Добавляем рекомендацию при отклонениях
        if "diagnosis" in results_text and results_text["diagnosis"] != "Норма":
            report += "\n\n🩺 *Советуем обратиться к врачу для получения профессиональной помощи!*"

        if "kyphosis" in results_text and "Норма" not in results_text["kyphosis"]:
            report += "\n\n🩺 *Советуем обратиться к врачу для получения профессиональной помощи!*"

        if "lordosis" in results_text and "Норма" not in results_text["lordosis"]:
            report += "\n\n🩺 *Советуем обратиться к врачу для получения профессиональной помощи!*"

        await update.message.reply_text(report, parse_mode="Markdown")

        # Кнопки после анализа
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Новый анализ", callback_data="restart")],
            [InlineKeyboardButton("🏋️ Профилактические упражнения", callback_data="exercises")]
        ])
        await update.message.reply_text("Что хочешь сделать дальше?", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        await update.message.reply_text(f"❌ Ошибка во время анализа: {str(e)}")

    finally:
        # Удаляем временные файлы
        for path in [upload_path, result_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.info(f"Файл удалён: {path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить {path}: {e}")

# --- Inline кнопки ---
async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "restart":
        await start(query, context)

    elif query.data == "exercises":
        exercises = [
            {
                "file": "exercises/plank.jpg",
                "caption": "1️⃣ *Планка*\nДержите тело прямым 30–60 секунд. 3 подхода."
            },
            {
                "file": "exercises/superman.jpg",
                "caption": "2️⃣ *Супермен*\nЛягте на живот, поднимайте руки и ноги одновременно. 3×15."
            },
            {
                "file": "exercises/stretch.jpg",
                "caption": "3️⃣ *Растяжка грудных мышц*\nВстаньте у стены, тяните грудь вперёд. 20–30 секунд."
            },
            {
                "file": "exercises/rows.jpeg",
                "caption": "4️⃣ *Тяга эспандера*\nТяните резинку к груди сидя. 3×15 повторений."
            },
            {
                "file": "exercises/catcow.jpg",
                "caption": "5️⃣ *Кошка–Корова*\nЧередуйте прогиб и округление спины. 1–2 минуты."
            }
        ]

        for ex in exercises:
            try:
                if os.path.exists(ex["file"]):
                    with open(ex["file"], "rb") as img:
                        await query.message.reply_photo(
                            photo=img,
                            caption=ex["caption"],
                            parse_mode="Markdown"
                        )
                else:
                    await query.message.reply_text(ex["caption"], parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Не удалось отправить упражнение {ex['file']}: {e}")

        # Итоговое предупреждение
        await query.message.reply_text(
            "⚠️ Выполняйте упражнения регулярно для укрепления спины.\n"
            "Если появляются боли — обязательно обратитесь к врачу!",
            parse_mode="Markdown"
        )

# --- Запуск ---
def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(inline_handler))

    app.run_polling()

if __name__ == "__main__":
    run_bot()
