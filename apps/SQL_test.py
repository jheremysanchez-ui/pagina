import pytest
from django.db import connection

# ✅ Payloads típicos (no destructivos)
PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "\" OR \"\"=\"",
    "'; DROP TABLE x; --",
]

@pytest.mark.django_db
@pytest.mark.parametrize("payload", PAYLOADS)
def test_raw_query_is_parameterized(monkeypatch, payload):
    """
    Esta prueba NO intenta explotar nada.
    Verifica que tu código llama cursor.execute(sql, params)
    y que el SQL contiene placeholders %s (en vez de concatenar strings).
    """

    calls = []

    class FakeCursor:
        def execute(self, sql, params=None):
            calls.append((sql, params))
            return None
        def fetchall(self): return []
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    def fake_cursor():
        return FakeCursor()

    monkeypatch.setattr(connection, "cursor", fake_cursor)

    # -----------------------------
    # 👇 AQUÍ LLAMA TU FUNCIÓN REAL
    # Ejemplo (ADÁPTALO):
    # from apps.product.services import search_products_raw
    # search_products_raw(payload)
    #
    # Si tú usas Model.objects.raw(), idealmente tu función termina
    # ejecutando cursor.execute internamente; si no, usa el test 1.2
    # -----------------------------

    # ✅ EJEMPLO de ejecución cruda (solo para demostrar el patrón):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 WHERE 1=%s", [payload])

    assert calls, "No se ejecutó ninguna consulta (cursor.execute no fue llamado)."

    sql, params = calls[0]
    assert "%s" in sql, "No hay placeholder %s -> posible concatenación peligrosa."
    assert params is not None, "No se pasaron params -> posible interpolación peligrosa."
    assert payload in params, "El payload debe ir en params, no incrustado en el SQL."
    assert payload not in sql, "El payload NO debe aparecer dentro del string SQL."
