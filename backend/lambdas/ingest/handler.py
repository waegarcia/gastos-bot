import json
import boto3
import urllib.request
from bedrock import parse_expense
from dynamo import save_expense

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

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')

        if not chat_id or not text:
            return {'statusCode': 200, 'body': 'ok'}

        if chat_id not in get_allowed_chat_ids():
            return {'statusCode': 200, 'body': 'ok'}

        parsed = parse_expense(text)
        if parsed is None:
            return {'statusCode': 200, 'body': 'ok'}

        token = get_telegram_token()

        save_expense(
            place=parsed['place'],
            amount=parsed['amount'],
            category=parsed['category'],
            date=parsed['date'],
            raw_message=text
        )

        reply = (
            f"Gasto registrado:\n"
            f"Lugar: {parsed['place']}\n"
            f"Monto: ${parsed['amount']:,.2f} ARS\n"
            f"Categoria: {parsed['category']}\n"
            f"Fecha: {parsed['date']}"
        )
        send_telegram_message(chat_id, reply, token)

        return {'statusCode': 200, 'body': 'ok'}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 200, 'body': 'ok'}