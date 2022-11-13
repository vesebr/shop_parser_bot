import config
import datetime
import asyncio
import aioschedule as schedule
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, filters
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils import executor
from googlesheet_table import GoogleTable
from shop_parser import parse


class TelegramBot(Bot):
    def __init__(
            self,
            token,
            parse_mode,
            google_table=None,
            flag: int = 0,
            flag2: int = 0,
            flag3: int = 0,
            shops=None,
            shop_links=None,
            user_id: str = None,
            user_ids=None,
            row_h: int = 2,
            row_d: int = 2,
            users=None,
    ):
        super().__init__(token, parse_mode=parse_mode)
        if user_ids is None:
            user_ids = []
        if users is None:
            users = {}
        if shop_links is None:
            shop_links = []
        if shops is None:
            shops = {}
        self.users: dict = users
        self._google_table: GoogleTable = google_table
        self.flag: int = flag
        self.flag2: int = flag2
        self.flag3: int = flag3
        self.shops: dict = shops
        self.shop_links: list = shop_links
        self.user_ids: list = user_ids
        self.user_id: str = user_id
        self.row_h: int = row_h
        self.row_d: int = row_d


bot = TelegramBot(
    token=config.settings["TOKEN"],
    parse_mode=types.ParseMode.HTML,
)

dp = Dispatcher(bot)


# bot.users={
#    "user_id": {
#        "shop_links": [shop_url_1, shop_url_2],
#        "sheet_link": google_sheet_url,
#        "shop_name":{
#             "title": "title",
#             "orders": "orders",
#             "reviews": "reviews",
#             "link": "link",
#             }
#        "flag": 0,
#        "flag2": 0,
#        "flag3": 0,
# }


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    button1 = KeyboardButton("Добавить магазин")
    button2 = KeyboardButton("Удалить магазин")
    button3 = KeyboardButton("Добавить таблицу")

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(button1, button2).add(button3)

    bot.user_id = str(message.from_user.id)

    bot.users[str(message.from_user.id)] = {
        "flag": 0,
        "flag2": 0,
        "flag3": 0,
        "row_h": 2,
        "row_d": 2,
        "shop_links": [],
        "shops_list": [],
    }
    bot.user_ids.append(str(message.from_user.id))

    await message.answer("🔹 Вы в главном меню 🔹", reply_markup=keyboard)
    await message.answer("В первую очередь добавьте таблицу для корректной работы", reply_markup=keyboard)


@dp.message_handler(text=["В меню", "Отмена"])
async def cmd_menu(message: types.Message):
    button1 = KeyboardButton("Добавить магазин")
    button2 = KeyboardButton("Удалить магазин")
    button3 = KeyboardButton("Добавить таблицу")

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(button1, button2).add(button3)

    bot.user_id = str(message.from_user.id)

    bot.users[str(message.from_user.id)]["flag"] = 0
    bot.users[str(message.from_user.id)]["flag2"] = 0
    bot.users[str(message.from_user.id)]["flag3"] = 0

    await message.answer("🔹 Вы в главном меню 🔹", reply_markup=keyboard)


@dp.message_handler(text='Добавить таблицу')
async def add_shop(message: Message) -> None:
    bot.user_id = message.from_user.id
    bot.users[str(message.from_user.id)]["flag3"] = 1

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = KeyboardButton("Отмена")
    keyboard.add(menu_button)

    await bot.send_message(message.from_user.id, '🔷 Введите ссылку на таблицу 🔷',  reply_markup=keyboard)


@dp.message_handler(text='Добавить магазин')
async def add_shop(message: Message) -> None:
    bot.users[str(message.from_user.id)]["flag"] = 1
    bot.user_id = message.from_user.id

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = KeyboardButton("Отмена")
    keyboard.add(menu_button)

    await bot.send_message(message.from_user.id, '🔷 Введите ссылку на магазин 🔷', reply_markup=keyboard)


