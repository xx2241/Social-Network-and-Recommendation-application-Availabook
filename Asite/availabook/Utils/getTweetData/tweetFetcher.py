import os
import sys
import json
import tweepy
from tweepy import StreamListener
from kafka import SimpleProducer, KafkaClient

"""reload intepretor, add credential path"""
reload(sys)
sys.setdefaultencoding('UTF8')


"""import credentials from root/AppCreds"""
with open(os.path.dirname(sys.path[0])+'/TwitterAcct.json','r') as TwitterAcct:
    twittconf = json.loads(TwitterAcct.read())
consumer_key = twittconf["consumer_key"]
consumer_secret = twittconf["consumer_secret"]
access_token = twittconf["access_token"]
access_token_secret = twittconf["access_token_secret"]


"""Kafka Settings"""
TOPIC = b'tweets'
KAFKA_CLIENT = KafkaClient('localhost:9092')
KAFKA_PRODUCER = SimpleProducer(KAFKA_CLIENT)

"""streaming"""
class TweetStreamListener(StreamListener):
    def __init__(self, api):
        self.topic = TOPIC
        self.api = api
        super(StreamListener, self).__init__()
        self.producer = KAFKA_PRODUCER
        self.backoff = 1
    
    def on_data(self, data):
        tweetJson = json.loads(data.encode('utf8'))
        try:
            if 'lang' in tweetJson:
                if tweetJson['lang'] == 'en':
                    print ('fetching tweet successfully')
                    self.backoff /= 2
                    self.producer.send_messages(self.topic, data.encode('utf8'))
        except Exception as error:
            print error
            return True
        return True

    def on_error(self, status):
        print (status)
        return True

def streaming():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    stream = tweepy.Stream(auth, listener = TweetStreamListener(api))
    stream.filter(track=['event'], languages = ['en'])

if __name__ == '__main__':
    streaming()