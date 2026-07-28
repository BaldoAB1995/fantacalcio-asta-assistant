"""
Importa le quotazioni Mantra/Classic del fantacalcio da un file
CSV o Excel-esportato-come-CSV nel formato usato da fantacalcio.it
(e da molti altri siti di quotazioni, che seguono uno schema simile).

Il file ufficiale si scarica cosi':
1. Accedi al tuo account su https://www.fantacalcio.it
2. Vai su Quotazioni e FVM (https://www.fantacalcio.it/quotazioni-fantacalcio)
3. Seleziona la stagione desiderata e premi "Scarica" per esportare l'Excel
4. Apri il file con Excel/Google Sheets e salvalo come CSV (UTF-8)
5. Metti il CSV in data/ (es. data/quotazioni.csv) e passalo a questo script

Questo modulo NON scarica automaticamente il file (serve un account
per farlo), ma normalizza qualunque export con intestazioni simili a:
    Id;R;RM;Nome;Squadra;Qt.A;Qt.I;Diff.;Qt.A M;Qt.I M;Diff.M;FVM;FVM M
riconoscendo diverse varianti di nome colonna.

Uso:
    python -m src.quotazioni_import --input data/quotazioni.csv --output data/quotazioni_pulite.csv
"""
import argparse
import csv
from pathlib import Path

# Possibili nomi di colonna (minuscolo, senza spazi) -> campo normalizzato
COLUMN_ALIASES = {
    "nome": "nome",
    "calciatore": "nome",
    "squadra": "squadra",
    "sq": "squadra",
    "r": "ruolo_classic",
    "ruolo": "ruolo_classic",
    "rm": "ruoli_mantra",
    "ruolomantra": "ruoli_mantra",
    "ruolim": "ruoli_mantra",
    "qt.i": "qt_iniziale_classic",
    "qti": "qt_iniziale_classic",
    "quotazioneiniziale": "qt_iniziale_classic",
    "qt.a": "qt_attuale_classic",
    "qta": "qt_attuale_classic",
    "quotazioneattuale": "qt_attuale_classic",
    "qt.im": "qt_iniziale_mantra",
    "qtim": "qt_iniziale_mantra",
    "qt.am": "qt_attuale_mantra",
    "qtam": "qt_attuale_mantra",
    "fvm": "fvm_classic",
    "fvmm": "fvm_mantra",
    "fvm.m": "fvm_mantra",
}

OUTPUT_FIELDS = [
    "nome",
    "squadra",
    "ruolo_classic",
    "ruoli_mantra",
    "qt_iniziale_classic",
    "qt_attuale_classic",
    "fvm_classic",
    "qt_iniziale_mantra",
    "qt_attuale_mantra",
    "fvm_mantra",
]


def _normalize_header(raw_header):
    key = raw_header.strip().lower().replace(" ", "")
    return COLUMN_ALIASES.get(key)


def _sniff_dialect(sample_text):
    try:
        return csv.Sniffer().sniff(sample_text, delimiters=",;")
    except csv.Error:
        return csv.excel  # fallback: virgola


def load_quotazioni(path):
    """Legge un file di quotazioni e restituisce una lista di dizionari
    con chiavi normalizzate (vedi OUTPUT_FIELDS). Le colonne non
    riconosciute vengono ignorate."""
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    dialect = _sniff_dialect(text[:2048])

    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    header_map = {}
    for raw in reader.fieldnames or []:
        normalized = _normalize_header(raw)
        if normalized:
            header_map[raw] = normalized

    rows = []
    for raw_row in reader:
        row = {field: "" for field in OUTPUT_FIELDS}
        for raw_key, value in raw_row.items():
            normalized = header_map.get(raw_key)
            if normalized:
                row[normalized] = (value or "").strip()
        # RM puo' contenere piu' ruoli separati da ';' o ','
        if row["ruoli_mantra"]:
            parts = [p.strip() for p in row["ruoli_mantra"].replace(",", ";").split(";") if p.strip()]
            row["ruoli_mantra"] = ";".join(parts)
        if row["nome"]:
            rows.append(row)
    return rows


def save_clean_csv(rows, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Normalizza un file di quotazioni fantacalcio")
    parser.add_argument("--input", required=True, help="File CSV scaricato (Excel esportato come CSV)")
    parser.add_argument("--output", default="data/quotazioni_pulite.csv", help="File CSV normalizzato di output")
    args = parser.parse_args()

    rows = load_quotazioni(args.input)
    save_clean_csv(rows, args.output)
    print(f"Normalizzati {len(rows)} giocatori in {args.output}")


if __name__ == "__main__":
    main()
