from flask import Flask, jsonify
import os
app = Flask(__name__)
@app.get('/')
def home():
    return jsonify(project='X AutoPilot', status='ready', mode='dry-run' if os.getenv('DRY_RUN','true').lower() != 'false' else 'live', scheduler='GitHub Actions')
