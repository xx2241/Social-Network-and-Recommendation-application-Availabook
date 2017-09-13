from django.db import models
from boto3.session import Session
from boto3.dynamodb.conditions import Attr
import os
import sys
import json
from availabook.recommendation import recommend, common, get_label, get_score,rec_to_signup,normalize
import nltk
import operator
from nltk.corpus import wordnet as wn
import numpy as np
import random


"""reload intepretor, add credential path"""
reload(sys)
sys.setdefaultencoding('UTF8')

nltk.data.path.append(os.path.dirname(sys.path[0])+'/Asite/availabook/Utils/nltk_data')
"""import credentials from root/AppCreds"""

with open(os.path.dirname(sys.path[0])+'/Asite/availabook/AppCreds/AWSAcct.json','r') as AWSAcct:
    awsconf = json.loads(AWSAcct.read())

dynamodb_session = Session(aws_access_key_id=awsconf["aws_access_key_id"],
              aws_secret_access_key=awsconf["aws_secret_access_key"],
              region_name="us-east-1")

dynamodb = dynamodb_session.resource('dynamodb')

user_table = dynamodb.Table("User")
event_table = dynamodb.Table("Event")
post_table = dynamodb.Table("Post")
tb_result = dynamodb.Table("Result")
preference_table = dynamodb.Table("Preference")
# Create your models here.
class Users():
    #def __init__(self, id, passwd, passwd_again, firstname, lastname, age, city, zipcode):
    def __init__(self, id, passwd):
        self.id = id
        self.passwd = passwd
        #self.passwd_again = passwd_again
        #self.firstname = firstname
        #self.lastname = lastname
        #self.age = age
        #self.city = city
        #self.zipcode = zipcode
        self.verified = False


    def get_response_by_id(self, id):
        response = user_table.get_item(
            Key={
                'email': id
            }
        )
        return response

    def authen_user(self):
	    return self.verify_email() and self.verify_passwd()

    def verify_email(self):
    	#user_id = self.id
        response = self.get_response_by_id(self.id)
        if 'Item' in response:
            return True
        else:
            return False

    def verify_passwd(self):
    	#user_id = self.id
        response = self.get_response_by_id(self.id)
        item = response['Item']
        pwd = item['password']
        if pwd == self.passwd:
            return True
        else:
            return False
        return False

    def authorize(self):
        self.verified = True

    @staticmethod
    def get_user_info(uid):
        response = user_table.get_item(
            Key={
                'email': uid
            }
        )
        if 'Item' in response:
            return response['Item']
        return None

    @staticmethod
    def get_image_by_id(id):
        response = user_table.get_item(
            Key={
                'email': id
            }
        )
        if 'Item' in response:
            return response['Item']['picture']
        return None

    @staticmethod
    def update_image_by_id(uid, link):
        try:
            response = user_table.update_item(
            Key={
                'email': uid
            },
            UpdateExpression="set picture = :r",
            ExpressionAttributeValues={
                ':r': link
            },
            ReturnValues="UPDATED_NEW"
                )
            print "Update Image succeeded"
            return True
        except Exception as e:
            print e
            return False


class Signup():
    def __init__(self, user_id, pwd, pwd_a, firstname, lastname, age, city, zipcode):
        self.id = user_id
        self.pwd = pwd
        self.pwd_a = pwd_a
        self.firstname = firstname
        self.lastname = lastname
        self.age = age
        self.city = city
        self.zipcode = zipcode
        self.picture = ''

    def add_picture(self, link):
        self.picture = link

    def push_to_dynamodb(self):
        user_table.put_item(
            Item={
                'email': self.id,
                'age': self.age,
                'city': self.city,
                'first_name': self.firstname,
                'last_name': self.lastname,
                'password': self.pwd,
                'zipcode': self.zipcode,
                'picture': str(self.picture),
            }
        )
        rec_res_new_user=tb_result.get_item(
            Key = {
                'email':'new_user'
            }
        )['Item']['rec_res']
        tb_result.put_item(
            Item={
                'email': self.id,
                'fave': 'False',
                'post': 'False',
                'rec_res': rec_res_new_user,
                'rec_to_all': 'False',
                'sign_up_flag': 'True'
            }
        )
        rating_default = normalize(np.ones(10))
        hyper_para_default = normalize(np.ones(4))
        print('random default user hyper vector'+str(hyper_para_default))
        preference_table.put_item(
            Item={
                'email': self.id,
                'rating': [str(i) for i in rating_default.tolist()],
                'distance_para':str(hyper_para_default[0]),
                'popularity_para':str(hyper_para_default[1]),
                'time_para':str(hyper_para_default[2]),
                'topic_para':str(hyper_para_default[3])
            }
        )

    @staticmethod
    def update_to_dynamodb(uid, first_name, last_name, age, city, zipcode):
        print "pushing"
        try:
            response = user_table.update_item(
            Key={
                'email': uid
            },
            UpdateExpression="set first_name = :fname, last_name = :lname, age = :a, city = :c, zipcode = :z",
            ExpressionAttributeValues={
                ':fname': first_name,
                ':lname': last_name,
                ':a': age,
                ':c': city,
                ':z': zipcode
            },
            ReturnValues="UPDATED_NEW"
                )
            print "Update User succeeded"
            print first_name, last_name, age, city, zipcode
            return True
        except Exception as e:
            print e
            return False


