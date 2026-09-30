import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "8966563925:AAEfgBnZ7Mv90eqXLWViV9GEq2TtDuyxfRk"
ADMIN_CHAT_ID = -1004412941809
CHANNEL_ID = -1004321340609

bot = Bot(token=TOKEN)
dp = Dispatcher()


class Suggestion(StatesGroup):
  waiting_for_content = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
  await message.answer(
      "Привет! 👋 Отправь мне текст, фото или видео, и я передам его на"
      " модерацию админам."
  )
  await state.set_state(Suggestion.waiting_for_content)


@dp.message(Suggestion.waiting_for_content)
async def process_suggestion(message: types.Message, state: FSMContext):
  keyboard = types.InlineKeyboardMarkup(
      inline_keyboard=[
          [
              types.InlineKeyboardButton(
                  text="✅ Опубликовать",
                  callback_data=f"pub_{message.from_user.id}",
              ),
              types.InlineKeyboardButton(
                  text="❌ Отклонить", callback_data="rej"
              ),
          ]
      ]
  )

  await message.forward(chat_id=ADMIN_CHAT_ID)
  await bot.send_message(
      ADMIN_CHAT_ID,
      "📩 Новая предложка от пользователя:",
      reply_markup=keyboard,
  )

  await message.answer(
      "✅ Спасибо! Твоя предложка отправлена на проверку. Если она подойдет,"
      " ее опубликуют в канале."
  )
  await state.clear()


@dp.callback_query(F.data.startswith("pub_"))
async def publish_post(callback: types.CallbackQuery):
  await callback.message.forward(chat_id=CHANNEL_ID)
  await callback.message.edit_text("✅ Пост успешно опубликован в канале!")
  await callback.answer()


@dp.callback_query(F.data == "rej")
async def reject_post(callback: types.CallbackQuery):
  await callback.message.edit_text("❌ Предложка отклонена.")
  await callback.answer()


# --- МИНИ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
  return web.Response(text="Bot is alive!")


async def main():
  logging.basicConfig(level=logging.INFO, stream=sys.stdout)

  # 1. Сначала запускаем веб-сервер, чтобы Render сразу увидел открытый порт
  app = web.Application()
  app.add_routes([web.get("/", handle)])
  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get("PORT", 10000))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()
  logging.info(f"Web server started on port {port}")

  # 2. Затем запускаем самого телеграм-бота
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
