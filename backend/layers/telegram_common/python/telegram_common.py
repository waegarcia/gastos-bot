import json
import urllib.request

import boto3

ssm = boto3.client('ssm', region_name='us-east-1')


def get_telegram_token():
    response = ssm.get_parameter(Name='/gastos/telegram-token', WithDecryption=True)
    return response['Parameter']['Value']


def get_allowed_chat_ids():
    response = ssm.get_parameter(Name='/gastos/telegram-allowed-chat-ids')
    raw = response['Parameter']['Value']
    return {int(chat_id.strip()) for chat_id in raw.split(',') if chat_id.strip()}


def send_telegram_message(chat_id, text, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
