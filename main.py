import logging
import re
import time

import random
from persistance.entitiy.channel_entity import ChannelEntity
from persistance.repo.channel_repo import ChannelRepo
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from telethon.client import TelegramClient
from telethon.tl.types.messages import ChatFull
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelInvalidError, ChannelPrivateError, ChannelPublicGroupNaError, TimeoutError

from aiogram import Bot, Dispatcher, executor, types

BOT_API_TOKEN = '5194179073:AAGT5w6pJ_99JK3fErSFI5Wd9h4RuX2pn7g'
CLIENT_API_ID = 14551263
CLIENT_API_TOKEN = 'a88c839942b0c36db6e3632d2a8a207b'

logging.basicConfig(level=logging.INFO)

client = TelegramClient("script", CLIENT_API_ID, CLIENT_API_TOKEN)
bot = Bot(BOT_API_TOKEN)
dp = Dispatcher(bot)

channel_repo = ChannelRepo()


async def main():
    await client.connect()


@dp.message_handler(commands=['start', 'help'])
async def startOrHelpCommandHandler(message: types.Message):
    await message.answer(
        text=f"Вітаю!\n\
Цей бот створений для збору російських пропагандистських каналів, щоб потім відправляти на них репорти.\n\n\
Відправляйте мені канали, а я буду додавати їх у свою базу, після чого будемо старатися їх заблокувати!\n\
Щоб побачити всі каналі в базі напиши /channels\n\
До речі, також занємо що небайдужі КПІники розробили десктопний додаток, що допоможе автоматично кидати репорти\n\
https://auto-skarga.herokuapp.com\n\
Перемога за нами! Слава Україні!\n\n\
З усіх питань звертайся до @neonflame або @ya_rema"
    )

@dp.message_handler(commands=["channels"])
async def channelHandler(message: types.Message):
    channels: list = channel_repo.findAllByApprovedAndActive(approved=1)
    channel: ChannelEntity
    iterator = 0

    text = "Кількість підписників | Лінк\n"
    for channel in channels:
        if iterator % 100 == 0 and iterator != 0:
            await message.answer(text)
            text = "Кількість підписників | Лінк\n"

        text += "{0}\t | {1}\n".format(channel.subscribers, channel.link)
        iterator += 1

    if len(text.splitlines()) <= 100:
        await message.answer(text)


@dp.message_handler(commands=["verify"])
async def verify_request(message: types.Message):
    if not await is_moderator(message.from_user.username):
        await message.answer("Тебе не має у списку модерів")
        return

    channels: list = channel_repo.findAllByApprovedAndActive(approved=0)

    if channels is None or len(channels) == 0:
        await message.answer("Каналів на апрув бильше не має. Чекаємо нові")
        return

    await message.answer(
        text=channels[0].link,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✔️",
                        callback_data="approved"
                    ),
                    InlineKeyboardButton(
                        text="✖️️️",
                        callback_data="declined"
                    )
                ]
            ]
        )
    )

@dp.message_handler()
async def messageHandler(message: types.Message):
    await client.connect()

    links = re.findall(r'\S+t\.me\S+', message.text)
    for link in links:

        try:
            entity = await client.get_entity(link)
            channel_full_info: ChatFull = await client(GetFullChannelRequest(link))
            # time.sleep(random.randint(3, 10))
            time.sleep(1)
        except (ChannelInvalidError, TypeError):
            await message.answer("Щось бачу, але то не є канал")
            continue
        except ChannelPrivateError:
            await message.answer("Нажаль цей канал є приватним і я не можу заглянути туди")
            continue
        except ChannelPublicGroupNaError:
            await message.answer("Недоступний лінк( ")
            continue
        except TimeoutError:
            await message.answer("Timeout error, спробуй ще")
            continue
        except ValueError:
            await message.answer("Не можу нічого знайти за цим лінком")
            continue

        if not entity.broadcast:
            await message.answer("За цим лінком знаходиться не канал")
            continue

        channel: ChannelEntity = channel_repo.findByLink(link)

        if channel is not None:
            await message.answer("Ми вже знаємо про цей кнал. Дякую за пильність")
            continue

        channel = ChannelEntity(channel_full_info.full_chat.id, link, channel_full_info.full_chat.participants_count, 1)
        channel_repo.save(channel)
        await message.answer("Дякую записав канал до бази.\n Назва: {0} Кількість підписників: {1}".format(entity.username, channel.subscribers))

    await client.disconnect()


@dp.callback_query_handler()
async def verify_or_decline(callback: types.CallbackQuery):
    if not await is_moderator(callback.from_user.username):
        await callback.message.answer("Тебе не має у списку модерів")
        return

    approve = 1 if callback.data == "approved" else -1
    channel_repo.updateApproveByLink(callback.message.text, approve)
    await callback.answer()
    await callback.message.delete()

    channels: list = channel_repo.findAllByApprovedAndActive(approved=0)

    if channels is None or len(channels) == 0:
        await callback.message.answer("Каналів на апрув бильше не має. Чекаємо нові")
        return

    await callback.message.answer(
        text=channels[0].link,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✔️",
                        callback_data="approved"
                    ),
                    InlineKeyboardButton(
                        text="✖️️️",
                        callback_data="declined"
                    )
                ]
            ]
        )
    )


async def is_moderator(username: str) -> bool:
    with open("admin_list.txt") as file:
        moderators = file.read().split("\n")
    if username in moderators:
        return True
    return False

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
    executor.start_polling(dp, skip_updates=True)