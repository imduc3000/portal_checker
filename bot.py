from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os
from dotenv import load_dotenv

load_dotenv()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['Gửi ảnh 📸', 'Gửi nhạc 🎵'],
        ['Thông tin ℹ️', 'Hỗ trợ 🆘']
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f'Chào {update.effective_user.first_name}, hãy chọn một tính năng bên dưới:', 
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text

    if msg == 'Gửi ảnh 📸':
        await update.message.reply_text('Đang tìm ảnh đẹp cho bạn đây...')

        await context.bot.send_photo(
            chat_id= update.effective_chat.id,
            photo= 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1024px-Telegram_logo.svg.png',
            caption= 'Đây là logo của Telegram nha!'
        )
    if msg == 'Gửi nhạc 🎵':
        await update.message.reply_text('Sắp có nhạc hay cho bạn nghe đây!')

        await context.bot.send_audio (
            chat_id= update.effective_chat.id,
            audio= 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'
        )
    else:
        await update.message.reply_text(f'Bạn vừa nhắn: {msg}')


async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    option = [
        [InlineKeyboardButton(text="google", url="https://google.com")]
    ]

    reply_markup = InlineKeyboardMarkup(option)

    await update.message.reply_text(
        "Mời bạn ghé thăm Google",
        reply_markup= reply_markup
    )
    

if __name__ == '__main__':
    # Load token từ .env file (KHÔNG hardcode!)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in .env file!")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("web", website))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))



    app.run_polling()


