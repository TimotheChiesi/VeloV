import requests
import pymongo
import os

class VeloVExtractor:
    def __init__(self):
        # Read from the environment variables defined in your .env / docker-compose
        self.api_url = os.getenv("API_URL")
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB_NAME")
        self.collection_name = os.getenv("MONGO_COLLECTION")

    def fetch(self):
        response = requests.get(self.api_url)
        response.raise_for_status()
        return response.json().get('values', [])

    def save(self, data):
        client = pymongo.MongoClient(self.mongo_uri)
        db = client[self.db_name]
        db[self.collection_name].insert_many(data)
        client.close()

    def run(self):
        data = self.fetch()
        if data:
            self.save(data)

if __name__ == "__main__":
    extractor = VeloVExtractor()
    extractor.run()
    print("DONE")