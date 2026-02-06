# 🚲 Velo’v Realtime Data Pipeline

## Made By
**Omayma El Kasbaoui** and **Timothé Chiesi**

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

### Airflow

**Access:** (Airflow URL)[http://localhost:8080]

**Credentials:** 
- **Username:** `airflow`
- **Password:** `airflow`

All DAGs are located in the `airflow/dags/` folder and will be parsed automatically.

### Grafana

**Access:** (Grafana URL)[http://localhost:3000]

**Credentials:**
- **Username:** `admin` 
- **Password:** `admin`

[!TIP] On your first login, you will be prompted to update your password. You can click **Skip** to continue using the default credentials.

**Available Dashboards:** The environment is fully provisioned. Once logged in, you will find two pre-configured dashboards:
- **MongoDB Data Lake:** Tracks raw data ingestion stats.
- **PostgreSQL Final Database:** Visualizes processed and structured data metrics.

### MongoDB

**Access:** (mongodb://localhost:27017)[mongodb://localhost:27017]

**Credentials:** no username and password

**Database:** `velov_db`

### PostgreSQL

**Access:** (jdbc:postgresql://localhost:5433/airflow)[jdbc:postgresql://localhost:5433/airflow]

**Credentials:**
- **Username:** `airflow` 
- **Password:** `airflow`

**Database:** `airflow`
**Table:** `velov_processed`

## 🛑 Stop the Stack

```bash
docker compose down
```

To remove volumes:

```bash
docker compose down -v
```
