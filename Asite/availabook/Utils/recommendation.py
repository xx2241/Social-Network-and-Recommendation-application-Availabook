from boto3.dynamodb.conditions import Key, Attr
from boto3.session import Session
import os
import sys
import json
import operator
import datetime

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

table = dynamodb.Table("Preference")

def recommend(email):
    response = table.get_item(
        Key={
            'email': email
        }
    )
    if 'Item' not in response:
        table.put_item(
            Item={
                'email': email,
                'sports': 0,
                'music': 0,
                'food': 0,
                'exihibition': 0,
                'movie': 0,
                'travel': 0,
                'study': 0
            }
        )
        return newUser(email)
    else:
        return returnUser(email)

# for new registered user
def newUser(email):
    tb_user = dynamodb.Table("User")
    tb_event = dynamodb.Table("Event")
    res_1 = tb_user.get_item(
        Key={
            'email': email
        }
    )
    location = res_1['Item']['city']
    res_2 = tb_event.scan(
        FilterExpression=Attr('place').eq(location),
    )
    res_2_diff = tb_event.scan(
        FilterExpression=Attr('place').ne(location),
    )
    items = res_2['Items']
    items_diff = res_2_diff['Items']
    dic = {}
    for item in items:
        EId = item['EId']
        fave = item['fave']
        popular = len(fave)
        dic[EId] = popular
    sorted_dic = sorted(dic.items(), key=operator.itemgetter(1), reverse=True)
    dic_diff = {}
    for item in items_diff:
        EId = item['EId']
        fave = item['fave']
        popular = len(fave)
        dic_diff[EId] = popular
    sorted_dic_diff = sorted(dic_diff.items(), key=operator.itemgetter(1), reverse=True)
    eventList = []
    for i in range(0,10):
        if i < len(sorted_dic):
            id = sorted_dic[i][0]
            res_3 = tb_event.get_item(
                Key={
                    'EId': id
                }
            )
            date = res_3['Item']['date']
            time = res_3['Item']['time']
            if isExpired(date, time):
                pass
            else:
                event = res_3['Item']
                eventList.append(event)
        else:
            pass
    length = len(eventList)
    if length < 10:
        for i in range(length, 10):
            if i-length < len(sorted_dic_diff):
                id = sorted_dic_diff[i-len(eventList)][0]
                res_4 = tb_event.get_item(
                    Key={
                        'EId': id
                    }
                )
                date = res_4['Item']['date']
                time = res_4['Item']['time']
                if isExpired(date, time):
                    pass
                else:
                    event = res_4['Item']
                    eventList.append(event)
            else:
                pass
    return eventList


def returnUser(email):
    response = table.get_item(
        Key={
            'email': email
        }
    )
    if response['Item']['sports'] == response['Item']['music'] == response['Item']['food'] == \
            response['Item']['exihibition'] == response['Item']['movie'] == response['Item']['travel'] == response['Item']['study']:
        return newUser(email)
    else:
        pass


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


# for not login user
def common():
    tb_event = dynamodb.Table("Event")
    event = tb_event.scan()
    items = event['Items']
    dic = {}
    for item in items:
        EId = item['EId']
        fave = item['fave']
        popular = len(fave)
        dic[EId] = popular
        sorted_dic = sorted(dic.items(), key=operator.itemgetter(1), reverse=True)
    eventList = []
    for i in range(0, 10):
        if i < len(sorted_dic):
            id = sorted_dic[i][0]
            res_3 = tb_event.get_item(
                Key={
                    'EId': id
                }
            )
            date = res_3['Item']['date']
            time = res_3['Item']['time']
            if isExpired(date, time):
                pass
            else:
                event = res_3['Item']
                eventList.append(event)
        else:
            pass
    return eventList


if __name__ == '__main__':
    # if not login
    # print common()
    # print ("\n")
    # if login
    print newUser("test@gmail.com")