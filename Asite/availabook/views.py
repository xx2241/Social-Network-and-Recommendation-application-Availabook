import time
import uuid
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.core import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from availabook.models import Users, Signup, Event, get_event_by_EId, get_event_list, put_event_into_db, get_recommended_event_list, get_user_by_email, get_user_info_from_eventlist, get_post_events_from_user,get_recommend_newversion
from availabook.recommendation import recommend_to_all,update_like_or_post_tag
from django.middleware import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt
import sys
from boto3.session import Session
import os
import json
from django.http import JsonResponse
from forms import UploadFileForm
from boto3.session import Session
from boto.s3.connection import S3Connection
from boto.s3.key import Key
"""reload intepretor, add credential path"""
reload(sys)
sys.setdefaultencoding('UTF8')


"""import credentials from root/AppCreds"""
print "path: " + os.path.dirname(sys.path[0])
with open(os.path.dirname(sys.path[0])+ '/Asite' + '/availabook/AppCreds/AWSAcct.json','r') as AWSAcct:
    awsconf = json.loads(AWSAcct.read())
#setup the bucket
#conn = S3Connection('<aws access key>', '<aws secret key>')
conn = S3Connection(awsconf["aws_access_key_id"], awsconf["aws_secret_access_key"])
bucket = conn.get_bucket('image-availabook')




# Create your views here.
def index(request):
    ''' render the landing page'''
    for key in request.session.keys():
        del request.session[key]

    if request.user.is_authenticated():
        print "home"
        #event_list = get_recommend_newversion(request.user.username)
        #email_list, user_name_list, user_picture_list = get_user_info_from_eventlist(event_list)
        #zipped_list = zip(event_list, email_list, user_name_list, user_picture_list)
        return render(request, 'homepage.html',{'zipped_list': zipped_list, 'logedin': True})
    else:
        print "landing"
        return render(request, 'landing.html')


def home(request):
    print(request.user.username)
    event_list = get_recommend_newversion(request.user.username)
    email_list, user_name_list, user_picture_list = get_user_info_from_eventlist(event_list)
    zipped_list = zip(event_list, email_list, user_name_list, user_picture_list)
    if request.user.is_authenticated():
        fname = Users.get_user_info(request.user.username)['first_name']
        return render(request, 'homepage.html',{'zipped_list':zipped_list, 'logedin': True,'fname':fname})
    else:
        print "not authenticate"
        return render(request, 'homepage.html',{'zipped_list':zipped_list, 'logedin': False})


@csrf_exempt
def fb_login(request, onsuccess="/availabook/temp", onfail="/availabook/"):
    print "fb_login"
    user_id = str(request.POST.get("email"))
    pwd = str(request.POST.get("psw"))
    pwd_a = pwd
    firstname = request.POST.get("fn")
    lastname = request.POST.get("ln")
    age = request.POST.get("age")
    picture = request.POST.get("picture")
    print user_id, pwd, firstname, lastname, age, picture

    city = 'ny'
    zipcode = '10027'
    signup_handler = Signup(user_id, pwd, pwd_a, firstname, lastname, age, city, zipcode)
    signup_handler.add_picture(picture)

    user_db = Users(user_id, pwd)
    if user_db.verify_email() == False:
        print "account not exist"
        if not user_exists(user_id):
            user = User(username=user_id, email=user_id)
            user.set_password(pwd)
            user.save()
            authenticate(username=user_id, password=pwd)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)

            try:
                print "~~~~~~~~~"
                signup_handler.push_to_dynamodb()
                print "push success"
            except Exception as e:
                print (e)


            print str(request.user.username) + " is signed up and logged in: " + str(request.user.is_authenticated())
            return redirect(onsuccess)
        else:
            user=authenticate(username=user_id, password=pwd)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            print str(request.user.username) + " is signed up and logged in: " + str(request.user.is_authenticated())
            return redirect(onsuccess)
    else:
        print "dynamo has the user info", user_id, pwd
        user = authenticate(username=user_id, password=pwd)
        print user
        try:
            if user is not None:
                auth_login(request, user)
                print "redirecting"
                return redirect(onsuccess)
            else:
                print "user is none"
                return redirect(onfail)
        except Exception as e:
            print e
            return redirect(onfail)


