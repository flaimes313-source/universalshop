from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import ADMIN_ID
from database.models import User

router = Router()

@router.callback_query(F.data == "admin_customers")
async def list_customers(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список клиентов."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    result = await session.execute(select(User).order_by(User.created_at.desc()).limit(50))
    users = result.scalars().all()

    if not users:
        await callback.message.edit_text(
            "👥 Клиентов пока нет.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
            ])
        )
        await callback.answer()
        return

    text = "👥 <b>Последние клиенты:</b>\n\n"
    for u in users:
        name = u.full_name or "Без имени"
        phone = u.phone or "не указан"
        text += f"• {name} | Тел: {phone} | ID: <code>{u.id}</code>\n"

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()