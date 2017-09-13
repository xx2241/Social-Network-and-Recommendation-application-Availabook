from django.conf.urls import url

from . import views

app_name = 'availabook'
print app_name
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/', views.login, name='login'),
    url(r'^fb_login/', views.fb_login, name='fb_login'),
    url(r'^signup/', views.signup, name='signup'),
    url(r'^logout/', views.logout, name='logout'),
    url(r'^home/', views.home, name='home'),
    url(r'^post_event/',views.post_event, name='post_event'),
    url(r'^get_fave/',views.get_fave,name='get_fave'),
    url(r'^profile/',views.profile,name='profile'),
    url(r'^upload/',views.upload,name='upload'),
    url(r'^info/',views.info,name='info'),
    url(r'^edit/',views.edit,name='edit'),
    url(r'^temp/',views.temp,name='temp'),
]
