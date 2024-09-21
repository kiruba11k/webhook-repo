from flask import Flask, request, jsonify, render_template, abort
from pymongo import MongoClient
from datetime import datetime, timedelta,timezone
import json
import hmac
import hashlib
import os
from dotenv import load_dotenv
import logging
import signal

load_dotenv()

app = Flask(__name__)
client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
events_collection = client['webhook_db']['events']
GITHUB_SECRET = os.getenv("GITHUB_SECRET", 'your_webhook_secret')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("webhook_events.log"),
    logging.StreamHandler()
])

def verify_signature(data, signature):
    return hmac.compare_digest(f"sha256={hmac.new(GITHUB_SECRET.encode(), data, hashlib.sha256).hexdigest()}", signature)

signal.signal(signal.SIGPIPE, lambda s, f: logging.warning("SIGPIPE caught and ignored"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature or not verify_signature(request.data, signature):
        logging.warning("Invalid signature received.")
        abort(403)

    try:
        data = json.loads(request.data)
        event_type = request.headers.get('X-GitHub-Event')
        timestamp = int(datetime.now(timezone.utc))
        
        event = {
            'timestamp': timestamp,
            'request_id': data.get('head_commit', {}).get('id', str(data['pull_request']['id'])),
            'author': data.get('pusher', {}).get('name', data['pull_request']['user']['login']),
            'from_branch': data.get('pull_request', {}).get('head', {}).get('ref', None),
            'to_branch': data['ref'].split('/')[-1] if event_type == 'push' else data['pull_request']['base']['ref'],
            'action': 'PUSH' if event_type == 'push' else ('PULL_REQUEST' if data['action'] == 'opened' else 'MERGE')
        }
        events_collection.insert_one(event)
        logging.info(f"{event_type.capitalize()} event logged: {event}")
        return jsonify({'message': 'Webhook received'}), 200

    except (BrokenPipeError, ConnectionResetError) as e:
        logging.error(f"Client disconnected: {e}")
        return jsonify({'message': 'Client disconnected'}), 499
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'message': 'Error processing request'}), 500

@app.route('/events', methods=['GET'])
def get_events():
    fifteen_seconds_ago = int((datetime.now(timezone.utc) - timedelta(seconds=15)).timestamp())
    events = list(events_collection.find({'timestamp': {'$gte': fifteen_seconds_ago}}).sort('timestamp'))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify(events), 200

if __name__ == '__main__':
    app.run(debug=True)
