from datetime import datetime

from bedrock import parse_expense, _detect_category, _parse_amount


class TestParseAmount:
    def test_dot_as_decimal_separator(self):
        assert _parse_amount('45.50') == 45.50

    def test_dot_as_thousands_separator(self):
        assert _parse_amount('80.000') == 80000.0

    def test_comma_decimal_with_dot_thousands(self):
        # Formato argentino: "80.006,94" -> 80006.94
        assert _parse_amount('80.006,94') == 80006.94

    def test_comma_decimal_no_thousands(self):
        assert _parse_amount('5000,50') == 5000.50

    def test_integer_no_separators(self):
        assert _parse_amount('5000') == 5000.0


class TestDetectCategory:
    def test_alimentacion_keyword(self):
        assert _detect_category('Coto $5000') == 'ALIMENTACION'

    def test_transporte_keyword(self):
        assert _detect_category('Uber $2500') == 'TRANSPORTE'

    def test_salud_keyword(self):
        assert _detect_category('Farmacia $1200') == 'SALUD'

    def test_mascotas_keyword(self):
        assert _detect_category('Petshop $3000') == 'MASCOTAS'

    def test_automovil_keyword(self):
        assert _detect_category('Nafta $15000') == 'AUTOMOVIL'

    def test_case_insensitive(self):
        assert _detect_category('CARNICERIA $9000') == 'ALIMENTACION'

    def test_accents_normalized(self):
        assert _detect_category('Carnicería $9000') == 'ALIMENTACION'

    def test_unmatched_falls_back_to_otros(self):
        assert _detect_category('Cine $5000') == 'OTROS'

    def test_word_boundary_avoids_partial_match(self):
        # "acabar" no deberia matchear el keyword "aca"
        assert _detect_category('Acabar de comprar algo $500') == 'OTROS'

    def test_known_false_positive_aca(self):
        # Riesgo conocido y aceptado (ver CLAUDE.md): el keyword "aca" (club
        # automotor ACA) matchea contra la palabra comun "aca" como adverbio
        # de lugar. Este test documenta el comportamiento actual, no lo corrige.
        assert _detect_category('Compre esto por aca cerca $500') == 'AUTOMOVIL'


class TestParseExpense:
    def test_no_amount_returns_none(self):
        assert parse_expense('nos vemos a las 8') is None

    def test_extracts_place_and_amount(self):
        result = parse_expense('Carniceria $45000')
        assert result['place'] == 'Carniceria'
        assert result['amount'] == 45000.0
        assert result['category'] == 'ALIMENTACION'
        assert result['currency'] == 'ARS'

    def test_date_is_today(self):
        result = parse_expense('Coto $5000')
        assert result['date'] == datetime.now().strftime('%Y-%m-%d')

    def test_argentine_format_end_to_end(self):
        result = parse_expense('Nafta $80.006,94')
        assert result['amount'] == 80006.94
        assert result['category'] == 'AUTOMOVIL'
