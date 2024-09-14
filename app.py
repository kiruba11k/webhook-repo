from flask import Flask, request, jsonify, render_template, abort
from pymongo import MongoClient
from datetime import datetime
import json
import hmac
import hashlib
import os
from dotenv import load_dotenv  # Import python-dotenv to load .env file

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# MongoDB setup using environment variables
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['webhook_db']
events_collection = db['events']

# GitHub webhook secret (retrieved from environment variables)
GITHUB_SECRET = os.getenv("GITHUB_SECRET", 'your_webhook_secret')

def verify_signature(data, signature):
    """Verify the GitHub webhook signature using HMAC and the secret."""
    hmac_gen = hmac.new(GITHUB_SECRET.encode(), data, hashlib.sha256)
    return hmac.compare_digest(f"sha256={hmac_gen.hexdigest()}", signature)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    
    # Verify the signature using the secret
    if not signature or not verify_signature(request.data, signature):
        abort(403)  # Forbidden if the signature is invalid

    if request.method == 'POST':
        data = json.loads(request.data)
        event_type = request.headers.get('X-GitHub-Event')

        if event_type == 'push':
            # Using the commit hash as request_id
            request_id = data['head_commit']['id']
            author = data['pusher']['name']
            to_branch = data['ref'].split('/')[-1]
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

            event = {
                'request_id': request_id,
                'author': author,
                'action': 'PUSH',
                'from_branch': None,
                'to_branch': to_branch,
                'timestamp': timestamp
            }
            events_collection.insert_one(event)

        elif event_type == 'pull_request':
            action = data['action']
            # Use PR ID as request_id
            request_id = str(data['pull_request']['id'])
            author = data['pull_request']['user']['login']
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

            event_action = 'PULL_REQUEST' if action == 'opened' else 'MERGE'

            event = {
                'request_id': request_id,
                'author': author,
                'action': event_action,
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': timestamp
            }
            events_collection.insert_one(event)

        return jsonify({'message': 'Webhook received'}), 200

@app.route('/events', methods=['GET'])
def get_events():
    events = list(events_collection.find().sort('timestamp', -1).limit(10))
    for event in events:
        event['_id'] = str(event['_id'])  # Convert ObjectId to string
    return jsonify(events), 200

if __name__ == '__main__':
    app.run(debug=True)
