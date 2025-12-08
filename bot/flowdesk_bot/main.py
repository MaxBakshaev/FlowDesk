import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import httpx

from .config import BOT_TOKEN, N8N_WEBHOOK_URL


class LeadForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот FlowDesk.\n"
        "Команда /lead — создать лида (имя + email), который уйдёт в систему."
    )


@dp.message(Command("lead"))
async def cmd_lead(message: Message, state: FSMContext):
    await state.set_state(LeadForm.waiting_for_name)
    await message.answer("Как вас зовут?")


@dp.message(LeadForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(LeadForm.waiting_for_email)
    await message.answer("Укажите email:")


@dp.message(LeadForm.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip()
    data = await state.get_data()
    name = data.get("name")

    if "@" not in email:
        await message.answer("Это не похоже на email. Попробуйте ещё раз:")
        return

    await state.clear()

    payload = {
        "name": name,
        "email": email,
        "source": "telegram-bot",
    }

    print("N8N_WEBHOOK_URL:", N8N_WEBHOOK_URL)
    print("Payload:", payload)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        await message.answer(
            "Не удалось отправить данные в систему 😔\n" f"Техническая ошибка: {e}"
        )
        return

    await message.answer(
        "Спасибо! Лид создан и отправлен в систему ✅\n"
        "Вы получите ответ, когда менеджер свяжется с вами."
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

# python -m bot.flowdesk_bot.main
