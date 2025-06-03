from flask import Flask, jsonify
import random
import nltk
from nltk.corpus import webtext, brown
from nltk.tokenize import sent_tokenize
import requests
from requests_oauthlib import OAuth1

app = Flask(__name__)

# NLTK setup (run once on startup)
nltk.download('punkt')
nltk.download('webtext')
nltk.download('brown')

# Prepare sentences corpus once
sentences = (
    sent_tokenize(webtext.raw('overheard.txt')) +
    sent_tokenize(' '.join(brown.words(categories='news')))
)

# OAuth1 credentials
api_key = "uBtfCM4DQQo8Y2ZOakJvVvkko"
api_secret = "ioB4d4SPXRlZW0x4yt5nrpgkxpCRg4uHpxucE21esjV9niRHvk"
access_token = "1929938679629524998-l1pOp5k1WkOfL8rkbdmB4SBALcR5wz"
access_token_secret = "t2k1JxzDY20KynYj0cU3ckb5cJcsu8qcM29oWeD5QtdXV"

auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
url = 'https://api.twitter.com/2/tweets'

def generate_tweet():
    while True:
        tweet = random.choice(sentences).strip()
        if 20 < len(tweet) < 280 and not tweet.startswith('['):
            return tweet

@app.route('/tweet', methods=['POST', 'GET'])
def tweet():
    tweet_text = generate_tweet()
    payload = {"text": tweet_text}
    response = requests.post(url, auth=auth, json=payload)
    
    if response.status_code == 201:
        return jsonify({"status": "success", "tweet": tweet_text}), 201
    else:
        return jsonify({"status": "error", "code": response.status_code, "message": response.text}), response.status_code

if __name__ == "__main__":
    app.run(debug=True)
