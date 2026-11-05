from scraper.build import date_cuerpo_from_name
from scraper.parse_pdf import parse_text

SAMPLE = """\
                                                                      05/11/2026
                      ADJUDICACIÓN DE PERSONAL DOCENTE INTERINO DÍA 05/11/2026
                                         Mestres / Maestros

 MESTRES

1   PEREZ LOPEZ, ANA


                                                                         Desactivat

2   GOMEZ RUIZ, LUIS                                         Petición:   1   Voluntaria

         858392 VINARÒS(12004916)CENTRE PÚBLIC FPA LLIBERTAT
                  153 / FPA PRIMÀRIA
       23 horas                                     SUBSTITUCIÓ INDETERMINADA         Adjudicat

3   SANZ VERA, MARTA


                                                                         No ha participat

4   TORRES PONS, JAIME                                       Petición:   3   Voluntaria

         600158 SALER (EL)(46015691)CEIP LLUÍS DE SANTÀNGEL
                  126 / AUDICIÓ I LLENGUATGE
       23 horas                 Itinerante           VACANT                          Adjudicat

5   RIOS MORA, ELENA

                                                                         No adjudicat
"""


def test_parse_sample():
    rows, fecha = parse_text(SAMPLE)
    assert fecha == "2026-11-05"
    assert [r["orden"] for r in rows] == [1, 2, 3, 4, 5]
    assert [r["estado"] for r in rows] == [
        "desactivado", "adjudicado", "no_ha_participado", "adjudicado", "no_adjudicado"]
    adj = rows[1]["adj"]
    assert adj["provincia"] == "Castellón"
    assert adj["centro_codigo"] == "12004916"
    assert adj["especialidad"] == "FPA PRIMÀRIA"
    assert adj["tipo"] == "sustitucion_indeterminada"
    assert adj["peticion"] == 1
    adj2 = rows[3]["adj"]
    assert adj2["localidad"] == "SALER (EL)"
    assert adj2["itinerante"] is True and adj2["tipo"] == "vacante"
    assert "adj" not in rows[0]


def test_filename():
    assert date_cuerpo_from_name("261105_lis_mae.pdf") == ("2026-11-05", "mae")
    assert date_cuerpo_from_name("otra_cosa.pdf") == (None, None)
