import os
import joblib
from django.apps import AppConfig
from django.conf import settings
import pandas as pd


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    MODEL_FILE = os.path.join(settings.MODELS, "svdModel.joblib")
    book_data_path = os.path.join(settings.MODELS, "books_data.txt")
    sentiment_data_path = os.path.join(settings.MODELS, "sentiment_data_final_final.csv")
    # _pd_book_metadata = pd.read_csv(book_data_path)
    # _pd_sentiment_data = pd.read_csv(sentiment_data_path)
    model = joblib.load(MODEL_FILE)
