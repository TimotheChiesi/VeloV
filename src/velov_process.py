import os
import pymongo
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime


class VeloVProcessor:
    def __init__(self):
        # Mongo
        self.mongo_uri = os.getenv("MONGO_URI")
        self.mongo_db = os.getenv("MONGO_DB_NAME")
        self.mongo_collection = os.getenv("MONGO_COLLECTION")

        # Postgres
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

    def fetch_from_mongo(self):
        client = pymongo.MongoClient(self.mongo_uri)
        collection = client[self.mongo_db][self.mongo_collection]
        data = list(collection.find({}, {"_id": 0}))
        client.close()
        return data

    def clean_data(self, raw_data):
        cleaned = []

        for row in raw_data:
            number = row.get("number", 0)
            last_update = self._parse_date(row.get("last_update"))

            # Drop invalid rows
            if number == 0 or last_update is None:
                continue

            cleaned.append((
                number,
                last_update,
                row.get("name"),
                row.get("address"),
                row.get("commune"),
                row.get("bike_stands"),
                row.get("available_bike_stands"),
                row.get("available_bikes"),
                row.get("availability"),
                row.get("status"),
            ))

        return cleaned


    def _parse_date(self, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value.replace("Z", ""))
        except Exception:
            return None

    def write_to_postgres(self, data):
        insert_sql = """
            INSERT INTO velov_processed (
                number, last_update, name, address, commune,
                bike_stands, available_bike_stands, available_bikes,
                availability, status
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (number, last_update) DO NOTHING;
        """

        with self.pg_conn:
            with self.pg_conn.cursor() as cur:
                execute_batch(cur, insert_sql, data)

    def clear_mongo(self):
        client = pymongo.MongoClient(self.mongo_uri)
        collection = client[self.mongo_db][self.mongo_collection]
        collection.delete_many({})
        client.close()

    def ensure_table_exists(self):
        create_sql = """
        CREATE TABLE IF NOT EXISTS velov_processed (
            number INTEGER NOT NULL,
            last_update TIMESTAMP NOT NULL,
            name TEXT,
            address TEXT,
            commune TEXT,
            bike_stands INTEGER,
            available_bike_stands INTEGER,
            available_bikes INTEGER,
            availability TEXT,
            status TEXT,
            PRIMARY KEY (number, last_update)
        );
        """

        with self.pg_conn:
            with self.pg_conn.cursor() as cur:
                cur.execute(create_sql)


    def run(self):
        raw_data = self.fetch_from_mongo()
        if not raw_data:
            print("No data to process")
            return

        cleaned_data = self.clean_data(raw_data)

        self.ensure_table_exists()
        self.write_to_postgres(cleaned_data)
        self.clear_mongo()

        print(f"Processed {len(cleaned_data)} rows")



if __name__ == "__main__":
    VeloVProcessor().run()
