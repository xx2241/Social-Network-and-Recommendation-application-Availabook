from __future__ import division
import json
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import sys

reload(sys)
sys.setdefaultencoding('utf8')

def saveFile(rdd):
    f = open("/Users/Kaili/Desktop/tweet.txt", 'a')
    f.write(str(rdd.encode('utf-8')))
    f.write("\n")
    f.close()

if __name__ == '__main__':
    sc = SparkContext(appName="TwitterStreaming")
    ssc = StreamingContext(sc, 1)
    tweetStream = KafkaUtils.createStream(ssc, 'localhost:2181', "kafka-stream-redis", {'tweets': 1})
    tweets = tweetStream.map(lambda x: x[1])

    ssc.checkpoint("./checkpoint-tweet")

    parsed = tweetStream.map(lambda v: json.loads(v[1]))
    text_dstream = parsed.map(lambda tweet: tweet['text'])

    text_dstream.foreachRDD(lambda rdd: rdd.foreach(saveFile))

    ssc.start()
    ssc.awaitTermination()