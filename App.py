import time
import random
import requests
from requests_oauthlib import OAuth1
from flask import Flask, jsonify, request
import logging
import threading
import json
import os
from datetime import datetime, timedelta
import openai

# Set your OpenAI API key here
openai.api_key = "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"

SYSTEM_PROMPT = "You are @DaggerStriker on Twitter. Write tweets and replies in their style."

# Twitter OAuth1 credentials
api_key = "uBtfCM4DQQo8Y2ZOakJvVvkko"
api_secret = "ioB4d4SPXRlZW0x4yt5nrpgkxpCRg4uHpxucE21esjV9niRHvk"
access_token = "1929938679629524998-l1pOp5k1WkOfL8rkbdmB4SBALcR5wz"
access_token_secret = "t2k1JxzDY20KynYj0cU3ckb5cJcsu8qcM29oWeD5QtdXV"

# Twitter API endpoint
url = 'https://api.twitter.com/2/tweets'
auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tweet timing & limits
API_TWEET_LIMIT = 17
SECONDS_IN_DAY = 86400
base_interval = SECONDS_IN_DAY / API_TWEET_LIMIT  # ~5082 seconds
TRACK_FILE = "tweet_tracker.json"

# Generate a tweet with OpenAI acting as @DaggerStriker
def generate_tweet():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Write a tweet within 280 characters."}
            ],
            max_tokens=100,
            temperature=0.8,
        )
        tweet = response['choices'][0]['message']['content'].strip()
        if len(tweet) > 280:
            tweet = tweet[:279]
        return tweet
    except Exception as e:
        logger.error(f"OpenAI tweet generation error: {e}")
        return None

# Load tweet tracking data
def load_tracker():
    if not os.path.exists(TRACK_FILE):
        return {
            "date": str(datetime.utcnow().date()),
            "count": 0,
            "last_tweet_time": None,
            "debt": 0
        }
    with open(TRACK_FILE, 'r') as f:
        return json.load(f)

# Save tweet tracking data
def save_tracker(data):
    with open(TRACK_FILE, 'w') as f:
        json.dump(data, f)

# Main loop for tweeting with timing and limits
def tweet_loop():
    while True:
        tracker = load_tracker()
        last_date = datetime.strptime(tracker['date'], "%Y-%m-%d").date()
        current_date = datetime.utcnow().date()

        # Reset count & debt if day has changed
        if current_date > last_date:
            tracker = {
                "date": str(current_date),
                "count": 0,
                "last_tweet_time": None,
                "debt": 0
            }

        now = datetime.utcnow()
        last_time_str = tracker.get("last_tweet_time")
        last_time = datetime.strptime(last_time_str, "%Y-%m-%dT%H:%M:%S") if last_time_str else None

        wait_time = base_interval + tracker.get("debt", 0)

        if last_time:
            elapsed = (now - last_time).total_seconds()
            if elapsed < wait_time:
                sleep_time = wait_time - elapsed
                logger.info(f"Waiting {int(sleep_time)}s before next tweet...")
                time.sleep(sleep_time)

        if tracker['count'] < API_TWEET_LIMIT:
            tweet = generate_tweet()
            if tweet:
                payload = {"text": tweet}
                response = requests.post(url, auth=auth, json=payload)

                now = datetime.utcnow()

                if response.status_code in [200, 201]:
                    logger.info(f"[{now}] [SUCCESS] Tweeted: {tweet}")
                    tracker['count'] += 1

                    if last_time:
                        elapsed = (now - last_time).total_seconds()
                        if elapsed < base_interval:
                            tracker['debt'] = base_interval - elapsed
                        else:
                            tracker['debt'] = 0
                    else:
                        tracker['debt'] = 0

                    tracker['last_tweet_time'] = now.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    logger.error(f"[{now}] [ERROR] Status {response.status_code}: {response.text}")

                save_tracker(tracker)
            else:
                logger.error("Failed to generate tweet; skipping this cycle.")
        else:
            logger.info(f"[{datetime.utcnow()}] Tweet limit reached for {tracker['date']} ({tracker['count']} tweets). Waiting for next day...")
            time.sleep(60)

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "online"})

# Reply endpoint to respond to mentions, generating replies in character
@app.route("/reply", methods=['POST'])
def reply():
    data = request.json
    incoming_tweet = data.get('tweet', '')

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Reply to this tweet as @DaggerStriker: {incoming_tweet}"}
            ],
            max_tokens=100,
            temperature=0.8,
        )
        reply_text = response['choices'][0]['message']['content'].strip()
        logger.info(f"Generated reply: {reply_text}")
        return jsonify({"reply": reply_text})
    except Exception as e:
        logger.error(f"OpenAI reply generation error: {e}")
        return jsonify({"error": "Failed to generate reply"}), 500

# Start tweet loop in background thread
def start_thread():
    thread = threading.Thread(target=tweet_loop)
    thread.daemon = True
    thread.start()

start_thread()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
