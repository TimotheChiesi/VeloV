# 🚲 Velo’v Realtime Data Pipeline

This project fetches Velo’v bike station data in real time, processes it with **Airflow**, stores raw data in **MongoDB**, and writes cleaned, deduplicated data into **PostgreSQL**.  
Monitoring is provided via **Prometheus** and **Grafana**, and the stack runs fully in **Docker**.

## 🧱 Architecture Overview

```
API (Velo'v)
   ↓
Airflow (Extract)
   ↓
MongoDB (Raw data)
   ↓
Airflow (Process & Clean)
   ↓
PostgreSQL (Analytics-ready data)
```

## 🚀 Getting Started


### 2️⃣ Create the .env file

Create a file named `.env` at the project root.

```.env
# Airflow Image
AIRFLOW_IMAGE_NAME=apache/airflow:2.8.1

# Airflow Core
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__FERNET_KEY=-4Nudz_Y0PDu_S2uBx-jiIDCAy-jMiHqLcDXzyC7lX4=
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW_UID=10000

# Database Connection (Airflow Internal)
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow

# Postgres Settings
AIRFLOW_POSTGRES_USER=airflow
AIRFLOW_POSTGRES_PASSWORD=airflow
AIRFLOW_POSTGRES_DB=airflow

# Mongo
MONGO_URI=mongodb://mongodb:27017
MONGO_DB_NAME=velov_db
MONGO_COLLECTION=station_status

API_URL=https://data.grandlyon.com/fr/datapusher/ws/rdata/jcd_jcdecaux.jcdvelov/all.json?&start=1
```

## ▶️ Running the Project

### Initialize Airflow (first run only)

```bash
docker compose up airflow-init
```

### Start the full stack

```bash
docker compose up -d
```


## 🌐 Access the Services

- Airflow UI: http://localhost:8080 (airflow / airflow)

## 🛑 Stop the Stack

```bash
docker compose down
```

To remove volumes:

```bash
docker compose down -v
```