@csrf_exempt
def login(request, onsuccess="/availabook/temp", onfail="/availabook/"):
    csrf_token = csrf.get_token(request)
    user_id = request.POST.get("id")
    pwd = request.POST.get("psw")
    print user_id, pwd, csrf_token

    user = authenticate(username=user_id, password=pwd)
    if user is not None:
        auth_login(request, user)
        print ("Current input user information is already existed in Django sqlite")
    else:
        print ("Current input user information is not existed in Django sqlite or the input password incorrect with that in Django sqlite!")
        return HttpResponse("Error")

    login_user = Users(user_id, pwd)
    if login_user.authen_user():
        login_user.authorize()
        print str(request.user.username) + " is logged in: " + str(request.user.is_authenticated())
        return redirect(onsuccess)
    else:
        print ("Current user information not exist in AWS Dynamodb or the input password is incorrect with that in AWS Dynamodb!")
        #return redirect(onfail)
        return HttpResponse("Error")


@csrf_exempt
def signup(request, onsuccess="/availabook/temp", onfail="/availabook/"):
    user_id = request.POST.get("email")
    pwd = request.POST.get("psw")
    pwd_a = request.POST.get("psw_a")
    firstname = request.POST.get("fn")
    lastname = request.POST.get("ln")
    age = request.POST.get("age")
    city = request.POST.get("city")
    zipcode = request.POST.get("zipcode")
    print user_id, pwd, pwd_a, firstname, lastname, age, city, zipcode

    signup_handler = Signup(user_id, pwd, pwd_a, firstname, lastname, age, city, zipcode)
    signup_handler.add_picture("https://s3.amazonaws.com/image-availabook/default")

    if pwd == pwd_a:
        if not user_exists(user_id):
            user = User(username=user_id, email=user_id)
            user.set_password(pwd)
            user.save()
            authenticate(username=user_id, password=pwd)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            print ("Successfully saving user information to Django sqlite.")
            try:
                signup_handler.push_to_dynamodb()
                print ("Successfully pushing user information to AWS Dynamodb.")
                print str(request.user.username) + " is signed up and logged in: " + str(request.user.is_authenticated())
                return redirect(onsuccess)
            except Exception as e:
                print (e)
                print ("Pushing user information to AWS Dynamodb failed! Please sign up again!")
                return HttpResponse("Error")
        else:
            user_db = Users(user_id, pwd)
            if user_db.verify_email() == False:
                print "Current user is already existed in Django sqlite, but not in AWS Dynamodb! Generally, sign up will fail. For debugging, maybe you should first delete this user from your django sqlite, clean the cache in browser and sign up again!"
                try:
                    signup_handler.push_to_dynamodb()
                    print ("Successfully pushing user information to AWS Dynamodb.")
                    if request.user.is_authenticated():
                        print str(request.user.username) + " is signed up and logged in: " + str(request.user.is_authenticated())
                        return redirect(onsuccess)
                    else:
                        print ("Sign up failed. Please debug following the instructions above!")
                        return HttpResponse("Error")
                except Exception as e:
                    print (e)
                    print ("Pushing user information to AWS Dynamodb failed! Please debug and sign up again!")
                    return HttpResponse("Error")
            else:
                print ("Current user is already existed in both Django sqlite and AWS Dynamodb! Please turn to log in first!")
                print ("If you still can't sign up and log in, for debugging, please delete this user from your django sqlite, clean the cache in browser and sign up again!")
                return HttpResponse("Error")
    else:
        print "Two input passwords inconsistent! Please sign up again!"
        return HttpResponse("Error")


def user_exists(username):
    ''' check if user exists'''
    user_count = User.objects.filter(username=username).count()
    if user_count == 0:
        return False
    return True


def logout(request):
    ''' logout and redirect'''
    if request.user.is_authenticated():
        print str(request.user.username) + " is logged out!"
        auth_logout(request)
    return redirect("/availabook/temp")


def temp(request):
    return render(request, 'homepage.html');


