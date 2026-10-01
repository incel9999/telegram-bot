import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8966563925:AAFVyRch533cPFAJ3_IFeR_2-MXZGt9xTpI"
ADMIN_CHAT_ID = -1004412941809
CHANNEL_ID = -1004321340609

# --- ТВОИ ССЫЛКИ ДЛЯ ТЕКСТА В ПОСТЕ ---
URL_NAVIGATOR = "https://t.me/podslushkaumsf"
URL_CHAT = "https://t.me/+Ke9d8wUtJD1hM2Zi"
URL_RULES = "https://t.me/c/4321340609/6"
URL_BOT = "https://t.me/project121212_bot"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Suggestion(StatesGroup):
    waiting_for_content = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💬 Чат", url=URL_CHAT),
        types.InlineKeyboardButton(text="📜 Правила", url=URL_RULES),
    )
    builder.row(
        types.InlineKeyboardButton(text="🔀 Переходник", url=URL_NAVIGATOR),
    )
    builder.row(
        types.InlineKeyboardButton(text="📥 Предложить пост", callback_data="start_suggest")
    )

    await message.answer("Меню навигации:", reply_markup=builder.as_markup())
    await state.set_state(Suggestion.waiting_for_content)

@dp.callback_query(F.data == "start_suggest")
async def callback_start_suggest(callback: types.CallbackQuery):
    await callback.message.answer("Отправляй пост (текст, фото или видео):")
    await callback.answer()

@dp.message(Suggestion.waiting_for_content)
async def process_suggestion(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Опубликовать", callback_data="pub"),
                types.InlineKeyboardButton(text="❌ Отклонить", callback_data="rej"),
            ]
        ]
    )

    forwarded_msg = await message.forward(chat_id=ADMIN_CHAT_ID)
    
    await bot.send_message(
        ADMIN_CHAT_ID,
        "📩 Новая предложка:",
        reply_markup=keyboard,
        reply_to_message_id=forwarded_msg.message_id
    )

    await message.answer("✅ Отправлено на проверку.")

@dp.callback_query(F.data == "pub")
async def publish_post(callback: types.CallbackQuery):
    if callback.message.reply_to_message:
        original_msg = callback.message.reply_to_message
        
        # Ссылки текстом через разделители в самом низу поста
        links_text = (
            f"\n\n<a href='{URL_NAVIGATOR}'>Переходник</a> | "
            f"<a href='{URL_CHAT}'>Чат</a> | "
            f"<a href='{URL_RULES}'>Инфо</a>\n"
            f"<a href='{URL_BOT}'>Предложить пост</a>"
        )

        text = original_msg.html_text or ""
        final_text = text + links_text

        if original_msg.photo:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=original_msg.photo[-1].file_id,
                caption=final_text,
                parse_mode="HTML"
            )
        elif original_msg.video:
            await bot.send_video(
                chat_id=CHANNEL_ID,
                video=original_msg.video.file_id,
                caption=final_text,
                parse_mode="HTML"
            )
        elif original_msg.text:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=final_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        else:
            await bot.copy_message(chat_id=CHANNEL_ID, from_chat_id=original_msg.chat.id, message_id=original_msg.message_id)
            await bot.send_message(chat_id=CHANNEL_ID, text=links_text.strip(), parse_mode="HTML", disable_web_page_preview=True)
        
    await callback.message.edit_text("✅ Опубликовано в канале!")
    await callback.answer()

@dp.callback_query(F.data == "rej")
async def reject_post(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Отклонено.")
    await callback.answer()

# --- МИНИ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
