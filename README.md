# 🚲 Velo’v Realtime Data Pipeline

## Made By
**Omayma El Kasbaoui** and **Timothé Chiesi**

This project fetches Velo’v bike station data in real time, processes it with **Airflow**, stores raw data in **MongoDB**, and writes cleaned, deduplicated data into **PostgreSQL**.  
Monitoring is provided via **Prometheus** and **Grafana**, and the stack runs fully in **Docker**.

## Overview

This project leverages the Grand Lyon’s continuous API to monitor real-time statuses of VeloV bike-sharing stations in Lyon. The pipeline automatically aggregates, cleans, and analyzes station data for decision-making, maintenance, and operational insights.

**Data Flow & Processing**

1. Data Ingestion

- Continuous API Polling: Every 5 minutes, the pipeline fetches live status of all VeloV stations via the Grand Lyon API.
- Storage: Raw data is stored in a MongoDB data lake, preserving temporal context and raw records for auditing.

2. Data Transformation & Validation

- Cleaning Filter: A Python script processes the data, discarding:
 - Invalid/duplicate entries.
 - Station records that haven’t been updated since the last run.
- Change Detection: Only new or updated data is retained for downstream analysis.

3. Storage & Analytics

- PostgreSQL Database: Cleaned data is loaded into PostgreSQL, where:
 - Historical updates for each station are preserved in a time-series format.
 - Temporal statistics enable trends analysis (e.g., occupancy patterns, usage spikes).
 - Crowded station ranking identifies high-demand hubs for targeted services.

**Key Features**

- Real-Time Monitoring: Near-instant updates with 5-minute granularity.
- Auditability: Raw data retained in MongoDB for traceability.
- Scalable Analytics: PostgreSQL supports complex queries for operational insights.

**Technical Stack**

- API Layer: Grand Lyon Open Data API
- Storage:
  - MongoDB (raw data)
  - PostgreSQL (processed, statistical data)
- Processing: Python scripts (pipeline orchestration)

**Why This Matters**

- Proactive Maintenance: Detect anomalies (e.g., broken stations) to minimize downtime.
- Resource Optimization: Identify peak-demand stations to allocate staff/vehicles efficiently.
- Research Insights: Underpin studies on urban mobility, accessibility, or policy recommendations.


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

**Access:** [Airflow URL](http://localhost:8080)

**Credentials:** 
- **Username:** `airflow`
- **Password:** `airflow`

All DAGs are located in the `airflow/dags/` folder and will be parsed automatically.

![Airflow Web View](./assets/Airflow_Web_view.png)

### Grafana

**Access:** [Grafana URL](http://localhost:3000)

**Credentials:**
- **Username:** `admin` 
- **Password:** `admin`

[!TIP] On your first login, you will be prompted to update your password. You can click **Skip** to continue using the default credentials.

**Available Dashboards:** The environment is fully provisioned. Once logged in, you will find two pre-configured dashboards:
- **MongoDB Data Lake:** Tracks raw data ingestion stats.
![MongoDB Dashboard View](./assets/MongoDB-Dashboard.png)

- **PostgreSQL Final Database:** Visualizes processed and structured data metrics.
![PostgreSQL Dashboard View](./assets/PostgreSQL-Dasboard.png)

### MongoDB

**Access:** [mongodb://localhost:27017](mongodb://localhost:27017)

**Credentials:** no username and password

**Database:** `velov_db`

### PostgreSQL

**Access:** [jdbc:postgresql://localhost:5433/airflow](jdbc:postgresql://localhost:5433/airflow)

**Credentials:**
- **Username:** `airflow` 
- **Password:** `airflow`

**Database:** `airflow`
**Table:** `velov_processed`

### Streamlit dashboard

**Access:** [Streamlit Dashboard](http://localhost:8501/)

The Streamlit dashboard provides a visual analytics layer over the final processed data in PostgreSQL. It includes:
- **Real-time Alerts:** Identification of stations with no bikes available or no free docking slots.
- **System Overview:** Global Velo'v statistics and current station status.
- **Deep-Dive Analysis:** Occupancy patterns, geographic distribution, and temporal trends.
- **Station Profiles:** Detailed metrics for individual docking points.

**Note:** If you have just launched the docker-compose environment, your graphs may appear sparse. The dashboard will populate and show more complex trends as the data lake collects more history over time.

**Troubleshooting**

If the dashboard appears empty or doesn't reflect recent data updates:
1. Click the three dots (⋮) in the top-right corner.
2. Select "Clear cache".
3. Click "Rerun" to refresh the data connection.

**Gallery:**
![Streamlit View](./assets/Streamlit_1.png)
![Streamlit View](./assets/Streamlit_2.png)
![Streamlit View](./assets/Streamlit_3.png)
![Streamlit View](./assets/Streamlit_4.png)
![Streamlit View](./assets/Streamlit_5.png)
![Streamlit View](./assets/Streamlit_6.png)

## 🧪 Continuous Integration (CI)

This project includes a **GitHub Actions CI workflow** to ensure the Dockerized environment works correctly and that all required Python dependencies are installed in the Airflow webserver.

### CI Workflow Overview

The workflow performs the following steps on every push to `main` or feat/fix branches:

1. **Checkout repository** – pulls the latest code.  
2. **Create `.env` file** – dynamically generates environment variables from GitHub secrets.  
3. **Set up Docker Buildx** – enables multi-platform Docker builds.  
4. **Create Airflow folders** – ensures `dags`, `logs`, and `plugins` directories exist.  
5. **Fix permissions** – assigns proper ownership to `AIRFLOW_UID` so Airflow can write logs.  
6. **Initialize Airflow** – runs `airflow db migrate` and creates the default admin user.  
7. **Start the full stack** – launches all services.  
8. **Wait for webserver** – gives the Airflow webserver time to start.  
9. **Verify Python packages** – checks that required packages (`requests`, `beautifulsoup4`, `supabase`, `python-dotenv`, `pymongo`) are installed in the Airflow webserver container.  
10. **Check container health** – ensures no container failed to start.  
11. **Shutdown environment** – stops and removes all containers and optionally volumes.


## 🛑 Stop the Stack

```bash
docker compose down
```

To remove volumes:

```bash
docker compose down -v
```
