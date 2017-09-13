from __future__ import print_function
from pyspark import SparkContext
from pyspark.sql import SQLContext, Row
from pyspark.sql.functions import col
from pyspark.ml.feature import CountVectorizer
from pyspark.mllib.clustering import LDA, LDAModel
from pyspark.mllib.linalg import Vector, Vectors
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml import Pipeline
from nltk.stem.porter import PorterStemmer
import sys

reload(sys)
sys.setdefaultencoding('utf8')

if __name__ == "__main__":
    sc = SparkContext(appName="LDA")
    data = sc.textFile("/Users/xx/Desktop/Availabook/Asite/availabook/Utils/LDA.txt")
    data = data.map(lambda x: x.replace('#',' ').replace(',',' ').replace('.',' ').replace('-',' ').replace('"',' ').lower())
    sqlContext = SQLContext(sc)
    parsedData = data.zipWithIndex().map(lambda (words,idd): Row(idd= idd, words = words.split(' ')))
    docDF = sqlContext.createDataFrame(parsedData)
    # docDF.show()

    # stopword remover
    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    remover.transform(docDF).show(truncate=False)

    Vector = CountVectorizer(inputCol="filtered", outputCol="vectors")

    pipeline = Pipeline(stages=[remover])

    model_prep = pipeline.fit(docDF)
    result = model_prep.transform(docDF)

    model = Vector.fit(result)
    result = model.transform(result)
    result.show()

    corpus = result.select("idd", "vectors").rdd.map(lambda (x, y): [x, Vectors.fromML(y)]).cache()

    # Cluster the documents into six topics using LDA
    ldaModel = LDA.train(corpus, k=6, maxIterations=100, optimizer='online')
    topics = ldaModel.topicsMatrix()

    vocabArray = model.vocabulary

    topicIndices = sc.parallelize(ldaModel.describeTopics(maxTermsPerTopic=20))

def do_stemming(filtered):
    stemmed = []
    for f in filtered:
        stemmed.append(PorterStemmer().stem(f))
    return stemmed

def topic_render(topic):  # specify vector id of words to actual words
    terms = topic[0]
    result = []
    for i in range(20):
        term = vocabArray[terms[i]]
        result.append(term)
    result_final = do_stemming(result)
    return result_final

topics_final = topicIndices.map(lambda topic: topic_render(topic)).collect()

for topic in range(len(topics_final)):
    print ("Topic" + str(topic) + ":")
    for term in topics_final[topic]:
        print (term)
    print ('\n')