import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gastos')


def lambda_handler(event, context):
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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': json.dumps(items)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': 'Internal server error'})
        }
