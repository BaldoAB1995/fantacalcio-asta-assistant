"""
Importa il calendario ufficiale di Serie A dall'endpoint pubblico
usato dal widget "Calendario e Risultati" di legaseriea.it.

L'endpoint e' pubblico e non richiede autenticazione. Se non si
specifica il parametro matchDayId restituisce tutte le partite
della stagione in un'unica risposta.

Uso:
    python -m src.calendario_import --season 2026/27 --output data/calendario.csv
    python -m src.calendario_import --season-id "serie-a::Football_Season::XXXX" --output data/calendario.csv

Per trovare il season-id di una nuova stagione:
1. Apri https://www.legaseriea.it/serie-a/calendario-risultati
2. Apri gli strumenti sviluppatore del browser (F12) -> tab Network
3. Cambia giornata nel widget e cerca una richiesta verso
   api-sdp.legaseriea.it/.../seasons/<SEASON_ID>/matches
4. Copia il SEASON_ID dalla URL e aggiungilo al dizionario SEASON_IDS
   qui sotto (o passalo con --season-id).
"""
import argparse
import csv
import json
import sys
from urllib.parse import quote
from urllib.request import urlopen

API_URL_TEMPLATE = (
    "https://api-sdp.legaseriea.it/v1/serie-a/football/seasons/{season_id}/matches?locale=it-IT"
)

# Season id noti. Aggiungere qui i nuovi id man mano che la lega li pubblica.
SEASON_IDS = {
    "2026/27": "serie-a::Football_Season::ed7fdc2a3e7b408b942ec177b7b956b5",
}

FIELDNAMES = ["giornata", "data", "ora", "squadra_casa", "squadra_ospite", "stadio"]


def fetch_matches(season_id):
    url = API_URL_TEMPLATE.format(season_id=quote(season_id, safe=""))
    with urlopen(url) as resp:
        payload = json.load(resp)
    return payload["matches"]


def matches_to_rows(matches):
    rows = []
    for i, m in enumerate(matches):
        giornata = i // 10 + 1  # 10 partite per giornata con 20 squadre
        date_str, _, time_str = m["matchDateLocal"].partition("T")
        rows.append(
            {
                "giornata": giornata,
                "data": date_str,
                "ora": time_str[:5] if time_str else "",
                "squadra_casa": m["home"]["shortName"],
                "squadra_ospite": m["away"]["shortName"],
                "stadio": m.get("stadiumName") or "",
            }
        )
    return rows


def save_csv(rows, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Importa il calendario Serie A")
    parser.add_argument("--season", default="2026/27", help="Etichetta stagione presente in SEASON_IDS")
    parser.add_argument("--season-id", default=None, help="Season id completo (sovrascrive --season)")
    parser.add_argument("--output", default="data/calendario.csv", help="Percorso file CSV di output")
    args = parser.parse_args()

    season_id = args.season_id or SEASON_IDS.get(args.season)
    if not season_id:
        print(f"Season id sconosciuto per '{args.season}'. Passa --season-id.", file=sys.stderr)
        sys.exit(1)

    matches = fetch_matches(season_id)
    rows = matches_to_rows(matches)
    save_csv(rows, args.output)
    print(f"Salvate {len(rows)} partite in {args.output}")


if __name__ == "__main__":
    main()
