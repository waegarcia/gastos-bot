#!/bin/bash
# Deploy completo de gastos-ingest Lambda + API Gateway
# Requiere AWS CLI configurado con permisos suficientes

set -e

FUNCTION_NAME="gastos-ingest"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/gastos-lambda-role"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID}"
RUNTIME="python3.12"
HANDLER="handler.lambda_handler"
ZIP_FILE="ingest.zip"
API_ID="${API_GATEWAY_ID}"
STAGE="prod"
ROUTE_PATH="/webhook"

# Verificar variables requeridas
if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$API_GATEWAY_ID" ]; then
  echo "ERROR: Definir variables de entorno antes de ejecutar:"
  echo "  export AWS_ACCOUNT_ID=<tu-account-id>"
  echo "  export API_GATEWAY_ID=<tu-api-id>"
  exit 1
fi

echo "============================================"
echo " PASO 1: Empaquetar Lambda"
echo "============================================"
rm -f "$ZIP_FILE"
python -c "import zipfile; z = zipfile.ZipFile('$ZIP_FILE', 'w', zipfile.ZIP_DEFLATED); z.write('handler.py'); z.write('bedrock.py'); z.write('dynamo.py'); z.close()"
echo "OK: $ZIP_FILE creado"

echo ""
echo "============================================"
echo " PASO 2: Crear o actualizar funcion Lambda"
echo "============================================"
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "Funcion existe, actualizando codigo..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --output table
else
    echo "Funcion no existe, creando..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --timeout 30 \
        --memory-size 128 \
        --output table
fi

echo "Esperando que la funcion este activa..."
aws lambda wait function-active --function-name "$FUNCTION_NAME" --region "$REGION"

LAMBDA_ARN=$(aws lambda get-function \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query 'Configuration.FunctionArn' \
    --output text)
echo "OK: Lambda ARN = $LAMBDA_ARN"

echo ""
echo "============================================"
echo " PASO 2b: Adjuntar ultima version del Lambda Layer compartido"
echo "============================================"

LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name gastos-telegram-common \
    --region "$REGION" \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text)

aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --layers "$LAYER_ARN" \
    --region "$REGION" \
    --output table

echo "Esperando que la configuracion se actualice..."
aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"
echo "OK: Layer adjuntado = $LAYER_ARN"

echo ""
echo "============================================"
echo " PASO 3: Crear integracion en API Gateway"
echo "============================================"

# Verificar si ya existe una integracion para esta Lambda
EXISTING_INTEGRATION=$(aws apigatewayv2 get-integrations \
    --api-id "$API_ID" \
    --region "$REGION" \
    --query "Items[?IntegrationUri=='$LAMBDA_ARN'].IntegrationId" \
    --output text)

if [ -n "$EXISTING_INTEGRATION" ]; then
    INTEGRATION_ID="$EXISTING_INTEGRATION"
    echo "Integracion ya existe: $INTEGRATION_ID"
else
    echo "Creando integracion Lambda..."
    INTEGRATION_ID=$(aws apigatewayv2 create-integration \
        --api-id "$API_ID" \
        --integration-type AWS_PROXY \
        --integration-uri "$LAMBDA_ARN" \
        --payload-format-version "2.0" \
        --region "$REGION" \
        --query 'IntegrationId' \
        --output text)
    echo "OK: Integration ID = $INTEGRATION_ID"
fi

echo ""
echo "============================================"
echo " PASO 4: Crear ruta POST /webhook"
echo "============================================"

# Verificar si la ruta ya existe
EXISTING_ROUTE=$(aws apigatewayv2 get-routes \
    --api-id "$API_ID" \
    --region "$REGION" \
    --query "Items[?RouteKey=='POST $ROUTE_PATH'].RouteId" \
    --output text)

if [ -n "$EXISTING_ROUTE" ]; then
    ROUTE_ID="$EXISTING_ROUTE"
    echo "Ruta ya existe: $ROUTE_ID"
else
    echo "Creando ruta POST $ROUTE_PATH..."
    ROUTE_ID=$(aws apigatewayv2 create-route \
        --api-id "$API_ID" \
        --route-key "POST $ROUTE_PATH" \
        --target "integrations/$INTEGRATION_ID" \
        --region "$REGION" \
        --query 'RouteId' \
        --output text)
    echo "OK: Route ID = $ROUTE_ID"
fi

echo ""
echo "============================================"
echo " PASO 5: Permiso para que API Gateway invoque Lambda"
echo "============================================"

SOURCE_ARN="arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/$STAGE/POST$ROUTE_PATH"

# Intentar agregar permiso (falla silenciosamente si ya existe)
aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "apigateway-post-webhook" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "$SOURCE_ARN" \
    --region "$REGION" \
    --output table 2>/dev/null && echo "OK: Permiso agregado" || echo "OK: Permiso ya existia, continuando..."

echo ""
echo "============================================"
echo " PASO 6: Re-deployar stage prod"
echo "============================================"
aws apigatewayv2 create-deployment \
    --api-id "$API_ID" \
    --stage-name "$STAGE" \
    --region "$REGION" \
    --output table
echo "OK: Stage '$STAGE' re-deployado"

echo ""
echo "============================================"
echo " DEPLOY COMPLETO"
echo "============================================"
echo ""
echo "Endpoint disponible en:"
echo "  POST https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE$ROUTE_PATH"
echo ""
echo "IDs para referencia:"
echo "  Lambda ARN:     $LAMBDA_ARN"
echo "  Integration ID: $INTEGRATION_ID"
echo "  Route ID:       $ROUTE_ID"
echo ""