def profile(request):
    if request.user.is_authenticated():
        print "views profile: ", request.user.username
        posts_list, events_list = get_post_events_from_user(request.user.username)
        zipped_list = zip(posts_list, events_list)
        item = Users.get_user_info(request.user.username)
        if item is None:
            print "No user info"
            return redirect("/availabook/home")
        email = item['email']
        link = item['picture']
        fname = item['first_name']
        lname = item['last_name']
        city = item['city']
        zipcode = item['zipcode']
        age = item['age']
        print link
        print {'fname':fname,'lname':lname,'city':city,'age':age,'zipcode':zipcode}
        return render(request, 'profile.html', {'email': email, 'link': link, 'logedin': True, 'fname': fname, 'lname': lname, 'city': city, 'age': age,'zipcode': zipcode, 'zipped_list': zipped_list})
    else:
        return redirect("/availabook/home")


def info(request):
    print "info"
    item = Users.get_user_info(request.user.username)
    if item is None:
        return redirect("/availabook/home")
    fname = item['first_name']
    lname = item['last_name']
    city = item['city']
    zipcode = item['zipcode']
    age = item['age']
    print "info send json", {'fname':fname,'lname':lname,'city':city,'age':age,'zipcode':zipcode}
    return JsonResponse({'fname':fname,'lname':lname,'city':city,'age':age,'zipcode':zipcode})


def edit(request):
    print "edit"
    fname = request.POST.get("fname")
    lname = request.POST.get("lname")
    city = request.POST.get("city")
    age = request.POST.get("age")
    zipcode = request.POST.get("zipcode")
    uid = request.user.username
    print fname, lname, age, city, zipcode, uid
    try:
        Signup.update_to_dynamodb(uid, fname, lname, age, city, zipcode)
    except Exception as e:
        print (e)
    return JsonResponse({'fname':fname,'lname':lname,'city':city,'age':age,'zipcode':zipcode})


def upload(request):
    print "uploading"
    profile_link = ""
    if request.method == 'POST':
        print "posting"
        print request.POST
        #print type(request.FILES['pic'].get('content_type'))
        #print type(request.FILES['pic']['file'])
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            print 'valid form'
            k = Key(bucket)
            k.key = request.user.username
            k.set_contents_from_file(request.FILES['pic'])
            print "upload!"
            profile_link = "https://s3.amazonaws.com/image-availabook/" + request.user.username
            profile_link = profile_link.replace('@','%40')
            print "link", profile_link
            uploaded = Users.update_image_by_id(request.user.username, profile_link)
            print uploaded
            #print k.get_contents_to_filename
        else:
            print 'invalid form'
            print form.errors
    return redirect("/availabook/profile")
    # return render(request, 'profile.html', {
    #     'link':profile_link
    # })


def post_event(request):
    if request.user.is_authenticated():
        print('post event')
        print('test')
        content = request.POST.get("post_content")
        print(content)
        print(request.POST.get("dateandtime"))
        event_date, event_time = request.POST.get("dateandtime").split("T")
        print(event_date, event_time)
        email = request.user.username
        print(email)
        user = get_user_by_email(email)
        print user
        zipcode = user['zipcode']
        print(zipcode)
        timestamp = time.strftime('%Y-%m-%d %A %X %Z',time.localtime(time.time()))
        EId = str(uuid.uuid4())
        print (timestamp)
        print (EId)
        try:
            put_event_into_db(EId=EId, content=content,date=event_date,time=event_time,fave=[], zipcode=zipcode,timestamp=timestamp,user_email=email)
            print ("Post is successfully puhed to AWS Dynamodb!")
        except Exception as e:
            print (e)
        event = {'EId':EId,'content':content,'date':event_date,'time':event_time,'fave':[],'zipcode':zipcode,'timestamp':timestamp,'user_email':email}

        update_like_or_post_tag(email,event,'post')

        print(EId +' posted')
        return redirect('/availabook/home')
    else:
        print "Please log in first before post!"
        return HttpResponse("Error")


def get_fave(request):
    if request.user.is_authenticated():
        EId = request.POST.get("EId")
        print(EId)
        event = get_event_by_EId(EId)

        update_like_or_post_tag(request.user.username,event,'like')

        event = Event(event)
        event.add_fave(request.user.username)
        return JsonResponse({"EId" : EId, "fave_num" : event.fave_num})
    else:
        print "Please log in first before like!"
        return JsonResponse({"EId" : "", "fave_num" : ""})
