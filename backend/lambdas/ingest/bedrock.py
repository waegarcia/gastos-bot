import re
import unicodedata
from datetime import datetime

AMOUNT_PATTERN = r'\$\s*(\d[\d.,]*)'  # "$" obligatorio, para no confundir horas/numeros sueltos con montos

CATEGORY_KEYWORDS = {
    'ALIMENTACION': ['coto', 'jumbo', 'carrefour', 'disco', 'dietetica', 'frizata', 'delivery', 'carniceria'],
    'TRANSPORTE': ['sube', 'uber', 'cabify'],
    'SALUD': ['farmacia', 'suplementos'],
    'MASCOTAS': ['petshop', 'bano perros', 'guarderia perros'],
    'AUTOMOVIL': ['nafta', 'mecanico', 'aca'],
}

def _normalize(text):
    # Saca acentos y pasa a minuscula, para que "Carnicería" y "carniceria" matcheen igual
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.lower()

def _detect_category(message):
    normalized = _normalize(message)
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', normalized):
                return category
    return 'OTROS'

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
    # Sin monto detectable, no es un gasto (evita guardar charla/ruido como si fuera uno)
    amount_match = re.search(AMOUNT_PATTERN, message)
    if not amount_match:
        return None

    today = datetime.now().strftime('%Y-%m-%d')
    amount = _parse_amount(amount_match.group(1))

    # Extraer lugar (todo antes del monto)
    place = re.sub(AMOUNT_PATTERN, '', message).strip()

    return {
        'place': place,
        'amount': amount,
        'currency': 'ARS',
        'category': _detect_category(message),
        'date': today
    }