"""
Tracker della rosa durante l'asta: tiene traccia dei crediti spesi/rimanenti
e dei giocatori presi, ruolo per ruolo.

Lo schema degli slot per ruolo (quanti giocatori per ruolo puoi/devi
prendere) cambia da lega a lega: personalizza SLOT_MANTRA_DEFAULT in
base al regolamento della tua lega prima di usarlo.
"""
import json
from pathlib import Path

# Esempio di composizione rosa Mantra (25 giocatori totali). Personalizza
# in base al regolamento della tua lega.
SLOT_MANTRA_DEFAULT = {
    "Portiere": 3,
    "Dif. centrale": 3,
    "Braccetto": 2,
    "Dif. destro": 1,
    "Dif. sinistro": 1,
    "Esterno": 2,
    "Mediano": 2,
    "Cen. centrale": 2,
    "Ala": 2,
    "Trequartista": 2,
    "Attaccante": 1,
    "Punta centrale": 2,
}


class Rosa:
    """Rappresenta la rosa che si sta costruendo durante l'asta."""

    def __init__(self, crediti_iniziali=500, slot_ruoli=None):
        self.crediti_iniziali = crediti_iniziali
        self.slot_ruoli = dict(slot_ruoli) if slot_ruoli else {}
        self.giocatori = []  # ogni elemento: {"nome", "ruolo", "squadra", "prezzo"}

    @property
    def crediti_spesi(self):
        return sum(g["prezzo"] for g in self.giocatori)

    @property
    def crediti_rimanenti(self):
        return self.crediti_iniziali - self.crediti_spesi

    def slot_totali(self):
        return sum(self.slot_ruoli.values()) if self.slot_ruoli else None

    def slot_occupati(self, ruolo=None):
        if ruolo is not None:
            return sum(1 for g in self.giocatori if g["ruolo"] == ruolo)
        return len(self.giocatori)

    def slot_liberi(self, ruolo):
        if ruolo not in self.slot_ruoli:
            return None
        return self.slot_ruoli[ruolo] - self.slot_occupati(ruolo)

    def aggiungi_giocatore(self, nome, ruolo, squadra, prezzo):
        if prezzo < 0:
            raise ValueError("Il prezzo non puo' essere negativo")
        if prezzo > self.crediti_rimanenti:
            raise ValueError(
                f"Crediti insufficienti: rimangono {self.crediti_rimanenti}, servono {prezzo}"
            )
        liberi = self.slot_liberi(ruolo)
        if liberi is not None and liberi <= 0:
            raise ValueError(f"Nessuno slot libero per il ruolo '{ruolo}'")
        self.giocatori.append(
            {"nome": nome, "ruolo": ruolo, "squadra": squadra, "prezzo": prezzo}
        )

    def rimuovi_giocatore(self, nome):
        prima = len(self.giocatori)
        self.giocatori = [g for g in self.giocatori if g["nome"] != nome]
        return len(self.giocatori) < prima

    def riepilogo_per_ruolo(self):
        riepilogo = {}
        for ruolo, slot in self.slot_ruoli.items():
            occupati = self.slot_occupati(ruolo)
            riepilogo[ruolo] = {
                "occupati": occupati,
                "slot": slot,
                "liberi": slot - occupati,
            }
        return riepilogo

    def to_dict(self):
        return {
            "crediti_iniziali": self.crediti_iniziali,
            "slot_ruoli": self.slot_ruoli,
            "giocatori": self.giocatori,
        }

    @classmethod
    def from_dict(cls, data):
        rosa = cls(data.get("crediti_iniziali", 500), data.get("slot_ruoli", {}))
        rosa.giocatori = list(data.get("giocatori", []))
        return rosa


def salva_stato(rosa, path):
    Path(path).write_text(json.dumps(rosa.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def carica_stato(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Rosa.from_dict(data)
