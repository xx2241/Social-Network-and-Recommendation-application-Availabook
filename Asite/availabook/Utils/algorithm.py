import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import pairwise_distances

header = ['user_id', 'sport_rating', 'moive_rating']
df = pd.read_csv('user.csv',names=header)
train = df.as_matrix()

user_similarity = pairwise_distances(train, metric='cosine')
# print user_similarity

item_similarity = pairwise_distances(train.T, metric='cosine')
# print item_similarity

mean_user_rating = train.mean(axis=1)
ratings_diff = (train - mean_user_rating[:, np.newaxis])
pred_user = mean_user_rating[:, np.newaxis] + user_similarity.dot(ratings_diff) / np.array([np.abs(user_similarity).sum(axis=1)]).T
# print pred_user

pred_item = train.dot(item_similarity) / np.array([np.abs(item_similarity).sum(axis=1)])
# print pred_item

########################################################################

from boto3.dynamodb.conditions import Key, Attr
from boto3.session import Session
import os
import sys
import json
import operator
import datetime
import numpy as np
from sklearn.metrics.pairwise import pairwise_distances

"""reload intepretor, add credential path"""
reload(sys)
sys.setdefaultencoding('UTF8')

"""import credentials from root/AppCreds"""
with open(os.path.dirname(sys.path[0])+'/AppCreds/AWSAcct.json','r') as AWSAcct:
    awsconf = json.loads(AWSAcct.read())

dynamodb_session = Session(aws_access_key_id=awsconf["aws_access_key_id"],
              aws_secret_access_key=awsconf["aws_secret_access_key"],
              region_name="us-east-1")
dynamodb = dynamodb_session.resource('dynamodb')

def user_based_similarity():
    tb_preference = dynamodb.Table("Preference")
    raw = tb_preference.scan()
    data = raw['Items']
    # print data
    cols_count, rows_count = 6, len(data)
    matrix = [[0 for x in range(cols_count)] for y in range(rows_count)]
    for i in range(0, len(data)):
        matrix[i][0]= int(data[i]['food'])
        matrix[i][1] = int(data[i]['movie'])
        matrix[i][2] = int(data[i]['study'])
        matrix[i][3] = int(data[i]['music'])
        matrix[i][4] = int(data[i]['travel'])
        matrix[i][5] = int(data[i]['exihibition'])
    train = np.array(matrix)

    user_similarity = pairwise_distances(train, metric='cosine')
    mean_user_rating = train.mean(axis=1)
    ratings_diff = (train - mean_user_rating[:, np.newaxis])
    pred_user = mean_user_rating[:, np.newaxis] + user_similarity.dot(ratings_diff) / np.array([np.abs(user_similarity).sum(axis=1)]).T
    return user_similarity

def most_similar_users(email):
    tb_preference = dynamodb.Table("Preference")
    raw = tb_preference.scan()
    data = raw['Items']
    matrix = user_based_similarity()
    print matrix
    length = len(data)
    list = []
    for i in range(0, length):
        if data[i]['email'] == email:
            list = matrix[i]
    print list
    high_similarity = max(list)
    print high_similarity
    user_index = []
    for i in range(0, len(list)):
        if list[i] == high_similarity:
            user_index.append(i)
    print user_index
    users = []
    for x in user_index:
        user = data[x]['email']
        users.append(user)
    print users
    return recommend_item(users)

def recommend_item(users):
    tb_fave = dynamodb.Table("Fave")
    tb_event = dynamodb.Table("Event")
    dict = {}
    for i in range(0, len(users)):
        print "user"+str(i)
        events = tb_fave.scan(
            FilterExpression=Attr('email').eq(users[i]),
        )
        eventlist = events['Items']
        length = len(eventlist)
        print "faveNumber"+str(length)
        for j in range(0, length):
            id = eventlist[j]['EId']
            res_5 = tb_event.get_item(
                Key={
                    'EId': id
                }
            )
            date = res_5['Item']['date']
            time = res_5['Item']['time']
            if isExpired(date, time) == False:
                if id not in dict:
                    dict[id] = 1
                else:
                    dict[id] += 1
    print dict
    sorted_dict = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)
    recommendation_list = []
    print sorted_dict
    for i in range(0,10):
        if i < len(sorted_dict):
            id = sorted_dict[i][0]
            res_6 = tb_event.get_item(
                Key={
                    'EId': id
                }
            )
            event = res_6['Item']
            recommendation_list.append(event)
        else:
            pass
    return recommendation_list


def create_table():
    table = dynamodb.create_table(
        TableName='Fave',
        KeySchema=[
            {
                'AttributeName': 'EId',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'email',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'EId',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'email',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    table.meta.client.get_waiter('table_exists').wait(TableName='Fave')

def isExpired(date, time):
    cur = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = cur.split(' ')
    curdate = cur[0].split('-')
    eventdate = date.split('-')
    curtime = cur[1].split(':')
    eventtime = time.split(':')
    if int(curdate[0]) < int(eventdate[0]):
        return False
    elif int(curdate[0]) == int(eventdate[0]) and int(curdate[1]) < int(eventdate[1]):
        return False
    elif int(curdate[0]) == int(eventdate[0]) and int(curdate[1]) == int(eventdate[1]) and int(curdate[2]) < int(eventdate[2]):
        return False
    elif int(curdate[0]) == int(eventdate[0]) and int(curdate[1]) == int(eventdate[1]) and int(curdate[2]) == int(eventdate[2]) \
        and int(curtime[0]) < int(eventtime[0]):
        return False
    elif int(curdate[0]) == int(eventdate[0]) and int(curdate[1]) == int(eventdate[1]) and int(curdate[2]) == int(eventdate[2]) \
        and int(curtime[0]) == int(eventtime[0]) and int(curtime[1]) < int(eventtime[1]):
        return False
    else:
        return True

if __name__ == '__main__':
    # create_table()
    print most_similar_users("xx@gmail.com")

