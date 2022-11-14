import json

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
            password: str = '57526748',  # '57526748',
            has_access: bool = False,
            user_list=None
    ):
        super().__init__(token, parse_mode=parse_mode)
        if user_list is None:
            user_list = []
        self.user_list: list = user_list
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
        self.password: str = password
        self.has_access: bool = has_access


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
    bot.users[str(message.from_user.id)] = {
        "access": bot.has_access
    }
    if not bot.users[str(message.from_user.id)]["access"]:
        await message.answer("Введите пароль")


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
async def add_table(message: Message) -> None:
    bot.user_id = message.from_user.id
    bot.users[str(message.from_user.id)]["flag3"] = 1

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = KeyboardButton("Отмена")
    keyboard.add(menu_button)

    await bot.send_message(message.from_user.id, '🔷 Введите ссылку на таблицу 🔷', reply_markup=keyboard)


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
            await cmd_menu(message)
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
    if not bot.users[str(message.from_user.id)]['access']:
        if str(message.text) == bot.password:
            button1 = KeyboardButton("Добавить магазин")
            button2 = KeyboardButton("Удалить магазин")
            button3 = KeyboardButton("Добавить таблицу")

            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.row(button1, button2).add(button3)

            bot.user_id = str(message.from_user.id)
            try:
                with open('users_ifo.json', 'r', encoding='utf8') as f:
                    user_list = json.load(f)
                check = 0
                for i in user_list:
                    for key, value in i.items():
                        if key == str(message.from_user.id):
                            check = 1
                if check:
                    for i in user_list:
                        for key, value in i.items():
                            if key == str(message.from_user.id):
                                bot.users[str(message.from_user.id)] = i[key]
                                if str(message.from_user.id) not in bot.user_ids:
                                    bot.user_ids.append(str(message.from_user.id))
                    await message.answer("🔹 Вы в главном меню 🔹", reply_markup=keyboard)
                    await message.answer("Ваши данные загружены",
                                         reply_markup=keyboard)
                else:
                    bot.users[str(message.from_user.id)] = {
                        "flag": 0,
                        "flag2": 0,
                        "flag3": 0,
                        "row_h": 2,
                        "row_d": 2,
                        "shop_links": [],
                        "shops_list": [],
                        "access": True,
                    }
                    if str(message.from_user.id) not in bot.user_ids:
                        bot.user_ids.append(str(message.from_user.id))
                    await message.answer("🔹 Вы в главном меню 🔹", reply_markup=keyboard)
                    await message.answer("В первую очередь добавьте таблицу для корректной работы",
                                         reply_markup=keyboard)
            except:
                bot.users[str(message.from_user.id)] = {
                    "flag": 0,
                    "flag2": 0,
                    "flag3": 0,
                    "row_h": 2,
                    "row_d": 2,
                    "shop_links": [],
                    "shops_list": [],
                    "access": True,
                }
                if str(message.from_user.id) not in bot.user_ids:
                    bot.user_ids.append(str(message.from_user.id))

                await message.answer("🔹 Вы в главном меню 🔹", reply_markup=keyboard)
                await message.answer("В первую очередь добавьте таблицу для корректной работы", reply_markup=keyboard)
        else:
            await message.answer("Введен неверный пароль")
    else:
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
    bot.user_list = []
    for id_ in bot.user_ids:
            bot.user_list.append({id_: bot.users[id_]})
            if bot.users[str(id_)]['sheet_link']:
                await write_cells_h(worksheet_title="Заказы за час", user_id=id_)
                with open("users_ifo.json", "w", encoding="utf8") as f:
                    json.dump(bot.user_list, f, sort_keys=False, indent=4, ensure_ascii=False)
            else:
                await bot.send_message(id_, "Вы не добавили таблицу")

            if len(bot.users[id_]['shop_links']) != 0:
                for link in bot.users[id_]['shop_links']:
                    info = parse(link)
                    await bot.send_message(id_,
                                           text=f'🔻Магазин *{bot.users[id_][link.split("/")[3]]["title"]}*\n\nВсего заказов: *{info["orders"]}*\nВсего отзывов: *{info["reviews"]}*\n\n    ❕Новых заказов: *{info["orders"] - bot.users[id_][link.split("/")[3]]["orders"]}*\n    ❕Новых отзывов: *{info["reviews"] - bot.users[id_][link.split("/")[3]]["reviews"]}*\n\n',
                                           parse_mode="Markdown")
                await bot.send_message(id_,
                                       text=f"✅Часовой отчет✅\nВремя выгрузки: *{datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}:00*",
                                       parse_mode="Markdown")

            else:
                await bot.send_message(id_, "Вы не добавили магазины")


