import re
from datetime import datetime

AMOUNT_PATTERN = r'\$?\s*(\d[\d.,]*)'

def _parse_amount(raw):
    if ',' in raw:
        # Formato argentino: "." separador de miles, "," decimal (ej: "80.006,94")
        raw = raw.replace('.', '').replace(',', '.')
    elif raw.count('.') == 1:
        integer_part, decimals = raw.split('.')
        if len(decimals) == 3:
            # "." como separador de miles, sin decimales (ej: "80.000" -> 80000)
            raw = integer_part + decimals
        # si no, se asume "." como separador decimal (ej: "45.50")
    return float(raw)

def parse_expense(message):
    today = datetime.now().strftime('%Y-%m-%d')

    # Extraer monto
    amount_match = re.search(AMOUNT_PATTERN, message)
    amount = _parse_amount(amount_match.group(1)) if amount_match else 0.0

    # Extraer lugar (todo antes del monto)
    place = re.sub(AMOUNT_PATTERN, '', message).strip()
    
    return {
        'place': place,
        'amount': amount,
        'currency': 'ARS',
        'category': 'OTROS',
        'date': today
    }