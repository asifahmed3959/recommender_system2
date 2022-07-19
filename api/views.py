import os
import numpy as np
import pandas as pd
import difflib
import random
import logging

from django.apps import AppConfig
from django.conf import settings
from django.http import JsonResponse

from .apps import ApiConfig

from rest_framework.views import APIView
from rest_framework.response import Response

from collections import defaultdict


class Logger():
    @staticmethod
    def getLogger():
        return logging.getLogger(__name__)


def prepare_dataset():
    book_data_path = os.path.join(settings.MODELS, "books_data.txt")
    sentiment_data_path = os.path.join(settings.MODELS, "sentiment_data_final_final.csv")
    _pd_book_metadata = pd.read_csv(book_data_path)
    _pd_sentiment_data = pd.read_csv(sentiment_data_path)

    return _pd_book_metadata, _pd_sentiment_data

def get_book_info(book_ids, metadata):
    """
    Returns some basic information about a book given the book id and the metadata dataframe.
    """
    book_info = metadata[metadata['book_id'].isin(book_ids)][['book_id', 'title']]
    return book_info.to_dict(orient='records')

def get_user_info(df, user_id):
    user_info = df[(df.user_id == user_id)].sort_values(['rating'], ascending=[False]).head(10).to_numpy().tolist()
    #     random_sample = random.sample(user_info, 5)
    return user_info

def prep_for_prediction(random_user_list):
    return [tuple(x) for x in random_user_list]

def prediction_with_algo(algo, testset):
    return algo.test(testset)


def get_book_list_ids(top_n):
    iid_set = []
    for uid, user_ratings in top_n.items():
        uid, iid_set = (uid, [iid for (iid, _) in user_ratings])
    return iid_set

def get_top_n(predictions, n=10):
    """Return the top-N recommendation for each user from a set of predictions.

    Args:
        predictions(list of Prediction objects): The list of predictions, as
            returned by the test method of an algorithm.
        n(int): The number of recommendation to output for each user. Default
            is 10.

    Returns:
    A dict where keys are user (raw) ids and values are lists of tuples:
        [(raw item id, rating estimation), ...] of size n.
    """

    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n


# # TODO: change the default Entry Point text to handleWebhook
#
def handleWebhook(book_list):
    if len(book_list) == 0:
        return "Sorry it seems you have never read a book here, how about you try yourself a book, " \
               "and we will recommend books later"

    book_recommendation = "These are the books we suggest: "

    for i in range(len(book_list) - 1):
        book_recommendation += book_list[i]['title'] + ", "

    book_recommendation += book_list[i]['title'] + "."

    book_recommendation += " Those were our suggestions hope you love them."

    return book_recommendation



class WeightPrediction(APIView):
    def post(self, request):
        try:
            data = request.data

            user_id = int(data["queryResult"]["parameters"]["user_id"])
            # user_id = 1000

            print(user_id)
            #
            books_metadata, df = ApiConfig._pd_book_metadata, ApiConfig._pd_sentiment_data
            # # books_metadata, df = prepare_dataset()
            #
            user_info_data = get_user_info(df, user_id)

            test_set = prep_for_prediction(user_info_data)
            svd = ApiConfig.model
            predictions = prediction_with_algo(svd, test_set)
            top_n = get_top_n(predictions, 5)
            recommended_book_ids = get_book_list_ids(top_n)
            response_data = get_book_info(recommended_book_ids, books_metadata)

            response_data = handleWebhook(response_data)

        except Exception as e:
            print(e)
            Logger.getLogger().error(e)
            return Response ("some error occured", status=400)

        response = JsonResponse({"fulfillmentMessages": [{"text": {"text": [response_data]}}]}, status=200)
        response['Retry-after'] = 345  # seconds
        response['Token'] = request.META['HTTP_TOKEN']

        return response