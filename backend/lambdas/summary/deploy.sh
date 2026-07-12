#!/bin/bash
# Deploy completo de gastos-monthly-summary Lambda + EventBridge Scheduler
# Requiere AWS CLI configurado con permisos suficientes
# Requiere que gastos-scheduler-role ya exista (creado una sola vez a mano, no lo gestiona este script)

set -e

FUNCTION_NAME="gastos-monthly-summary"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/gastos-lambda-role"
SCHEDULER_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/gastos-scheduler-role"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID}"
RUNTIME="python3.12"
HANDLER="handler.lambda_handler"
ZIP_FILE="summary.zip"
SCHEDULE_NAME="gastos-monthly-summary"

# Verificar variables requeridas
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "ERROR: Definir variable de entorno antes de ejecutar:"
  echo "  export AWS_ACCOUNT_ID=<tu-account-id>"
  exit 1
fi

echo "============================================"
echo " PASO 1: Empaquetar Lambda"
echo "============================================"
rm -f "$ZIP_FILE"
python -c "import zipfile; z = zipfile.ZipFile('$ZIP_FILE', 'w', zipfile.ZIP_DEFLATED); z.write('handler.py'); z.close()"
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
echo " PASO 3: Crear o actualizar EventBridge Schedule"
echo "============================================"

# Corre el dia 1 de cada mes a las 09:00 hora Argentina, manda el resumen del mes anterior
SCHEDULE_EXPRESSION="cron(0 9 1 * ? *)"
TARGET="{\"Arn\":\"$LAMBDA_ARN\",\"RoleArn\":\"$SCHEDULER_ROLE_ARN\"}"

if aws scheduler get-schedule --name "$SCHEDULE_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "Schedule ya existe, actualizando..."
    aws scheduler update-schedule \
        --name "$SCHEDULE_NAME" \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --schedule-expression-timezone "America/Argentina/Buenos_Aires" \
        --flexible-time-window "Mode=OFF" \
        --target "$TARGET" \
        --region "$REGION" \
        --output table
else
    echo "Creando schedule..."
    aws scheduler create-schedule \
        --name "$SCHEDULE_NAME" \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --schedule-expression-timezone "America/Argentina/Buenos_Aires" \
        --flexible-time-window "Mode=OFF" \
        --target "$TARGET" \
        --region "$REGION" \
        --output table
fi
echo "OK: Schedule '$SCHEDULE_NAME' configurado"

echo ""
echo "============================================"
echo " PASO 4: Permiso para que EventBridge Scheduler invoque Lambda"
echo "============================================"

SCHEDULE_ARN="arn:aws:scheduler:$REGION:$ACCOUNT_ID:schedule/default/$SCHEDULE_NAME"

# Intentar agregar permiso (falla silenciosamente si ya existe)
aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "scheduler-monthly-summary" \
    --action "lambda:InvokeFunction" \
    --principal "scheduler.amazonaws.com" \
    --source-arn "$SCHEDULE_ARN" \
    --region "$REGION" \
    --output table 2>/dev/null && echo "OK: Permiso agregado" || echo "OK: Permiso ya existia, continuando..."

echo ""
echo "============================================"
echo " DEPLOY COMPLETO"
echo "============================================"
echo ""
echo "Lambda: $FUNCTION_NAME"
echo "Corre: dia 1 de cada mes, 09:00 hora Argentina (schedule '$SCHEDULE_NAME')"
echo ""
echo "IDs para referencia:"
echo "  Lambda ARN:   $LAMBDA_ARN"
echo "  Schedule ARN: $SCHEDULE_ARN"
echo ""
