import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gastos')

def save_expense(place, amount, category, date, raw_message):
    item = {
        'expense_id': str(uuid.uuid4()),
        'date': date,
        'month': date[:7],
        'place': place,
        'amount': str(amount),
        'currency': 'ARS',
        'category': category,
        'raw_message': raw_message
    }
    table.put_item(Item=item)
    return item