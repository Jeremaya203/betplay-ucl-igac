#!/usr/bin/env python3
"""
update_firebase.py — UCL 25/26 Betplay IGAC
Detecta automáticamente todos los partidos (Octavos, Cuartos, Semis, Final)
desde football-data.org y actualiza Firebase Firestore.
"""
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json, re, os

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_KEY          = os.environ.get("FOOTBALL_API_KEY", "79b8030c17c949618a2ca60e3840ca77")
SEASON           = 2025
UCL_ID           = 2001
SERVICE_ACCOUNT  = "serviceAccountKey.json"

# ── MAPEO DE RONDAS ───────────────────────────────────────────────────────────
ROUND_MAP = {
    "LAST_16":        "oct",
    "Round of 16":    "oct",
    "ROUND_OF_16":    "oct",
    "QUARTER_FINALS": "qtr",
    "Quarter-finals": "qtr",
    "SEMI_FINALS":    "semi",
    "Semi-finals":    "semi",
    "FINAL":          "final",
    "Final":          "final",
}

# ── ESCUDOS POR NOMBRE OFICIAL (football-data.org) ────────────────────────────
CRESTS_BY_NAME = {
    "Paris Saint-Germain FC":    "psg",
    "Chelsea FC":                "chelsea",
    "Galatasaray SK":            "galatasaray",
    "Liverpool FC":              "liverpool",
    "Real Madrid CF":            "realmadrid",
    "Manchester City FC":        "mancity",
    "Atalanta BC":               "atalanta",
    "FC Bayern München":         "bayernmunich",
    "Newcastle United FC":       "newcastle",
    "FC Barcelona":              "barcelona",
    "Club Atlético de Madrid":   "atletico",
    "Tottenham Hotspur FC":      "tottenham",
    "FK Bodø/Glimt":             "bodo",
    "Sporting Clube de Portugal":"sporting",
    "Bayer 04 Leverkusen":       "leverkusen",
    "Arsenal FC":                "arsenal",
    "FC Internazionale Milano":  "inter",
    "PSV Eindhoven":             "psv",
    "AC Milan":                  "milan",
    "Juventus FC":               "juventus",
    "SL Benfica":                "benfica",
    "Feyenoord":                 "feyenoord",
    "FC Porto":                  "porto",
    "AS Monaco FC":              "monaco",
    "BSC Young Boys":            "youngboys",
    "Celtic FC":                 "celtic",
    "Club Brugge KV":            "bruges",
    "Aston Villa FC":            "astonvilla",
}

# ── PRONÓSTICOS DE OCTAVOS (Excel v3 — perspectiva home_first) ───────────────
# Nota: ida.home/away y vuelta.home/away SIEMPRE desde perspectiva del equipo
# que jugó de local en la IDA (home_first), igual que results en Firebase.
# Para VUELTA: home = goles del home_first (visitante físico), away = goles del away_first (local físico).
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

# ── HELPERS ───────────────────────────────────────────────────────────────────
def slug(home: str, away: str) -> str:
    """Genera un ID corto estable desde los nombres de equipo."""
    def code(name):
        words = re.sub(r"[^a-zA-Z ]", "", name.lower()).split()
        stop = {"fc","af","sc","bv","ac","cf","de","klub","club","the","sk","bc"}
        words = [w for w in words if w not in stop] or words
        return words[0][:3]
    return f"{code(home)}-{code(away)}"

def get_score(match: dict, side: str):
    val = (match.get("score") or {}).get("fullTime", {}).get(side)
    return int(val) if val is not None else None

