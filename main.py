from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

DATA = {"projects": {}}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "OK", "timestamp": str(datetime.now())})

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    user_idea = data.get('idea', '')
    
    if not user_idea:
        return jsonify({"error": "Idea required"}), 400
    
    project_id = f"proj_{len(DATA['projects'])}"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        prompt = f"""Create a product brief from this idea:
        IDEA: {user_idea}
        
        Respond ONLY as JSON:
        {{"name": "...", "description": "...", "target_market": "...", "price": "..."}}
        """
        
        response = model.generate_content(prompt)
        brief = response.text
        
        try:
            brief_json = json.loads(brief)
        except:
            brief_json = {"raw": brief}
        
        DATA['projects'][project_id] = {
            "idea": user_idea,
            "brief": brief_json,
            "created": str(datetime.now())
        }
        
        return jsonify({
            "project_id": project_id,
            "brief": brief_json,
            "status": "ok"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    if project_id not in DATA['projects']:
        return jsonify({"error": "Not found"}), 404
    return jsonify(DATA['projects'][project_id])

@app.route('/api/projects', methods=['GET'])
def list_projects():
    return jsonify({"projects": DATA['projects']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