@dp.message_handler(filters.Regexp(regexp=r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$"))
async def collect_first_data(message: Message) -> None:
    if bot.users[str(message.from_user.id)]["flag"] == 1:
        url = str(message.text)
        try:
            info = parse(url)
            bot.users[str(message.from_user.id)][f"{url.split('/')[3]}"] = {
                "title": info["title"],
                "orders": info["orders"],
                "reviews": info["reviews"],
                "link": url,
                'name': str(url.split('/')[3])
            }

            if url not in bot.users[str(message.from_user.id)]['shop_links']:
                bot.users[str(message.from_user.id)]['shop_links'].append(url)
                bot.users[str(message.from_user.id)]["shops_list"].append(
                    {f"{url.split('/')[3]}": bot.users[str(message.from_user.id)][f"{url.split('/')[3]}"]})
            bot.users[str(message.from_user.id)]["flag"] = 0
            await bot.send_message(message.from_user.id, f"✅ Магазин *{info['title']}* успешно добавлен",
                                   parse_mode="Markdown")
        except:
            await bot.send_message(message.from_user.id, "Проверьте правильность ссылки")

    elif bot.users[str(message.from_user.id)]["flag3"] == 1:
        bot.users[str(message.from_user.id)]['sheet_link'] = str(message.text)
        try:
            bot._google_table = GoogleTable("key.json", str(message.text))
            bot._google_table.add_sheet()
            bot._google_table.write_data("A1", "Дата и время", worksheet_title="Заказы за час")
            bot._google_table.write_data("B1", "Название магазина", worksheet_title="Заказы за час")
            bot._google_table.write_data("C1", "Новых заказов", worksheet_title="Заказы за час")
            bot._google_table.write_data("D1", "Новых отзывов", worksheet_title="Заказы за час")
            bot._google_table.write_data("A1", "Дата и время", worksheet_title="Заказы за сутки")
            bot._google_table.write_data("B1", "Название магазина", worksheet_title="Заказы за сутки")
            bot._google_table.write_data("C1", "Новых заказов", worksheet_title="Заказы за сутки")
            bot._google_table.write_data("D1", "Новых отзывов", worksheet_title="Заказы за сутки")
            bot.users[str(message.from_user.id)]["flag3"] = 0
            await bot.send_message(message.from_user.id, "Таблица успешно добавлена")
        except Exception:
            bot._google_table.write_data("A1", "Дата и время", worksheet_title="Заказы за час")
            bot._google_table.write_data("B1", "Название магазина", worksheet_title="Заказы за час")
            bot._google_table.write_data("C1", "Новых заказов", worksheet_title="Заказы за час")
            bot._google_table.write_data("D1", "Новых отзывов", worksheet_title="Заказы за час")
            bot._google_table.write_data("A1", "Дата и время", worksheet_title="Заказы за сутки")
            bot._google_table.write_data("B1", "Название магазина", worksheet_title="Заказы за сутки")
            bot._google_table.write_data("C1", "Новых заказов", worksheet_title="Заказы за сутки")
            bot._google_table.write_data("D1", "Новых отзывов", worksheet_title="Заказы за сутки")
            bot.users[str(message.from_user.id)]["flag3"] = 0
            await bot.send_message(message.from_user.id, "Таблица успешно добавлена")
    else:
        await bot.send_message(message.from_user.id, "Что-то не так")


@dp.message_handler(text='Удалить магазин')
async def remove_shop(message: Message) -> None:
    bot.users[str(message.from_user.id)]["flag2"] = 1
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = KeyboardButton("В меню")
    try:
        for link in bot.users[str(message.from_user.id)]['shop_links']:
            button = KeyboardButton(f"{bot.users[str(message.from_user.id)][link.split('/')[3]]['title']}")
            keyboard.add(button)
        keyboard.add(menu_button)
    except:
        keyboard.add(menu_button)
    await message.answer("🔹 Выберите магазин, который хотите удалить 🔹", reply_markup=keyboard)


@dp.message_handler()
async def remove(message: Message) -> None:
    if bot.users[str(message.from_user.id)]['flag2'] == 1:
        try:
            for item in bot.users[str(message.from_user.id)]['shops_list']:
                for key, value in item.items():
                    if str(message.text) == value['title']:
                        bot.users[str(message.from_user.id)]["shop_links"].remove(value['link'])
                        bot.users[str(message.from_user.id)]["shops_list"].remove({key: value})
                        bot.users[str(message.from_user.id)].pop(key)
            await message.answer(f'Магазин *{message.text}* удален', parse_mode="Markdown")

            bot.users[str(message.from_user.id)]["flag2"] = 0
            await cmd_menu(message)
        except:
            await message.answer('Выберите магазин, который хотите удалить')
    else:
        await answer_other(message)


@dp.message_handler()
async def answer_other(message: Message) -> None:
    await message.answer('Я понимаю только заданные команды')


async def send_hour():
    for id_ in bot.user_ids:
        text = ''
        for link in bot.users[id_]['shop_links']:
            info = parse(link)
            text_part = f'🔻Магазин *{bot.users[id_][link.split("/")[3]]["title"]}*\n\nВсего заказов: *{info["orders"]}*\nВсего отзывов: *{info["reviews"]}*\n\n    ❕Новых заказов: *{info["orders"] - bot.users[id_][link.split("/")[3]]["orders"]}*\n    ❕Новых отзывов: *{info["reviews"] - bot.users[id_][link.split("/")[3]]["reviews"]}*\n\n'
            text += text_part
        text += f"✅Часовой отчет✅\nВремя выгрузки: *{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*"
        await write_cells_h(worksheet_title="Заказы за час", user_id=id_)
        await bot.send_message(id_, text, parse_mode="Markdown")


async def send_day():
    for id_ in bot.user_ids:
        text = ''
        for link in bot.users[id_]['shop_links']:
            info = parse(link)
            text_part = f'🔻Магазин *{bot.users[id_][link.split("/")[3]]["title"]}*\n\nВсего заказов: *{info["orders"]}*\nВсего отзывов: *{info["reviews"]}*\n\n    ❕Новых заказов: *{info["orders"] - bot.users[id_][link.split("/")[3]]["orders"]}*\n    ❕Новых отзывов: *{info["reviews"] - bot.users[id_][link.split("/")[3]]["reviews"]}*\n\n'
            text += text_part
        text += f"✅Дневной отчет✅\nВремя выгрузки: *{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*"
        await write_cells_d(worksheet_title="Заказы за сутки", user_id=id_)
        await bot.send_message(id_, text, parse_mode="Markdown")


async def write_cells_h(worksheet_title: str, user_id) -> None:
    bot._google_table = GoogleTable("key.json", bot.users[user_id]['sheet_link'])
    for link in bot.users[user_id]['shop_links']:
        info = parse(link)
        bot._google_table.write_data(f"A{str(bot.users[user_id]['row_h'])}",
                                     f"{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                                     worksheet_title=worksheet_title)
        bot._google_table.write_data(f"B{str(bot.users[user_id]['row_h'])}", f"{bot.users[user_id][link.split('/')[3]]['title']}",
                                     worksheet_title=worksheet_title)
        bot._google_table.write_data(f"C{str(bot.users[user_id]['row_h'])}",
                                     f"{info['orders'] - bot.users[user_id][link.split('/')[3]]['orders']}",
                                     worksheet_title=worksheet_title)
        bot._google_table.write_data(f"D{str(bot.users[user_id]['row_h'])}",
                                     f"{info['reviews'] - bot.users[user_id][link.split('/')[3]]['reviews']}",
                                     worksheet_title=worksheet_title)
        bot.users[user_id]['row_h'] += 1


async def write_cells_d(worksheet_title: str, user_id) -> None:
    bot._google_table = GoogleTable("key.json", bot.users[user_id]['sheet_link'])
    for link in bot.users[user_id]['shop_links']:
        info = parse(link)
        bot._google_table.write_data(f"A{str(bot.users[user_id]['row_d'])}",
                                     f"{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                                     worksheet_title=worksheet_title)
        bot._google_table.write_data(f"B{str(bot.users[user_id]['row_d'])}", f"{bot.users[user_id][link.split('/')[3]]['title']}",
                                     worksheet_title=worksheet_title)
        bot._google_table.write_data(f"C{str(bot.users[user_id]['row_d'])}",
                                     f"{info['orders'] - bot.users[user_id][link.split('/')[3]]['orders']}",
                                     worksheet_title=worksheet_title)
        bot._google_table.write_data(f"D{str(bot.users[user_id]['row_d'])}",
                                     f"{info['reviews'] - bot.users[user_id][link.split('/')[3]]['reviews']}",
                                     worksheet_title=worksheet_title)
        bot.users[user_id]['row_d'] += 1


async def scheduler():
    schedule.every().day.at("00:00").do(send_hour)
    schedule.every().day.at("00:00").do(send_day)
    schedule.every().day.at("01:00").do(send_hour)
    schedule.every().day.at("02:00").do(send_hour)
    schedule.every().day.at("03:00").do(send_hour)
    schedule.every().day.at("04:00").do(send_hour)
    schedule.every().day.at("05:00").do(send_hour)
    schedule.every().day.at("06:00").do(send_hour)
    schedule.every().day.at("07:00").do(send_hour)
    schedule.every().day.at("08:00").do(send_hour)
    schedule.every().day.at("09:00").do(send_hour)
    schedule.every().day.at("10:00").do(send_hour)
    schedule.every().day.at("11:00").do(send_hour)
    schedule.every().day.at("12:00").do(send_hour)
    schedule.every().day.at("13:00").do(send_hour)
    schedule.every().day.at("14:00").do(send_hour)
    schedule.every().day.at("15:00").do(send_hour)
    schedule.every().day.at("16:00").do(send_hour)
    schedule.every().day.at("17:00").do(send_hour)
    schedule.every().day.at("18:00").do(send_hour)
    schedule.every().day.at("19:00").do(send_hour)
    schedule.every().day.at("20:00").do(send_hour)
    schedule.every().day.at("21:00").do(send_hour)
    schedule.every().day.at("22:00").do(send_hour)
    schedule.every().day.at("23:00").do(send_hour)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(0.2)


async def on_startup(s):
    asyncio.create_task(scheduler())


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
