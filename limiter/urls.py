from django.urls import path
from limiter.views import PingView, CustomLimitView, StatsView

app_name = 'limiter'

urlpatterns = [
    path('ping/', PingView.as_view(), name='ping'),
    path('custom-limit/', CustomLimitView.as_view(), name='custom-limit'),
    path('stats/<str:identifier>/', StatsView.as_view(), name='stats'),
]

