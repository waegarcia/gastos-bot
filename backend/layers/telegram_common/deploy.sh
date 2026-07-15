#!/bin/bash
# Publica una nueva version del Lambda Layer gastos-telegram-common
# Requiere AWS CLI configurado con permisos suficientes
# Las funciones que usan este layer (gastos-ingest, gastos-monthly-summary)
# se encargan de adjuntar la ultima version publicada en sus propios deploy.sh

set -e

LAYER_NAME="gastos-telegram-common"
REGION="${AWS_REGION:-us-east-1}"
ZIP_FILE="layer.zip"

echo "============================================"
echo " PASO 1: Empaquetar Layer"
echo "============================================"
rm -f "$ZIP_FILE"
python -c "import zipfile; z = zipfile.ZipFile('$ZIP_FILE', 'w', zipfile.ZIP_DEFLATED); z.write('python/telegram_common.py', 'python/telegram_common.py'); z.close()"
echo "OK: $ZIP_FILE creado"

echo ""
echo "============================================"
echo " PASO 2: Publicar nueva version del Layer"
echo "============================================"
LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --description "Funciones compartidas para Telegram: token, allowlist de chat_id, envio de mensajes" \
    --zip-file "fileb://$ZIP_FILE" \
    --compatible-runtimes python3.12 \
    --region "$REGION" \
    --query 'LayerVersionArn' \
    --output text)

echo "OK: Layer version publicada = $LAYER_VERSION_ARN"

echo ""
echo "============================================"
echo " DEPLOY COMPLETO"
echo "============================================"
echo ""
echo "Layer: $LAYER_NAME"
echo "Version ARN: $LAYER_VERSION_ARN"
echo ""
