from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
import zoneinfo

from services.users import get_user_by_telegram_id

router = Router()

class TimezoneStates(StatesGroup):
    waiting_for_timezone = State()

@router.message(F.text == "🌍 Часовой пояс")
async def ask_timezone(message: types.Message, state: FSMContext, session: AsyncSession):
    """Запрашивает у пользователя часовой пояс."""
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала выполните /start.")
        return

    # Показываем текущий пояс и список доступных
    zones = sorted(zoneinfo.available_timezones())
    popular = ["Europe/Moscow", "Europe/Kyiv", "Europe/Minsk", "Asia/Almaty", "Asia/Yekaterinburg", "Asia/Novosibirsk", "America/New_York", "America/Los_Angeles", "UTC"]
    
    text = (
        f"🌍 Ваш текущий часовой пояс: <b>{user.timezone}</b>\n\n"
        f"Введите новый часовой пояс (например: <code>Europe/Moscow</code>)\n\n"
        f"Популярные варианты:\n" + "\n".join(f"• <code>{z}</code>" for z in popular if z in zones)
    )
    await message.answer(text)
    await state.set_state(TimezoneStates.waiting_for_timezone)

@router.message(TimezoneStates.waiting_for_timezone)
async def save_timezone(message: types.Message, state: FSMContext, session: AsyncSession):
    """Сохраняет выбранный часовой пояс."""
    tz_name = message.text.strip()
    
    # Проверяем, существует ли такой пояс
    if tz_name not in zoneinfo.available_timezones():
        await message.answer(
            f"❌ Часовой пояс <code>{tz_name}</code> не найден.\n"
            f"Попробуйте еще раз (например: <code>Europe/Moscow</code>):"
        )
        return

    # Обновляем в БД
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if user:
        user.timezone = tz_name
        await session.commit()
        await message.answer(f"✅ Часовой пояс изменен на: <b>{tz_name}</b>")
    else:
        await message.answer("❌ Пользователь не найден.")

    await state.clear()