import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gastos')

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,PUT,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
}

VALID_CATEGORIES = {
    'ALIMENTACION', 'TRANSPORTE', 'SALUD', 'ENTRETENIMIENTO', 'HOGAR', 'ROPA',
    'EDUCACION', 'RESTAURANTE', 'SERVICIOS', 'MASCOTAS', 'AUTOMOVIL', 'OTROS',
}


def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    if method == 'DELETE':
        return _delete_expense(event)

    if method == 'PUT':
        return _update_expense(event)

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


def _update_expense(event):
    try:
        expense_id = (event.get('pathParameters') or {}).get('expense_id')
        date = (event.get('queryStringParameters') or {}).get('date')

        # date es la sort key de la tabla, sin ella no se puede identificar el item a editar.
        # No se permite editar la fecha en si: cambiarla implicaria mover el item a otra sort key
        # (borrar + crear), no un update simple.
        if not expense_id or not date:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Faltan expense_id o date'})
            }

        body = json.loads(event.get('body', '{}'))
        place = body.get('place')
        amount = body.get('amount')
        category = body.get('category')

        if not place or amount is None or not category:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Faltan place, amount o category'})
            }

        if category not in VALID_CATEGORIES:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': f'Categoria invalida: {category}'})
            }

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'amount invalido'})
            }

        table.update_item(
            Key={'expense_id': expense_id, 'date': date},
            UpdateExpression='SET place = :place, amount = :amount, category = :category',
            ExpressionAttributeValues={
                ':place': place,
                ':amount': str(amount),
                ':category': category,
            }
        )

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'updated': expense_id})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }
