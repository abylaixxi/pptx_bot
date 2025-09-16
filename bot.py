import os
import io
import logging
import wikipediaapi
from pptx import Presentation
from pptx.util import Inches, Pt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Включаем логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Читаем токен из переменных окружения Railway
TOKEN = os.getenv("TOKEN")

# Настройка Wikipedia API (важно: корректный user_agent!)
wiki = wikipediaapi.Wikipedia(
    language='ru',
    user_agent='AbylaiPresentationBot/1.0 (https://t.me/YourBotUsername; contact: youremail@example.com)'
)

# Создание презентации PowerPoint
def create_pptx(title: str, slides: list[str]) -> io.BytesIO:
    prs = Presentation()
    # Заглавный слайд
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    slide.placeholders[1].text = "Сгенерировано автоматически"

    # Остальные слайды
    for i, text in enumerate(slides, start=1):
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = f"Слайд {i}"
        slide.placeholders[1].text = text

    # Сохраняем в память
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output

# Генерация презентации из Wikipedia
async def generate_presentation(topic: str) -> io.BytesIO:
    page = wiki.page(topic)
    if not page.exists():
        return None

    # Берём первые 8 предложений
    summary = page.summary.split('. ')
    slides = summary[:8] if len(summary) > 8 else summary
    return create_pptx(topic, slides)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне тему, и я сделаю презентацию (.pptx) из Википедии.")

# Генерация презентации по запросу пользователя
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.strip()
    await update.message.reply_text(f"Генерирую презентацию по теме: {topic}...")

    pptx_file = await generate_presentation(topic)
    if pptx_file:
        await update.message.reply_document(
            document=pptx_file,
            filename=f"{topic}.pptx",
            caption=f"Вот презентация по теме: {topic}"
        )
    else:
        await update.message.reply_text("Не удалось найти информацию по этой теме.")

# Точка входа
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Переменная окружения TOKEN не найдена. Укажи её в Railway Variables.")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("presentation", handle_message))
    app.add_handler(CommandHandler("ppt", handle_message))

    # Обработчик всех текстовых сообщений
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен.")
    app.run_polling()
