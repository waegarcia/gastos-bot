import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gastos')

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
}


def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    if method == 'DELETE':
        return _delete_expense(event)

    return _list_expenses(event)


def _list_expenses(event):
    try:
        params = event.get('queryStringParameters') or {}
        month = params.get('month')  # formato esperado: "2026-07"

        if month:
            # Query sobre el GSI month-date-index, en vez de scan completo
            response = table.query(
                IndexName='month-date-index',
                KeyConditionExpression=Key('month').eq(month)
            )
        else:
            response = table.scan()

        items = response.get('Items', [])

        # DynamoDB puede paginar; seguir si hay LastEvaluatedKey
        while 'LastEvaluatedKey' in response:
            if month:
                response = table.query(
                    IndexName='month-date-index',
                    KeyConditionExpression=Key('month').eq(month),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            else:
                response = table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            items.extend(response.get('Items', []))

        # Ordenar por fecha descendente
        items.sort(key=lambda x: x.get('date', ''), reverse=True)

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps(items)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }


def _delete_expense(event):
    try:
        expense_id = (event.get('pathParameters') or {}).get('expense_id')
        date = (event.get('queryStringParameters') or {}).get('date')

        # date es la sort key de la tabla, sin ella no se puede identificar el item a borrar
        if not expense_id or not date:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Faltan expense_id o date'})
            }

        table.delete_item(Key={'expense_id': expense_id, 'date': date})

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'deleted': expense_id})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }
