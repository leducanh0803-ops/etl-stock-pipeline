# ETL Stock Pipeline

A modern data engineering pipeline for ingesting, storing, and transforming S&P 500 stock market data using Polygon.io, PostgreSQL, Airflow, and dbt.

## Overview

This project demonstrates an end-to-end data engineering workflow:

1. Extract stock market data from Polygon.io
2. Load raw data into PostgreSQL
3. Perform incremental updates using UPSERT logic
4. Orchestrate workflows with Apache Airflow
5. Transform and model data using dbt
6. Containerize all services using Docker

The pipeline automatically collects daily OHLCV market data and company metadata for S&P 500 companies.

---

## Architecture

```text
                +----------------+
                | Polygon.io API |
                +-------+--------+
                        |
                        v
                +----------------+
                |   Extractor     |
                |   Python ETL    |
                +-------+--------+
                        |
                        v
                +----------------+
                |   PostgreSQL   |
                |  Raw Storage   |
                +-------+--------+
                        |
                        v
                +----------------+
                |      dbt       |
                | Transformations|
                +-------+--------+
                        |
                        v
                +----------------+
                | Analytics Layer|
                +----------------+

                        ^
                        |
                +----------------+
                |    Airflow     |
                | Orchestration  |
                +----------------+
```

---

## Project Structure

```text
etl-stock-pipeline/
│
├── airflow/
│   └── dags/
│       └── orchestrator.py
│
├── api-request/
│   ├── extractor.py
│   ├── insert_logic.py
│   ├── pipeline.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── dbt/
│   ├── my_project/
│   ├── profiles.yml
│   ├── logs/
│   └── Dockerfile
│
├── postgres/
│   └── airflow_init.sql
│
├── docker-compose.yaml
└── README.md
```

---

## Features

### Market Data Extraction

* Retrieves S&P 500 constituents dynamically
* Pulls historical OHLCV data
* Supports 2 years of daily market history
* Collects company metadata from Polygon

### Incremental Loading

* Automatic table creation
* Dynamic schema generation from DataFrames
* PostgreSQL UPSERT support
* Duplicate prevention using unique constraints

### Airflow Orchestration

* DAG-based scheduling
* Automated pipeline execution
* Monitoring and retry capabilities

### dbt Modeling

* SQL-based transformations
* Version-controlled analytics models
* Reproducible data workflows

### Containerized Deployment

* Dockerized ETL service
* Dockerized dbt environment
* PostgreSQL service integration
* Single-command startup using Docker Compose

---

## Data Sources

### Polygon.io

The pipeline uses Polygon's REST API to retrieve:

#### Daily OHLCV Data

```text
Open
High
Low
Close
Volume
VWAP
```

#### Company Metadata

```text
Ticker
Company Name
Industry
Market
Address
Branding
Exchange Information
```

---

## Database Design

### Raw OHLCV Table

| Column          | Description    |
| --------------- | -------------- |
| date            | Trading date   |
| ticker          | Stock symbol   |
| open            | Opening price  |
| high            | Highest price  |
| low             | Lowest price   |
| close           | Closing price  |
| volume          | Trading volume |
| weighted_volume | VWAP           |

Primary uniqueness:

```sql
UNIQUE(date, ticker)
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/leducanh0803-ops/etl-stock-pipeline.git

cd etl-stock-pipeline
```

### Environment Variables

Create a `.env` file:

```env
API_KEY_MASSIVE=YOUR_POLYGON_KEY

API_URL=https://api.polygon.io

DB_HOST=postgres_containers
DB_NAME=db
DB_USER=db_user
DB_PASSWORD=db_password
```

---

## Running Locally

Start all services:

```bash
docker compose up --build
```

Run ETL manually:

```bash
python pipeline.py
```

Run dbt models:

```bash
dbt run
```

Run tests:

```bash
dbt test
```

---

## Example Workflow

### Initial Load

1. Download S&P 500 tickers
2. Pull 2 years of OHLCV history
3. Create PostgreSQL tables
4. Load historical data

### Daily Update

1. Fetch previous trading day's data
2. Perform UPSERT
3. Update existing records
4. Insert new records

---

## Future Improvements

* Object storage layer (S3 / MinIO)
* Data quality checks using Great Expectations
* CI/CD with GitHub Actions
* Data warehouse integration
* Partitioned PostgreSQL tables
* Kafka streaming ingestion
* Feature store for machine learning workloads

---

## Tech Stack

* Python
* Pandas
* SQLAlchemy
* PostgreSQL
* Polygon.io API
* Apache Airflow
* dbt
* Docker
* Docker Compose

---

## Learning Objectives

This project demonstrates practical experience with:

* ETL pipeline development
* Data modeling
* Incremental loading strategies
* Workflow orchestration
* Containerized data platforms
* Analytics engineering with dbt

---

## License

MIT License