async def send_day():
    bot.user_list = []
    for id_ in bot.user_ids:
        bot.user_list.append({id_: bot.users[id_]})
        if bot.users[str(id_)]['sheet_link']:
            await write_cells_d(worksheet_title="Заказы за сутки", user_id=id_)
            with open("users_ifo.json", "w", encoding="utf8") as f:
                json.dump(bot.user_list, f, sort_keys=False, indent=4, ensure_ascii=False)
        else:
            await bot.send_message(id_, "Вы не добавили таблицу")

        if len(bot.users[id_]['shop_links']) != 0:
            for link in bot.users[id_]['shop_links']:
                info = parse(link)
                await bot.send_message(id_,
                                       text=f'🔻Магазин *{bot.users[id_][link.split("/")[3]]["title"]}*\n\nВсего заказов: *{info["orders"]}*\nВсего отзывов: *{info["reviews"]}*\n\n    ❕Новых заказов: *{info["orders"] - bot.users[id_][link.split("/")[3]]["orders"]}*\n    ❕Новых отзывов: *{info["reviews"] - bot.users[id_][link.split("/")[3]]["reviews"]}*\n\n',
                                       parse_mode="Markdown")
            await bot.send_message(id_,
                                   text=f"✅Дневной отчет✅\nВремя выгрузки: *{datetime.datetime.now().strftime('%d.%m.%Y %H')}:00:00*",
                                   parse_mode="Markdown")
        else:
            await bot.send_message(id_, "Вы не добавили магазины")


async def write_cells_h(worksheet_title: str, user_id) -> None:
    bot._google_table = GoogleTable("key.json", bot.users[user_id]['sheet_link'])

    bot._google_table.write_cells(
        crange=f'A{str(bot.users[user_id]["row_h"])}:A{str(bot.users[user_id]["row_h"] + len(bot.users[user_id]["list_time"]))}',
        values=bot.users[user_id]["list_time"], worksheet_title=worksheet_title)
    bot._google_table.write_cells(
        crange=f'B{str(bot.users[user_id]["row_h"])}:B{str(bot.users[user_id]["row_h"] + len(bot.users[user_id]["list_titles"]))}',
        values=bot.users[user_id]["list_titles"], worksheet_title=worksheet_title)
    bot._google_table.write_cells(
        crange=f'C{str(bot.users[user_id]["row_h"])}:C{str(bot.users[user_id]["row_h"] + len(bot.users[user_id]["list_orders"]))}',
        values=bot.users[user_id]["list_orders"], worksheet_title=worksheet_title)
    bot._google_table.write_cells(
        crange=f'D{str(bot.users[user_id]["row_h"])}:D{str(bot.users[user_id]["row_h"] + len(bot.users[user_id]["list_reviews"]))}',
        values=bot.users[user_id]["list_reviews"], worksheet_title=worksheet_title)
    bot.users[user_id]['row_h'] += len(bot.users[user_id]["list_reviews"])


async def write_cells_d(worksheet_title: str, user_id):
    bot._google_table = GoogleTable("key.json", bot.users[user_id]['sheet_link'])

    bot._google_table.write_cells(
        crange=f'A{str(bot.users[user_id]["row_d"])}:A{str(bot.users[user_id]["row_d"] + len(bot.users[user_id]["list_time"]))}',
        values=bot.users[user_id]["list_time"], worksheet_title=worksheet_title)
    bot._google_table.write_cells(
        crange=f'B{str(bot.users[user_id]["row_d"])}:B{str(bot.users[user_id]["row_d"] + len(bot.users[user_id]["list_titles"]))}',
        values=bot.users[user_id]["list_titles"], worksheet_title=worksheet_title)
    bot._google_table.write_cells(
        crange=f'C{str(bot.users[user_id]["row_d"])}:C{str(bot.users[user_id]["row_d"] + len(bot.users[user_id]["list_orders"]))}',
        values=bot.users[user_id]["list_orders"], worksheet_title=worksheet_title)
    bot._google_table.write_cells(
        crange=f'D{str(bot.users[user_id]["row_d"])}:D{str(bot.users[user_id]["row_d"] + len(bot.users[user_id]["list_reviews"]))}',
        values=bot.users[user_id]["list_reviews"], worksheet_title=worksheet_title)
    bot.users[user_id]['row_d'] += len(bot.users[user_id]["list_reviews"])


