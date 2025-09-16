import logging
import wikipediaapi
from pptx import Presentation
from pptx.util import Inches
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import tempfile
import os
from dotenv import load_dotenv

# Загружаем переменные окружения (локально для тестов, Railway использует свои)
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Wikipedia API (русский)
wiki = wikipediaapi.Wikipedia('ru')

def create_presentation(topic: str, slides_count: int = 8) -> str:
    """Создает презентацию по теме."""
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    # Заголовок
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = topic
    slide.placeholders[1].text = "Автоматически создано ботом"

    # Данные из Wikipedia
    page = wiki.page(topic)
    if not page.exists():
        return None

    paragraphs = page.summary.split('. ')
    chunks = [paragraphs[i:i + 3] for i in range(0, len(paragraphs), 3)]

    for i in range(slides_count - 1):
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = f"{topic} — часть {i+1}"
        text = '. '.join(chunks[i]) if i < len(chunks) else "Нет дополнительной информации."
        slide.placeholders[1].text = text

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
        prs.save(tmp.name)
        return tmp.name

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для создания презентаций.\n"
        "Использование: /make <тема> [кол-во слайдов]\n"
        "Пример: /make Французская революция 8"
    )

async def make(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи тему. Пример: /make Французская революция 8")
        return

    try:
        slides_count = int(context.args[-1])
        topic = ' '.join(context.args[:-1])
    except ValueError:
        slides_count = 8
        topic = ' '.join(context.args)

    await update.message.reply_text(f"Создаю презентацию по теме: {topic} ({slides_count} слайдов)...")

    pptx_path = create_presentation(topic, slides_count)
    if pptx_path is None:
        await update.message.reply_text("Не удалось найти информацию по этой теме.")
        return

    with open(pptx_path, 'rb') as file:
        await update.message.reply_document(document=file, filename=f"{topic}.pptx")

    os.remove(pptx_path)

def main():
    if not TOKEN:
        raise ValueError("Токен не найден. Установи переменную окружения TOKEN.")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("make", make))
    app.run_polling()

if __name__ == "__main__":
    main()
