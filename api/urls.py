from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import WeightPrediction

urlpatterns = [
    path('weight', WeightPrediction.as_view(), name = 'weight_prediction'),
]

urlpatterns = format_suffix_patterns(urlpatterns)