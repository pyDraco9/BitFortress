"""BitFortress URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from bet.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', index),
    url(r'^(?P<p>\d+)/$', index),
    url(r'^view/(?P<bid>\d+)/$', view),
    url(r'^view/(?P<bid>\d+)/(?P<v>\d+)/$', vote),
    url(r'^api/tx/(?P<txid>[a-fA-F0-9]{64})/$', api_tx),
    url(r'^dashwood/$', admin_login),
    url(r'^dashwood/dashboard/$', admin_dashboard),
    url(r'^dashwood/logout/$', admin_logout),
    url(r'^dashwood/list/$', admin_list),
    url(r'^dashwood/list/(?P<p>\d+)/$', admin_list),
    url(r'^dashwood/list/(?P<p>\d+)/(?P<bid>\d+)/(?P<v>\d+)/$', admin_list),
    url(r'^dashwood/lot/(?P<bid>\d+)/$', admin_lot),
    url(r'^dashwood/lot/(?P<bid>\d+)/(?P<confirm>\d+)/$', admin_lot),
]
