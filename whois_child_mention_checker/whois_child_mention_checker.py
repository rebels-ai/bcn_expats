"""
This script processes a JSON file containing messages to identify and extract details
of senders who mention children (under 18) in messages tagged with the #whois hashtag.
It utilizes OpenAI's gpt-3.5-turbo model to analyze message content and outputs the results to a text file.

Requirements:
- openai==0.28.0 (`openai`) 
- Python 3.7 or higher

Environment Variables:
- OPENAI_API_KEY: Your OpenAI API key.

Usage:
Ensure the `input_data.json` file is in the same directory or provide the correct path.
Set the `OPENAI_API_KEY` environment variable before running the script.

Example:
    export OPENAI_API_KEY='your-api-key-here'
    python whois_child_mention_checker.py.py
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

import openai


# Configure logging
logging.basicConfig(
    filename='script.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_openai_api_key() -> str:
    """
    Retrieve the OpenAI API key from environment variables.

    Returns:
        str: OpenAI API key.

    Raises:
        EnvironmentError: If the API key is not found.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logging.error("OpenAI API key not found in environment variables.")
        raise EnvironmentError("OpenAI API key not found in environment variables.")
    return api_key


def analyze_mentions_of_children(message_text: str, api_key: str) -> bool:
    """
    Analyze the given message text to determine if it mentions children under 18.

    Args:
        message_text (str): The text of the message to analyze.
        api_key (str): OpenAI API key.

    Returns:
        bool: True if the message mentions children under 18, False otherwise.
    """
    try:
        response = openai.ChatCompletion.create(
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
        result = response.choices[0].message['content'].strip().lower()
        return result == 'yes'
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during API call: {e}")
        return False


def extract_sender_details_with_children_mentions(
    json_data: Dict,
    api_key: str
) -> List[str]:
    """
    Extract sender details from messages that contain the #whois hashtag and mention children.

    Args:
        json_data (dict): The JSON data containing messages.
        api_key (str): OpenAI API key.

    Returns:
        list: A list of strings with sender names and corresponding timestamps.
    """
    results = []
    processed_messages = set()  # To avoid processing duplicate messages

    for message in json_data.get("messages", []):
        try:
            # Check if the message contains the #whois hashtag
            if any(
                entity.get("type") == "hashtag" and entity.get("text").lower() == "#whois"
                for entity in message.get("text_entities", [])
            ):
                # Extract and concatenate message text parts
                message_text_parts = message.get("text", [])
                message_text = "".join(
                    [part["text"] if isinstance(part, dict) else part for part in message_text_parts]
                )

                if not message_text:
                    logging.warning("Empty message text encountered. Skipping.")
                    continue

                if message_text in processed_messages:
                    logging.info("Duplicate message detected. Skipping analysis.")
                    continue

                processed_messages.add(message_text)

                # Analyze if the message mentions children
                if analyze_mentions_of_children(message_text, api_key):
                    sender = message.get("from", "Unknown Sender")
                    date_str = message.get("date", "")
                    try:
                        date = datetime.fromisoformat(date_str)
                        exact_date_time = date.strftime("%d/%m/%Y %H:%M:%S")
                    except ValueError as e:
                        logging.error(f"Date parsing error for date '{date_str}': {e}")
                        exact_date_time = "Invalid Date"

                    results.append(f"{sender} - {exact_date_time}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    return results


def load_json_data(file_path: str) -> Dict:
    """
    Load JSON data from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as input_file:
            return json.load(input_file)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in file {file_path}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error loading JSON data: {e}")
        return {}


def write_results_to_file(results: List[str], file_path: str) -> None:
    """
    Write the results to a text file.

    Args:
        results (list): List of result strings to write.
        file_path (str): Path to the output text file.
    """
    try:
        with open(file_path, "w", encoding='utf-8') as output_file:
            output_file.write("\n".join(results))
        logging.info(f"Results successfully written to {file_path}.")
    except IOError as e:
        logging.error(f"I/O error writing to file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error writing to file {file_path}: {e}")


def main():
    """
    Main function to manage the processing of messages.
    """
    input_file_path = 'input_data.json'
    output_file_path = 'output_results.txt'

    logging.info("Script started.")

    try:
        api_key = get_openai_api_key()
    except EnvironmentError as e:
        logging.critical(f"API key error: {e}")
        return

    json_data = load_json_data(input_file_path)
    if not json_data:
        logging.error("No data to process. Exiting script.")
        return

    results = extract_sender_details_with_children_mentions(json_data, api_key)

    write_results_to_file(results, output_file_path)

    logging.info("Script finished successfully.")


if __name__ == "__main__":
    main()