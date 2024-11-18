"""
Telegram Message Analyzer

Author: Sergei Poluektov
Purpose: Analyzes Telegram messages for mentions of children in messages with #whois hashtag
Created: 18/11/2024

This script connects to Telegram, fetches messages from a specified chat, and analyzes them
using OpenAI's GPT-3.5 turbo to identify messages mentioning children. Results are saved to a file
with sender details and links.
"""

import asyncio
import logging
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from typing import List, Optional, Set

import openai
import yaml
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Message, User

# Configure logging with ISO format timestamp
logging.basicConfig(
    filename="script.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@dataclass
class TelegramConfig:
    """Configuration data structure for Telegram client.

    Attributes:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_name: Name of the session file
        chat_id: ID of the chat to analyze
        phone_number: Optional phone number for authentication
    """

    api_id: int
    api_hash: str
    session_name: str
    chat_id: int
    phone_number: Optional[str] = None


def read_config_from_yaml() -> TelegramConfig:
    """Read configuration data from a YAML file.

    Returns:
        TelegramConfig: Configuration object with Telegram client settings.

    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    try:
        with Path("config.yaml").open() as file:
            config_data = yaml.safe_load(file)
            return TelegramConfig(**config_data)
    except FileNotFoundError:
        logger.error("Configuration file 'config.yaml' not found")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise


def get_openai_api_key() -> str:
    """Retrieve the OpenAI API key from environment variables.

    Returns:
        str: OpenAI API key

    Raises:
        EnvironmentError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        raise EnvironmentError("OpenAI API key not found in environment variables")
    return api_key


async def analyze_mentions_of_children(message_text: str, api_key: str) -> bool:
    """Analyze if a message mentions children under 18.

    Args:
        message_text: The text message to analyze
        api_key: OpenAI API key for authentication

    Returns:
        bool: True if the message mentions children, False otherwise

    Note:
        Uses OpenAI's GPT-3.5 model to analyze Russian text for mentions of children.
    """
    try:
        response = await openai.ChatCompletion.acreate(
            api_key=api_key,
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Identify if the following message mentions kids (under 18).",
                },
                {
                    "role": "user",
                    "content": f"The following message is in Russian: '{message_text}'. "
                    "If it mentions kids under 18, respond 'yes', otherwise respond 'no'.",
                },
            ],
            max_tokens=5,
            temperature=0.2,
        )
        result = response.choices[0].message["content"].strip().lower()
        return result == "yes"
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during API call: {e}")
        return False


async def get_messages(client: TelegramClient, chat_id: int) -> List[Message]:
    """Fetch messages from the specified Telegram chat.

    Args:
        client: Authenticated Telegram client
        chat_id: ID of the chat to fetch messages from

    Returns:
        List[Message]: List of Telegram messages
    """
    try:
        return [msg async for msg in client.iter_messages(chat_id)]
    except Exception as e:
        logger.error(f"Error fetching messages from chat {chat_id}: {e}")
        return []


def get_user_link(user: User) -> str:
    """Generate a Telegram user link based on username or ID.

    Args:
        user: Telegram user object

    Returns:
        str: URL linking to the user's Telegram profile
    """
    return (
        f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
    )


async def extract_sender_details_with_children_mentions(
    messages: List[Message], api_key: str
) -> List[str]:
    """Extract sender details from messages mentioning children with #whois hashtag.

    Args:
        messages: List of Telegram messages to analyze
        api_key: OpenAI API key for content analysis

    Returns:
        List[str]: Formatted strings with sender details and links
    """
    results: List[str] = []
    processed_messages: Set[str] = set()

    for message in messages:
        try:
            if not (message.text and "#whois" in message.text.lower()):
                continue

            if message.text in processed_messages:
                logger.info("Duplicate message detected. Skipping analysis.")
                continue

            processed_messages.add(message.text)

            if await analyze_mentions_of_children(message.text, api_key):
                sender = await message.get_sender()
                sender_name = (
                    f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                )
                date = message.date.strftime("%d/%m/%Y %H:%M:%S")
                user_link = get_user_link(sender)
                results.append(f"{sender_name} - {date} - {user_link}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    return results


async def initialize_client(config: TelegramConfig) -> Optional[TelegramClient]:
    """Initialize and authenticate the Telegram client.

    Args:
        config: Telegram configuration object

    Returns:
        Optional[TelegramClient]: Authenticated client or None if authentication fails
    """
    client = TelegramClient(config.session_name, config.api_id, config.api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        if not config.phone_number:
            logger.error(
                "Client is not authorized and no phone number provided in config"
            )
            return None

        try:
            await client.send_code_request(config.phone_number)
            code = input("Enter the code you received: ")
            await client.sign_in(config.phone_number, code)
        except SessionPasswordNeededError:
            password = input(
                "Two-step verification enabled. Please enter your password: "
            )
            await client.sign_in(password=password)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None

    return client


async def main() -> None:
    """Main execution function."""
    logger.info("Script started")

    try:
        config = read_config_from_yaml()
        api_key = get_openai_api_key()

        client = await initialize_client(config)
        if not client:
            return

        messages = await get_messages(client, config.chat_id)
        results = await extract_sender_details_with_children_mentions(messages, api_key)

        output_path = Path("output_results.txt")
        output_path.write_text("\n".join(results), encoding="utf-8")
        logger.info(f"Results successfully written to {output_path}")

    except Exception as e:
        logger.error(f"Script execution failed: {e}")
    finally:
        if "client" in locals() and client:
            await client.disconnect()
            logger.info("Script finished successfully")


if __name__ == "__main__":
    asyncio.run(main())
