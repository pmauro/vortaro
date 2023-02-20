import public_site.mw as mw

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from pymongo import MongoClient
from random import choice
from threading import local

DB_NAME = "mw"
DB_COLLECTION = "definitions"

_mongo_client = local()
def mongo_client():
    client = getattr(_mongo_client, 'client', None)
    if client is None:
        client = MongoClient(settings.MONGODB_URI)
        _mongo_client.client = client
    return client

def main(request):
    db_docs = mongo_client()[DB_NAME][DB_COLLECTION].find()

    word_list = list(db_docs)
    cur_word = choice(word_list)
    definition = mw.parse(cur_word['word'], cur_word['api_response'][1:-1])

    context = {'word_list': sorted(w['word'] for w in word_list), 'definition': definition.to_dict() }
    return render(request, 'public_site/home.html', context)

# def menu(request):
#     db_docs = mongo_client()[DB_NAME][DB_COLLECTION].find()
#     context = {'word_list': sorted(d['word'] for d in db_docs)}
#     return render(request, 'public_site/menu.html', context)

def definition(request, word):
    num_records = mongo_client()[DB_NAME][DB_COLLECTION].count_documents({'word': word})
    if num_records == 0:
        return HttpResponse("word not found")
    elif num_records > 1:
        return HttpResponse("multiple records found")

    db_doc = mongo_client()[DB_NAME][DB_COLLECTION].find_one({"word": word})
    definition = mw.parse(word, db_doc['api_response'][1:-1])

    return render(request, 'public_site/word_card.html', {'definition': definition.to_dict()})