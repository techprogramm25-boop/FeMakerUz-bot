import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# LOGGING - Railway loglarida xatolarni ko'rish uchun
logging.basicConfig(level=logging.INFO)

# SOZLAMALAR
TOKEN = "8745370830:AAHZqC-2Llh78Jgll9YdHyhOrLOImzgrb9c"
CHANNEL_ID = "@MadinaBonuKiloKIyimlar"
YOUTUBE_URL = "https://m.youtube.com/@yusufxonpro"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# BAZA BILAN ISHLASH
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, bot_token TEXT, link TEXT, last_data TEXT)''')
    conn.commit()
    conn.close()

# TUGMALAR
def get_sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Telegram Kanal", url=f"https://t.me/MadinaBonuKiloKIyimlar")],
        [InlineKeyboardButton(text="📺 YouTube Kanal", url=YOUTUBE_URL)],
        [InlineKeyboardButton(text="✅ Obunani Tekshirish", callback_data="check")]
    ])

def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Botni Ulash", callback_data="add_bot")],
        [InlineKeyboardButton(text="🎁 Sovg'a olish", callback_data="gift")]
    ])

# START
@dp.message(CommandStart())
async def cmd_start(message: Message):
    try:
        user_status = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
        if user_status.status in ["member", "administrator", "creator"]:
            await message.answer(f"Xush kelibsiz, {message.from_user.first_name}!\nBu @FeMakerUz_Bot. Botni ulash uchun tugmani bosing:", 
                               reply_markup=get_main_kb())
        else:
            await message.answer("Botdan foydalanish uchun kanallarga obuna bo'ling:", reply_markup=get_sub_kb())
    except Exception as e:
        logging.error(f"Start error: {e}")
        await message.answer("Xatolik! Bot kanalga admin qilinmagan bo'lishi mumkin.")

@dp.callback_query(F.data == "check")
async def check_sub(call: CallbackQuery):
    user_status = await bot.get_chat_member(CHANNEL_ID, call.from_user.id)
    if user_status.status in ["member", "administrator", "creator"]:
        await call.message.edit_text("✅ Tasdiqlandi! Endi botingizni ulashingiz mumkin.", reply_markup=get_main_kb())
    else:
        await call.answer("Obuna bo'lmagansiz! ❌", show_alert=True)

@dp.callback_query(F.data == "add_bot")
async def add_bot_start(call: CallbackQuery):
    await call.message.answer("1. @BotFather dan olgan **Token**ni yuboring:")

@dp.message(F.text.contains(":"))
async def process_token(message: Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, bot_token) VALUES (?, ?)", 
                   (message.from_user.id, message.text))
    conn.commit()
    conn.close()
    await message.answer("✅ Token qabul qilindi! Endi kuzatish kerak bo'lgan sayt yoki profil linkini yuboring:")

@dp.message(F.text.startswith("http"))
async def process_link(message: Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET link=? WHERE user_id=?", (message.text, message.from_user.id))
    conn.commit()
    conn.close()
    await message.answer(f"🚀 Muvaffaqiyatli ulandi!\nManba: {message.text}\n\nReklama: @Yusufxonpro1 tomonidan ulandi.\nBot: @FeMakerUz_Bot")

# FONDA ISHLAYDIGAN MONITORING
async def monitor_system():
    while True:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        users = cursor.execute("SELECT * FROM users WHERE bot_token IS NOT NULL AND link IS NOT NULL").fetchall()
        
        for user_id, token, link, last_data in users:
            try:
                # BU YERDA REAL SCRAPING BO'LADI (Hozircha test xabari)
                current_info = "Yangi yangilik aniqlandi!" 
                
                if current_info != last_data:
                    temp_bot = Bot(token=token)
                    text = (f"📢 **YANGI POST!**\n\n{current_info}\nLink: {link}\n\n"
                            f"✅ @Yusufxonpro1 orqali ulandi\n🤖 @FeMakerUz_Bot")
                    
                    await temp_bot.send_message(user_id, text, parse_mode="Markdown")
                    
                    cursor.execute("UPDATE users SET last_data=? WHERE user_id=?", (current_info, user_id))
                    conn.commit()
                    await temp_bot.session.close()
            except Exception as e:
                logging.error(f"Monitor error for {user_id}: {e}")
        
        conn.close()
        await asyncio.sleep(600) # 10 daqiqada bir tekshirish

async def main():
    init_db()
    asyncio.create_task(monitor_system())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