async def collect_data_h():
    for id_ in bot.user_ids:
        bot.users[id_]["list_time"] = []
        bot.users[id_]["list_titles"] = []
        bot.users[id_]["list_orders"] = []
        bot.users[id_]["list_reviews"] = []
        for link in bot.users[id_]['shop_links']:
            info = parse(link)
            bot.users[id_]["list_time"].append([str(datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=4, minutes=1))).strftime('%d.%m.%Y %H:%M')) + ':00'])
            bot.users[id_]["list_titles"].append([info['title']])
            bot.users[id_]["list_orders"].append([info['orders'] - bot.users[id_][link.split('/')[3]]['orders']])
            bot.users[id_]["list_reviews"].append([info['reviews'] - bot.users[id_][link.split('/')[3]]['reviews']])


async def collect_data_d():
    for id_ in bot.user_ids:
        bot.users[id_]["list_time"] = []
        bot.users[id_]["list_titles"] = []
        bot.users[id_]["list_orders"] = []
        bot.users[id_]["list_reviews"] = []
        for link in bot.users[id_]['shop_links']:
            info = parse(link)
            bot.users[id_]["list_time"].append([str(datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=4, minutes=1))).strftime('%d.%m.%Y %H:%M')) + ':00'])
            bot.users[id_]["list_titles"].append([info['title']])
            bot.users[id_]["list_orders"].append([info['orders'] - bot.users[id_][link.split('/')[3]]['orders']])
            bot.users[id_]["list_reviews"].append([info['reviews'] - bot.users[id_][link.split('/')[3]]['reviews']])


async def scheduler():
    schedule.every().day.at("00:00").do(send_hour)
    schedule.every().day.at("00:01").do(send_day)
    schedule.every().day.at("00:59").do(collect_data_h)
    schedule.every().day.at("01:00").do(send_hour)
    schedule.every().day.at("01:59").do(collect_data_h)
    schedule.every().day.at("02:00").do(send_hour)
    schedule.every().day.at("02:59").do(collect_data_h)
    schedule.every().day.at("03:00").do(send_hour)
    schedule.every().day.at("03:59").do(collect_data_h)
    schedule.every().day.at("04:00").do(send_hour)
    schedule.every().day.at("04:59").do(collect_data_h)
    schedule.every().day.at("05:00").do(send_hour)
    schedule.every().day.at("05:59").do(collect_data_h)
    schedule.every().day.at("06:00").do(send_hour)
    schedule.every().day.at("06:59").do(collect_data_h)
    schedule.every().day.at("07:00").do(send_hour)
    schedule.every().day.at("07:59").do(collect_data_h)
    schedule.every().day.at("08:00").do(send_hour)
    schedule.every().day.at("08:59").do(collect_data_h)
    schedule.every().day.at("09:00").do(send_hour)
    schedule.every().day.at("09:59").do(collect_data_h)
    schedule.every().day.at("10:00").do(send_hour)
    schedule.every().day.at("10:59").do(collect_data_h)
    schedule.every().day.at("11:00").do(send_hour)
    schedule.every().day.at("11:59").do(collect_data_h)
    schedule.every().day.at("12:00").do(send_hour)
    schedule.every().day.at("12:59").do(collect_data_h)
    schedule.every().day.at("13:00").do(send_hour)
    schedule.every().day.at("13:59").do(collect_data_h)
    schedule.every().day.at("14:00").do(send_hour)
    schedule.every().day.at("14:59").do(collect_data_h)
    schedule.every().day.at("15:00").do(send_hour)
    schedule.every().day.at("15:59").do(collect_data_h)
    schedule.every().day.at("16:00").do(send_hour)
    schedule.every().day.at("16:59").do(collect_data_h)
    schedule.every().day.at("17:00").do(send_hour)
    schedule.every().day.at("17:59").do(collect_data_h)
    schedule.every().day.at("18:00").do(send_hour)
    schedule.every().day.at("18:59").do(collect_data_h)
    schedule.every().day.at("19:00").do(send_hour)
    schedule.every().day.at("19:59").do(collect_data_h)
    schedule.every().day.at("20:00").do(send_hour)
    schedule.every().day.at("20:59").do(collect_data_h)
    schedule.every().day.at("21:00").do(send_hour)
    schedule.every().day.at("21:59").do(collect_data_h)
    schedule.every().day.at("22:00").do(send_hour)
    schedule.every().day.at("22:59").do(collect_data_h)
    schedule.every().day.at("23:00").do(send_hour)
    schedule.every().day.at("23:59").do(collect_data_h)
    schedule.every().day.at("23:59").do(collect_data_d)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(s):
    asyncio.create_task(scheduler())


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