def debug_stages(all_matches):
    stages = {}
    for m in all_matches:
        s = m.get("stage", "N/A")
        stages[s] = stages.get(s, 0) + 1
    print("\n🔍 STAGES disponibles en la API:")
    for s, count in sorted(stages.items()):
        mapped = ROUND_MAP.get(s, "❌ NO MAPEADO")
        print(f"   → '{s}' ({count} partidos) → {mapped}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    # 1. Consultar API
    print("📡 Consultando football-data.org...")
    headers = {"X-Auth-Token": API_KEY}
    url = f"https://api.football-data.org/v4/competitions/{UCL_ID}/matches?season={SEASON}"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    all_matches = r.json().get("matches", [])
    print(f"   → {len(all_matches)} partidos encontrados en la UCL {SEASON}/{str(SEASON+1)[-2:]}")
    debug_stages(all_matches)

    # 2. Filtrar solo rondas knockout
    ko_matches = [m for m in all_matches if m.get("stage") in ROUND_MAP]

    # 3. Agrupar por par de equipos
    pairs = {}
    for m in ko_matches:
        ht = (m.get("homeTeam") or {}).get("name", "")
        at = (m.get("awayTeam") or {}).get("name", "")
        if not ht or not at:
            continue
        ht_crest = (m.get("homeTeam") or {}).get("crest", "")
        at_crest = (m.get("awayTeam") or {}).get("crest", "")
        key = frozenset([ht, at])
        phase = ROUND_MAP[m["stage"]]
        if key not in pairs:
            pairs[key] = {"matches": [], "phase": phase, "home_first": ht, "away_first": at, "home_crest": ht_crest, "away_crest": at_crest}
        pairs[key]["matches"].append(m)

    # 4. Procesar cada cruce — IDA = partido más antiguo
    results_doc = {}
    matches_meta = []

    print("\n📊 Resultados procesados:")
    for key, info in pairs.items():
        ms = sorted(info["matches"], key=lambda x: x.get("utcDate", ""))
        home_team = info["home_first"]
        away_team = info["away_first"]
        phase     = info["phase"]
        match_id  = slug(home_team, away_team)

        # IDA — siempre desde perspectiva de home_team
        m1    = ms[0]
        home1 = (m1.get("homeTeam") or {}).get("name", "")
        if home1 == home_team:
            ida = {"home": get_score(m1,"home"), "away": get_score(m1,"away")}
        else:
            ida = {"home": get_score(m1,"away"), "away": get_score(m1,"home")}

        # VUELTA — también desde perspectiva de home_team
        vuelta = None
        if len(ms) >= 2 and phase != "final":
            m2    = ms[1]
            home2 = (m2.get("homeTeam") or {}).get("name", "")
            if home2 == away_team:
                # away_team es local en la vuelta → invertimos para mantener perspectiva
                vuelta = {"home": get_score(m2,"away"), "away": get_score(m2,"home")}
            else:
                vuelta = {"home": get_score(m2,"home"), "away": get_score(m2,"away")}

        results_doc[match_id] = {"ida": ida, "vuelta": vuelta}

        ida_str = f"{ida['home']}-{ida['away']}" if ida["home"] is not None else "pendiente"
        vta_str = f"{vuelta['home']}-{vuelta['away']}" if (vuelta and vuelta["home"] is not None) else "pendiente"
        mark    = "✅" if (ida["home"] is not None or (vuelta and vuelta["home"] is not None)) else "⏳"
        print(f"   {mark} {match_id:<12} {phase:<6}  IDA: {ida_str:<12} VUELTA: {vta_str}")

        hi = CRESTS_BY_NAME.get(home_team, "ucl")
        ai = CRESTS_BY_NAME.get(away_team, "ucl")
        matches_meta.append({
            "id": match_id, "phase": phase,
            "home": home_team, "away": away_team,
            "hi": hi, "ai": ai,
            "hi_url": info.get("home_crest", ""),
            "ai_url": info.get("away_crest", ""),
            "oneleg": phase == "final", "tbd": False,
        })

    # Añadir TBDs para rondas no completas
    for ph, count in [("qtr",4),("semi",2),("final",1)]:
        existing = sum(1 for m in matches_meta if m["phase"] == ph)
        for i in range(existing, count):
            matches_meta.append({
                "id": f"{ph}{i+1}", "phase": ph,
                "home": "TBD", "away": "TBD",
                "hi": "ucl", "ai": "ucl",
                "hi_url": "https://crests.football-data.org/CL.png",
                "ai_url": "https://crests.football-data.org/CL.png",
                "oneleg": ph == "final", "tbd": True,
            })

    # 5. Inicializar Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    print("\n☁️  Subiendo a Firebase...")
    db.collection("betplay").document("results").set({
        "data": json.dumps(results_doc),
        "updated_at": datetime.now().isoformat()
    })
    print("✅ results actualizado")

    db.collection("betplay").document("matches_meta").set({
        "data": json.dumps(matches_meta),
        "updated_at": datetime.now().isoformat()
    })
    print("✅ matches_meta actualizado")

    # 6. Subir pronósticos de octavos (fusión, no sobreescribe cuartos)
    print("\n📋 Subiendo pronósticos de octavos...")
    for participante, data in PRONS_OCTAVOS.items():
        doc_ref  = db.collection("betplay").document(f"pron_{participante}")
        existing = doc_ref.get()
        current  = json.loads(existing.to_dict().get("data", "{}")) if existing.exists else {}
        current.update(data)
        doc_ref.set({"data": json.dumps(current), "updated_at": datetime.now().isoformat()})
        print(f"  ✅ pron_{participante} actualizado")

    print(f"\n🕐 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🏆 Firebase actualizado correctamente!")

if __name__ == "__main__":
    main()
