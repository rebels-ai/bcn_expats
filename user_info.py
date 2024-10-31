import asyncio
from pathlib import Path

import yaml
from telethon.sync import TelegramClient


# Функция для чтения данных из YAML файла
def read_config_from_yaml():
    with Path('config.yaml').open() as file:
        config = yaml.safe_load(file)
    return config


# Функция для извлечения информации о пользователях чата
async def get_chat_members_info(client, chat_id):
    members_info = {}

    # Получение списка участников
    async for user in client.iter_participants(chat_id):
        members_info[user.id] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_bot": user.bot
        }

    return members_info


# Пример использования функции
async def main():
    config = read_config_from_yaml()  # Замените на путь к вашему YAML файлу

    api_id = config['api_id']
    api_hash = config['api_hash']
    session_name = config['session_name']
    chat_id = config['chat_id']  # -1001702074444 sns_spain

    async with TelegramClient(session_name, api_id, api_hash) as client:
        info = await get_chat_members_info(client, chat_id)
        print(info)

if __name__ == '__main__':
    asyncio.run(main())
