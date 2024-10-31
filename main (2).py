import json
import openai
from datetime import datetime


openai.api_key = ''

def analyze_mentions_of_kids(message_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Identify if the following message mentions kids (under 18)."},
            {"role": "user", "content": f"The following message is in Russian: '{message_text}'. If it mentions kids under 18, respond 'yes', otherwise respond 'no'."}
        ],
        max_tokens=5,
        temperature=0.2,
    )
    return response.choices[0].message['content'].strip().lower() == 'yes'

def extract_sender_details(data):
    results = []

    for message in data.get("messages", []):
        if any(entity.get("type") == "hashtag" and entity.get("text") == "#whois" for entity in message.get("text_entities", [])):
            message_text = "".join([part["text"] if isinstance(part, dict) else part for part in message.get("text", [])])

            if analyze_mentions_of_kids(message_text):
                sender = message.get("from")
                date_str = message.get("date")
                date = datetime.fromisoformat(date_str)
                month_year = date.strftime("%m/%Y")
                
                results.append(f"{sender} - {month_year}")

    return results

with open('result.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

results = extract_sender_details(data)

for result in results:
    print(result)