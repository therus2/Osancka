import os
import logging
import uuid
import subprocess
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования для отладки
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Конфигурация под вашу структуру проекта ---
TOKEN = "8064118647:AAFsng1xffS7J-MgsWwVi8wFZo0eqAiLjRY"  # <<< ВСТАВЬТЕ СЮДА ВАШ ТОКЕН

BUTTONS_CONFIG = {
    "Анализ сбоку (Кифоз/Лордоз)": {
        "script": os.path.join("on_side", "on_side.py"),
        "upload_folder": os.path.join("on_side", "side_foto"),
        "result_folder": os.path.join("on_side", "side_result")
    },
    "Анализ со спины (Сколиоз)": {
        "script": os.path.join("beck", "beck.py"),
        "upload_folder": os.path.join("beck", "beck_foto"),
        "result_folder": os.path.join("beck", "beck_result")
    }
}

# Словарь для хранения выбора пользователя {user_id: "название кнопки"}
user_choice = {}


# --- Функции-обработчики ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и показывает кнопки."""
    reply_keyboard = [[btn] for btn in BUTTONS_CONFIG.keys()]
    await update.message.reply_text(
        "👋 Привет! Я бот для анализа осанки.\n\n"
        "Выберите тип анализа, нажав на одну из кнопок ниже, а затем отправьте мне фотографию.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие кнопок и запоминает выбор пользователя."""
    user_id = update.message.from_user.id
    button_text = update.message.text

    if button_text in BUTTONS_CONFIG:
        user_choice[user_id] = button_text
        await update.message.reply_text(
            f"✅ Вы выбрали: *{button_text}*.\n\nТеперь, пожалуйста, отправьте мне фотографию для анализа.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки для выбора анализа.")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает полученную фотографию."""
    user_id = update.message.from_user.id

    if user_id not in user_choice:
        await update.message.reply_text("Сначала, пожалуйста, выберите тип анализа с помощью кнопок.")
        return

    choice = user_choice[user_id]
    config = BUTTONS_CONFIG[choice]

    photo_file = await update.message.photo[-1].get_file()
    unique_filename = f"{uuid.uuid4()}.jpg"

    upload_path = os.path.join(config["upload_folder"], unique_filename)
    result_path = os.path.join(config["result_folder"], unique_filename)

    await photo_file.download_to_drive(upload_path)
    await update.message.reply_text("Фото получено. Начинаю анализ, это может занять несколько секунд...")

    try:
        command = ["python", config["script"], upload_path, result_path]
        subprocess.run(command, check=True, timeout=60)

        await update.message.reply_photo(photo=open(result_path, 'rb'), caption="✅ Анализ завершен! Вот ваш результат.")

    except subprocess.CalledProcessError:
        logger.error(f"Скрипт {config['script']} завершился с ошибкой.")
        await update.message.reply_text(
            "❌ Произошла ошибка во время анализа. Попробуйте другое фото или проверьте логи.")
    except FileNotFoundError:
        logger.error(f"Результат не был создан. Проверьте скрипт {config['script']}.")
        await update.message.reply_text("❌ Не удалось получить результат анализа. Свяжитесь с администратором.")
    except Exception as e:
        logger.error(f"Произошла неизвестная ошибка: {e}")
        await update.message.reply_text("❌ Произошла непредвиденная ошибка.")
    finally:
        if user_id in user_choice:
            del user_choice[user_id]


def main() -> None:
    """Основная функция для запуска бота."""
    for config in BUTTONS_CONFIG.values():
        os.makedirs(config["upload_folder"], exist_ok=True)
        os.makedirs(config["result_folder"], exist_ok=True)

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()