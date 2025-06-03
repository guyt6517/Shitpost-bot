import time
import random
import nltk
from nltk.corpus import webtext, brown
from nltk.tokenize import sent_tokenize
import requests
from requests_oauthlib import OAuth1
from flask import Flask, jsonify
import logging
import threading

# NLTK setup
nltk.download('punkt')
nltk.download('webtext')
nltk.download('brown')

# OAuth1 credentials (not encoded)
api_key = "uBtfCM4DQQo8Y2ZOakJvVvkko"
api_secret = "ioB4d4SPXRlZW0x4yt5nrpgkxpCRg4uHpxucE21esjV9niRHvk"
access_token = "1929938679629524998-l1pOp5k1WkOfL8rkbdmB4SBALcR5wz"
access_token_secret = "t2k1JxzDY20KynYj0cU3ckb5cJcsu8qcM29oWeD5QtdXV"

# Twitter API endpoint
url = 'https://api.twitter.com/2/tweets'
auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tweet generator
categories = ['news', 'editorial', 'reviews', 'religion', 'hobbies', 'lore', 'belles_lettres', 'government', 'learned', 'fiction', 'mystery', 'science_fiction', 'romance', 'humor']
random_category = random.choice(categories)
sentences = (
    sent_tokenize(webtext.raw('overheard.txt')) +
    sent_tokenize(' '.join(brown.words(categories=random_category)))
)

def generate_tweet():
    while True:
        tweet = random.choice(sentences).strip()
        if 20 < len(tweet) < 280 and not tweet.startswith('['):
            return tweet

# Tweet frequency calculation
API_TWEET_LIMIT = 17
SECONDS_IN_DAY = 86400
tweet_interval = SECONDS_IN_DAY // API_TWEET_LIMIT

# Tweet loop

def tweet_loop():
    while True:
        tweet = generate_tweet()
        payload = {"text": tweet}
        response = requests.post(url, auth=auth, json=payload)

        if response.status_code in [200, 201]:
            logger.info(f"[SUCCESS] Tweeted: {tweet}")
        else:
            logger.error(f"[ERROR] Status {response.status_code}: {response.text}")

        logger.info(f"Sleeping for {tweet_interval} seconds...")
        time.sleep(tweet_interval)

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "online"})

@app.before_first_request
def start_thread():
    thread = threading.Thread(target=tweet_loop)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
