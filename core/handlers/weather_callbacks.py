# core/handlers/weather_callbacks.py
from aiogram import Router, types
# from core.database.queries_weather import set_weather_subscription, get_user_location
from core.services.weather.service import weather_service

router = Router()

# @router.callback_query(lambda c: c.data and c.data.startswith("weather_sub_on"))
# async def sub_on_cb(cq: types.CallbackQuery):
#     user_id = cq.from_user.id
#     await set_weather_subscription(user_id, True)
#     await cq.answer("✅ Ви підписані на щоденну агропогоду", show_alert=False)
#
#
# @router.callback_query(lambda c: c.data and c.data.startswith("weather_sub_off"))
# async def sub_off_cb(cq: types.CallbackQuery):
#     user_id = cq.from_user.id
#     await set_weather_subscription(user_id, False)
#     await cq.answer("❌ Підписку вимкнено", show_alert=False)
#
#
# @router.callback_query(lambda c: c.data and c.data.startswith("weather_change"))
# async def change_loc_cb(cq: types.CallbackQuery):
#     await cq.message.answer("Введіть назву нового регіону:")
#     await cq.answer()
