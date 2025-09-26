import os
import logging
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import beck.beck

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8064118647:AAFsng1xffS7J-MgsWwVi8wFZo0eqAiLjRY"

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

# Словарь для хранения выбора пользователя
user_choice = {}

# --- Обработчики ---

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

    # Формируем путь для сохранения фото (совместимый с beck.py)
    upload_path = os.path.abspath(os.path.join("beck", "..", "foto", "rare.jpg"))
    result_path = os.path.abspath(os.path.join("beck", "..", "foto", "resul.jpg"))

    # Логируем текущую рабочую директорию и путь к файлу
    logger.info(f"Текущая рабочая директория: {os.getcwd()}")
    logger.info(f"Сохранение фото в: {upload_path}")

    # Создаем папку foto, если она не существует
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)

    # Загружаем фото
    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(upload_path)
        logger.info(f"Фото успешно сохранено в: {upload_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении фото: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке фото. Попробуйте еще раз.")
        return

    # Проверяем, существует ли файл и доступен ли он
    if not os.path.exists(upload_path):
        logger.error(f"Файл {upload_path} не был создан.")
        await update.message.reply_text("❌ Не удалось сохранить фото. Попробуйте еще раз.")
        return



    await update.message.reply_text("Фото получено. Начинаю анализ, это может занять несколько секунд...")

    try:
        if choice == "Анализ со спины (Сколиоз)":
            # Вызываем beck.beck.main() без аргументов
            beck.beck.main()
            # Ждем результат с таймаутом
            timeout = 30  # секунд
            start_time = time.time()
            while not os.path.exists(result_path):
                if time.time() - start_time > timeout:
                    raise TimeoutError("Превышено время ожидания результата")
                time.sleep(1)

            # Проверяем, существует ли результат
            if os.path.exists(result_path):
                logger.info(f"Результат найден: {result_path}")
                await update.message.reply_photo(
                    photo=open(result_path, 'rb'),
                    caption="✅ Анализ завершен! Вот ваш результат."
                )
            else:
                raise FileNotFoundError(f"Результат не найден: {result_path}")

        elif choice == "Анализ сбоку (Кифоз/Лордоз)":
            await update.message.reply_text("Анализ кифоза/лордоза пока не реализован.")

    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        await update.message.reply_text(
            f"❌ Произошла ошибка во время анализа: {str(e)}. Попробуйте другое фото."
        )
    #finally:
        # Удаляем временные файлы и выбор пользователя
        #if os.path.exists(upload_path):
        #    os.remove(upload_path)
        #    logger.info(f"Файл {upload_path} удален.")
        #if os.path.exists(result_path):
        #    os.remove(result_path)
        #    logger.info(f"Файл {result_path} удален.")
        #if user_id in user_choice:
        #    del user_choice[user_id]

def main() -> None:
    """Основная функция для запуска бота."""
    for config in BUTTONS_CONFIG.values():
        os.makedirs(config["upload_folder"], exist_ok=True)
        os.makedirs(config["result_folder"], exist_ok=True)

    # Логируем начальную рабочую директорию
    logger.info(f"Начальная рабочая директория: {os.getcwd()}")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()