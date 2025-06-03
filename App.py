from flask import Flask, jsonify
import threading
import time
import random
import nltk
from nltk.corpus import webtext, brown
from nltk.tokenize import sent_tokenize
import requests
from requests_oauthlib import OAuth1

# NLTK setup (download once)
nltk.download('punkt')
nltk.download('webtext')
nltk.download('brown')

# Twitter API credentials (plain for now — recommend using env vars)
api_key = "uBtfCM4DQQo8Y2ZOakJvVvkko"
api_secret = "ioB4d4SPXRlZW0x4yt5nrpgkxpCRg4uHpxucE21esjV9niRHvk"
access_token = "1929938679629524998-l1pOp5k1WkOfL8rkbdmB4SBALcR5wz"
access_token_secret = "t2k1JxzDY20KynYj0cU3ckb5cJcsu8qcM29oWeD5QtdXV"

# Twitter API endpoint
url = 'https://api.twitter.com/2/tweets'
auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

# Get sentences from a random Brown category + webtext
def get_random_sentences():
    category = random.choice(brown.categories())
    print(f"[INFO] Using Brown corpus category: {category}")
    brown_text = ' '.join(brown.words(categories=category))
    return (
        sent_tokenize(webtext.raw('overheard.txt')) +
        sent_tokenize(brown_text)
    )

# Generate tweet from the combined corpus
def generate_tweet():
    sentences = get_random_sentences()
    while True:
        tweet = random.choice(sentences).strip()
        if 20 < len(tweet) < 280 and not tweet.startswith('['):
            return tweet

# Tweet loop that runs forever
def tweet_loop():
    while True:
        tweet = generate_tweet()
        payload = {"text": tweet}
        response = requests.post(url, auth=auth, json=payload)

        if response.status_code in [200, 201]:
            print(f"[SUCCESS] Tweeted: {tweet}")
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text}")

        delay = random.randint(300, 900)
        print(f"[INFO] Sleeping for {delay // 60} min...")
        time.sleep(delay)

# Flask app setup
app = Flask(__name__)

@app.route("/")
def home():
    return "Shitpost Bot is online."

@app.route("/tweet-now")
def tweet_now():
    tweet = generate_tweet()
    payload = {"text": tweet}
    response = requests.post(url, auth=auth, json=payload)
    
    if response.status_code in [200, 201]:
        return jsonify({"status": "success", "tweet": tweet})
    else:
        return jsonify({"status": "error", "code": response.status_code, "message": response.text})

# Start tweet loop in background
threading.Thread(target=tweet_loop, daemon=True).start()

if __name__ == "__main__":
    app.run()
