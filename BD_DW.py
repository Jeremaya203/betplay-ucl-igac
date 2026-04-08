#!/usr/bin/env python3
"""
export_firebase.py — Betplay IGAC
Exporta todos los documentos de la colección 'betplay' a un archivo JSON local.
"""
import firebase_admin
from firebase_admin import credentials, firestore
import json

SERVICE_ACCOUNT = "serviceAccountKey.json"  # debe estar en la misma carpeta

# Inicializar Firebase
cred = credentials.Certificate(SERVICE_ACCOUNT)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Leer todos los documentos de la colección 'betplay'
print("📡 Conectando a Firebase...")
docs = db.collection("betplay").stream()

export = {}
for document in docs:
    raw = document.to_dict()
    # Si el campo 'data' es un string JSON, lo parseamos para que sea legible
    if "data" in raw and isinstance(raw["data"], str):
        try:
            raw["data"] = json.loads(raw["data"])
        except json.JSONDecodeError:
            pass  # lo deja como string si no es JSON válido
    export[document.id] = raw
    print(f"  ✅ {document.id}")

# Guardar en archivo
output_file = "betplay_export.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=2)

print(f"\n🎉 Exportado correctamente → {output_file}")
print(f"   Documentos encontrados: {list(export.keys())}")