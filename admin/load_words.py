import argparse
import json
import logging
import os
import requests
import time

from dateutil import parser
from decouple import config
from pathlib import Path
from pymongo import MongoClient
from ratelimiter import RateLimiter

DB_NAME = "mw"
DB_COLLECTION = "definitions"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s -- %(message)s')
LOGGER = logging.getLogger("dictionary")

# todo Keep this from repeating code that appears in vortaro/settings.py
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

def get_database():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://{username:}:{password:}@{host:}/?retryWrites=true&w=majority".format(
        username=config("MONGO_DB_USER"),
        password=config("MONGO_DB_PASS"),
        host=config("MONGO_DB_HOST")
    )

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    return client[DB_NAME]

def has_definition(json_tree):
    for branch in json_tree:
        if "meta" in branch:
            return True
    return False


# 1000 calls per day
@RateLimiter(max_calls=1000, period=3600*24)
def get_definition(word):
    url = f"https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={config('MW_API_KEY')}"
    resp = requests.get(url)

    if resp.status_code != 200:
        logging.warning(f"invalid API response: {word}")
        return time.localtime(), None

    json_entry = json.loads(resp.text)
    if not has_definition(json_entry):
        logging.warning(f"word not found: {word}")
        return time.localtime(), None

    return time.localtime(), resp.text


def save_entry(db_collection, word, query_time, entry, overwrite=False):
    if not overwrite:
        if db_collection.count_documents({"word": word}) != 0:
            LOGGER.info(f"word already appears in DB: {word}")
            return False
    else:
        db_collection.delete_many({"word": word})

    try:
        db_collection.insert_one({
            "word": word,
            "query_time": parser.parse(time.asctime(query_time)),
            "api_response": entry
        })
    except:
        LOGGER.error(f"could not write to DB: {word}")
        return False
    else:
        LOGGER.info(f"successfully wrote to DB: {word}")

    return True


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Batch loader of words for for Vorto')
    arg_parser.add_argument('--input', action='store', required=True, help='text file of input words')
    arg_parser.add_argument('--overwrite', action='store_true')
    args = arg_parser.parse_args()

    if not os.path.exists(args.input):
        LOGGER.error(f"Input file path does not exist: {args['input']}")
        exit(1)

    with open(args.input) as file:
        words = [line.strip() for line in file]

    # Get the database
    dbname = get_database()

    # Get the collection
    db_collection = dbname[DB_COLLECTION]

    # Get all the definition
    for word in words:
        word = word.strip().lower()

        query_time, api_response = get_definition(word)
        if api_response is None:
            LOGGER.error(f"could not lookup definition: {word}")
            continue

        save_entry(db_collection, word, query_time, api_response, args.overwrite)


