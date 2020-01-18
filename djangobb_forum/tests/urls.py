from django.conf.urls import include, url


urlpatterns = [
    url(r'^forum/', include(('djangobb_forum.urls', 'djangobb_forum'), namespace='djangobb'))
]
