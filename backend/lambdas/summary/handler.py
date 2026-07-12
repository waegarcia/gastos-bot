import json
import urllib.request
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key

ssm = boto3.client('ssm', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gastos')


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


def _previous_month():
    # El resumen siempre corre el dia 1, asi que "el mes anterior" es simplemente restar un dia al dia 1 actual
    first_of_this_month = datetime.now().replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    return last_month_end.strftime('%Y-%m')


def _fetch_month_expenses(month):
    response = table.query(
        IndexName='month-date-index',
        KeyConditionExpression=Key('month').eq(month)
    )
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.query(
            IndexName='month-date-index',
            KeyConditionExpression=Key('month').eq(month),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))

    return items


def _build_summary_text(month, items):
    if not items:
        return f"Resumen de {month}: no se registraron gastos."

    total = sum(float(i['amount']) for i in items)

    by_category = {}
    for i in items:
        cat = i.get('category', 'OTROS')
        by_category[cat] = by_category.get(cat, 0) + float(i['amount'])

    lines = [f"Resumen de gastos {month}", f"Total: ${total:,.2f} ARS", ""]
    for cat, amount in sorted(by_category.items(), key=lambda x: -x[1]):
        lines.append(f"{cat}: ${amount:,.2f}")

    return "\n".join(lines)


def lambda_handler(event, context):
    try:
        month = _previous_month()
        items = _fetch_month_expenses(month)
        text = _build_summary_text(month, items)

        token = get_telegram_token()
        for chat_id in get_allowed_chat_ids():
            send_telegram_message(chat_id, text, token)

        return {'statusCode': 200, 'body': 'ok'}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': 'error'}
