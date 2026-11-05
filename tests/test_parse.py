from scraper.build import slug
from scraper.parse_pdf import detect_columns, normalize_status, parse_order, rows_from_table


def test_status_normalization():
    assert normalize_status("Adjudicat") == "adjudicado"
    assert normalize_status("EXCLÒS") == "excluido"
    assert normalize_status("Activo") == "activo"


def test_parse_order():
    assert parse_order("1.234") == 1234
    assert parse_order("n/a") is None


def test_detect_columns_bilingual():
    cols = detect_columns(["Ordre", "NIF", "Cognoms i nom", "Estat"])
    assert set(cols.values()) == {"orden", "nif", "nombre", "estado"}


def test_rows_reuse_header_across_pages():
    page1 = [["Orden", "NIF", "Nombre", "Estado"], ["1", "***1234**", "Ana", "Adjudicado"]]
    page2 = [["2", "***5678**", "Luis", "Activo"]]
    rows1, m = rows_from_table(page1, None)
    rows2, _ = rows_from_table(page2, m)
    assert [r["orden"] for r in rows1 + rows2] == [1, 2]
    assert rows2[0]["estado"] == "activo"


def test_slug():
    assert slug("Educación Infantil (Maestros)") == "educacion-infantil-maestros"
