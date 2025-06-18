import logging
import gspread
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from google.oauth2.service_account import Credentials

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
CATEGORIES = [
    "Каркас здания", "Устройство пола", "Кирпичная кладка", "Монтаж лифта", "Отделка",
    "ОВ ВК", "Монтаж оконных проемов", "Монтаж металлоконструкции", "Кровля",
    "Фасад", "Электрооборудования", "Система связи",
    "Оператор автокрана", "Оператор петушок", "Оператор экскаватора/погрузчика",
    "Петушок", "Автокран", "Экскаватор", "Самосвал"
]
MAX_VALUES = {
    "Каркас здания": 3, "Устройство пола": 2, "Кирпичная кладка": 10, "Монтаж лифта": 4,
    "Отделка": 8, "ОВ ВК": 7, "Монтаж оконных проемов": 2, "Монтаж металлоконструкции": 7,
    "Кровля": 6, "Фасад": 6, "Электрооборудования": 4, "Система связи": 6,
    "Оператор автокрана": 2, "Оператор петушок": 1, "Оператор экскаватора/погрузчика": 2,
    "Петушок": 1, "Автокран": 3, "Экскаватор": 1, "Самосвал": 1
}
STATE_INDEX = 0

# Connect to Google Sheets
SHEET_ID = '1C_1Oj04hYwX0pRrbycfc6DfyovEJmhKPQLVEuiPUmv4'  # Replace this!
RANGE_NAME = 'Sheet1'  # or change if needed
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
gc = gspread.authorize(creds)
worksheet = gc.open_by_key(SHEET_ID).worksheet(RANGE_NAME)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['index'] = 0
    await update.message.reply_text(f"Введите количество для: {CATEGORIES[0]} (макс. {MAX_VALUES[CATEGORIES[0]]})")
    return STATE_INDEX

# Handle category inputs
async def collect_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data.get('index', 0)
    try:
        val = int(update.message.text)
        max_val = MAX_VALUES[CATEGORIES[index]]
        if 0 <= val <= max_val:
            context.user_data[CATEGORIES[index]] = val
        else:
            await update.message.reply_text(f"❗ Введите число от 0 до {max_val} для {CATEGORIES[index]}.")
            return STATE_INDEX
    except ValueError:
        await update.message.reply_text("❗ Пожалуйста, введите целое число.")
        return STATE_INDEX

    index += 1
    if index < len(CATEGORIES):
        context.user_data['index'] = index
        await update.message.reply_text(f"Введите количество для: {CATEGORIES[index]} (макс. {MAX_VALUES[CATEGORIES[index]]})")
        return STATE_INDEX
    else:
        # Prepare data
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [now] + [context.user_data.get(cat, 0) for cat in CATEGORIES]
        worksheet.append_row(row)
        summary = "📋 Отчёт по рабочим:\n" + "\n".join([f"{cat}: {context.user_data.get(cat, 0)}" for cat in CATEGORIES])
        await update.message.reply_text(summary + "\n✅ Спасибо! Данные сохранены в Google Sheets.")
        return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ввод отменён.")
    return ConversationHandler.END

# Bot token and application run
if __name__ == '__main__':
    application = ApplicationBuilder().token("7531600122:AAEXTeFsMXb8pkjbGLfj5YNghgRgD5VHGkI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={STATE_INDEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_input)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()