class Event():
    def __init__(self,event): ### event means event['item'] in db
        self.EId = event['EId']  ### use hadhid, to be modify
        self.content = event['content']
        self.date = event['date']
        self.time = event['time']
        self.label = event['label']
        self.fave = event['fave']
        self.zipcode = event['zipcode']
        self.fave_num = str(len(event['fave']))
    ### delete function
    def delete(self,EId):
        event_table.delete_item(
            Key={
                'EId': self.EId
            }
        )
    ### auxiliary function
    def add_fave(self,user_email):
        self.fave.append(user_email)
        self.fave_num = str(len(self.fave))
        event_table.update_item(
            Key={
            'EId': self.EId
        },
        UpdateExpression='SET fave = :val1',
        ExpressionAttributeValues={
            ':val1': self.fave,
        }
        )


def get_user_by_email(email):
    response = user_table.get_item(
            Key={
                'email': email
            }
    )
    if 'Item' in response:
        return response['Item']
    else:
        return None


def put_event_into_db(EId,content,date,time,fave,zipcode,timestamp,user_email):
    label = get_label(content)
    label = [str(i) for i in label.tolist()]
    event_table.put_item(
        Item={
            'EId': EId,
            'content': content,
            'date': date,
            'time': time,
            'label': label,
            'fave': fave,
            'zipcode': zipcode,
        }
    )
    post_table.put_item(
        Item={
            'EId': EId,
            'email': user_email,
            'post_time': timestamp
        }
    )
    print('get_label finish')


def get_user_info_from_eventlist(event_list):
    user_email_list = []
    user_name_list = []
    user_picture_list = []

    for event in event_list:
        response = post_table.get_item(
            Key={
                'EId': event.EId
            }
        )
        user_email_list.append(response['Item']['email'])
    for email in user_email_list:
        user = get_user_by_email(email)
        if user:
            user_name_list.append(user['first_name'] + " " + user['last_name'])
            user_picture_list.append(user['picture'])
        else:
            user_name_list.append("Default")
            user_picture_list.append("https://s3.amazonaws.com/image-availabook/default")

    return user_email_list, user_name_list, user_picture_list


def get_post_events_from_user(email):
    posts_list = []
    events_list = []

    response = post_table.scan(
        FilterExpression=Attr('email').eq(email)
    )
    if response:
        posts_list = response['Items']
        for post in posts_list:
            events_list.append(Event(get_event_by_EId(post["EId"])))

    return posts_list, events_list


def get_event_by_EId(EId):
    response = event_table.get_item(
        Key={
            'EId': EId
        }
    )
    return response['Item']


def get_event_list():
    ######## here need a iterator of dynamodb event table,then put them into event_list#######
    event_list = []
    response = event_table.scan(
    )
    tmp_list = response['Items']
    for e in tmp_list:
        event = Event(e)
        event_list.append(event)
    return event_list


def get_recommended_event_list(email): #### don't use this
    print "email recommendation:", email
    try:
        tmp_list = recommend(email)
    except:
        tmp_list = common()
    # print(tmp_list)
    event_list = []
    if tmp_list:
        for e in tmp_list:
            event = Event(e)
            event_list.append(event)
    return event_list

def get_recommend_newversion(email):
    rec_res = None
    try:
        rec_res = tb_result.get_item(
            Key={
                'email': email
            }
        )
    except:
        print('no such email, a visitor')
        rec_res = tb_result.get_item(
            Key={
                'email':'new_user'
            }
        )
    print('visitor get')
    rec_res = rec_res['Item']['rec_res']
    event_list = []
    print('before get rec_res')
    if rec_res:
        rec_res = json.loads(rec_res)
        rec_res_list = sorted(rec_res.items(),key=lambda x:x[1],reverse=True)
        i = 0
        for EId,value in rec_res_list:
            i+=1
            if i <= 20:
                print(i)
                try:
                    e = get_event_by_EId(EId)
                    event = Event(e)
                    print('get a new event'+e['content'] +': '+ str(rec_res[EId]))
                    event_list.append(event)
                except Exception as x:
                    print(x)
                    print('no such EId '+EId)
    return event_list




