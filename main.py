from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, re
from datetime import datetime
import google.generativeai as genai
from supabase import create_client, Client

app = Flask(name)
CORS(app)

Configuración de claves/servicios
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

MODEL_NAME = 'gemini-2.5-pro'

SYSTEM_PROMPT = """
Devuelve SOLO JSON válido (sin texto adicional, sin backticks).
Esquema:
{
"name": "string",
"description": "string",
"target_market": "string",
"price": "string"
}
"""

def extract_json_maybe(text: str):
# 1) Intento directo
try:
return json.loads(text)
except Exception:
pass
# 2) Extraer primer bloque {...}
m = re.search(r'{[\s\S]*}', text)
if m:
try:
return json.loads(m.group(0))
except Exception:
pass
# 3) Fallback
return {"raw": text.strip()}

@app.route('/api/health', methods=['GET'])
def health():
return jsonify({"status": "OK", "timestamp": str(datetime.utcnow())})

@app.route('/api/projects', methods=['POST'])
def create_project():
body = request.get_json(silent=True) or {}
idea = (body.get('idea') or '').strip()
if not idea:
return jsonify({"error": "Idea required"}), 400

text
# 1) Generar brief con Gemini
try:
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"{SYSTEM_PROMPT}\nIDEA: {idea}"
    resp = model.generate_content(prompt)
    text = (getattr(resp, 'text', '') or '').strip()
    brief = extract_json_maybe(text)
    # Validación mínima
    for k in ["name", "description", "target_market", "price"]:
        brief.setdefault(k, "")
except Exception as e:
    return jsonify({"error": f"Gemini: {str(e)}"}), 500

# 2) Guardar en Supabase
try:
    ins = sb.table('projects').insert({
        "idea": idea,
        "brief": brief
    }).execute()
    pid = ins.data["id"] if ins.data else None
    return jsonify({"status": "ok", "project_id": pid, "brief": brief})
except Exception as e:
    return jsonify({"error": f"Supabase: {str(e)}"}), 500
@app.route('/api/projects', methods=['GET'])
def list_projects():
res = sb.table('projects').select("*").order('created_at', desc=True).limit(50).execute()
return jsonify({"projects": res.data})

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
res = sb.table('projects').select("*").eq("id", project_id).single().execute()
if not res.data:
return jsonify({"error": "Not found"}), 404
return jsonify(res.data)

if name == "main":
app.run(host="0.0.0.0", port=5000)
