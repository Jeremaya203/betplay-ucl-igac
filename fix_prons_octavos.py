#!/usr/bin/env python3
"""
fix_prons_octavos.py — Betplay IGAC
Sube los pronósticos corregidos de Octavos (Excel v3) a Firebase.
Solo sobreescribe las keys de octavos; respeta cuartos/semis/final ya guardados.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

SERVICE_ACCOUNT = "serviceAccountKey.json"

# ── PRONÓSTICOS CORREGIDOS (Excel v3 — perspectiva home_first) ─────────────────
# IDA/VUELTA .home = goles del equipo que jugó de local en la IDA
# IDA/VUELTA .away = goles del equipo visitante en la IDA
PRONS_OCTAVOS = {
    "Fabián": {
        "par-che": {"ida": {"home":3,"away":2}, "vuelta": {"home":1,"away":3}},
        "gal-liv": {"ida": {"home":0,"away":2}, "vuelta": {"home":0,"away":2}},
        "rea-man": {"ida": {"home":2,"away":1}, "vuelta": {"home":1,"away":3}},
        "ata-bay": {"ida": {"home":1,"away":3}, "vuelta": {"home":1,"away":3}},
        "new-bar": {"ida": {"home":1,"away":3}, "vuelta": {"home":1,"away":3}},
        "atl-tot": {"ida": {"home":2,"away":1}, "vuelta": {"home":1,"away":2}},
        "fk-spo":  {"ida": {"home":2,"away":1}, "vuelta": {"home":1,"away":1}},
        "bay-ars": {"ida": {"home":0,"away":4}, "vuelta": {"home":0,"away":4}},
    },
    "Karen": {
        "par-che": {"ida": {"home":2,"away":3}, "vuelta": {"home":2,"away":1}},
        "gal-liv": {"ida": {"home":2,"away":1}, "vuelta": {"home":0,"away":1}},
        "rea-man": {"ida": {"home":3,"away":1}, "vuelta": {"home":2,"away":1}},
        "ata-bay": {"ida": {"home":2,"away":3}, "vuelta": {"home":0,"away":2}},
        "new-bar": {"ida": {"home":2,"away":1}, "vuelta": {"home":1,"away":0}},
        "atl-tot": {"ida": {"home":1,"away":2}, "vuelta": {"home":2,"away":0}},
        "fk-spo":  {"ida": {"home":1,"away":0}, "vuelta": {"home":1,"away":0}},
        "bay-ars": {"ida": {"home":1,"away":2}, "vuelta": {"home":0,"away":2}},
    },
    "Yohn": {
        "par-che": {"ida": {"home":2,"away":1}, "vuelta": {"home":1,"away":2}},
        "gal-liv": {"ida": {"home":0,"away":2}, "vuelta": {"home":0,"away":2}},
        "rea-man": {"ida": {"home":1,"away":3}, "vuelta": {"home":0,"away":2}},
        "ata-bay": {"ida": {"home":0,"away":2}, "vuelta": {"home":0,"away":3}},
        "new-bar": {"ida": {"home":1,"away":2}, "vuelta": {"home":1,"away":2}},
        "atl-tot": {"ida": {"home":2,"away":0}, "vuelta": {"home":1,"away":1}},
        "fk-spo":  {"ida": {"home":1,"away":2}, "vuelta": {"home":0,"away":2}},
        "bay-ars": {"ida": {"home":0,"away":3}, "vuelta": {"home":0,"away":2}},
    },
    "Michael": {
        "par-che": {"ida": {"home":2,"away":1}, "vuelta": {"home":2,"away":1}},
        "gal-liv": {"ida": {"home":0,"away":1}, "vuelta": {"home":0,"away":1}},
        "rea-man": {"ida": {"home":1,"away":3}, "vuelta": {"home":1,"away":3}},
        "ata-bay": {"ida": {"home":0,"away":3}, "vuelta": {"home":0,"away":3}},
        "new-bar": {"ida": {"home":1,"away":2}, "vuelta": {"home":1,"away":2}},
        "atl-tot": {"ida": {"home":3,"away":0}, "vuelta": {"home":3,"away":0}},
        "fk-spo":  {"ida": {"home":2,"away":0}, "vuelta": {"home":2,"away":0}},
        "bay-ars": {"ida": {"home":0,"away":2}, "vuelta": {"home":0,"away":2}},
    },
}

def main():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    print("🔧 Corrigiendo pronósticos de Octavos en Firebase...\n")
    for participante, oct_data in PRONS_OCTAVOS.items():
        doc_ref  = db.collection("betplay").document(f"pron_{participante}")
        existing = doc_ref.get()
        # Fusionar: conservar cuartos/semis/final, sobreescribir solo octavos
        current  = json.loads(existing.to_dict().get("data", "{}")) if existing.exists else {}
        current.update(oct_data)
        doc_ref.set({"data": json.dumps(current), "updated_at": datetime.now().isoformat()})
        print(f"  ✅ pron_{participante} actualizado ({len(oct_data)} cruces de octavos)")

    print(f"\n✔  Listo — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
