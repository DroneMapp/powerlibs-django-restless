from django.conf.urls import patterns, include, url
import testapp.urls

urlpatterns = patterns('',  # NOQA
    url('', include(testapp.urls)),
)
