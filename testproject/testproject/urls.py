from django.conf.urls import include, url
import testapp.urls

urlpatterns = [
    url('', include(testapp.urls)),
]
