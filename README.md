# Routio

## Table of contents
- [Application Structure](#application-structure)
- [Application Startup](#application-startup)
- [Environment Variables](#environment-variables)
    - [Backend](#1-backend)
    - [Frontend](#2-frontend)
    - [Root Directory](#3-root-directory)
- [Running Application](#running-application)
    - [Running the Application Locally](#1-running-the-application-locally)
    - [Running the Application with Docker – Development](#2-running-the-application-with-docker---development)
    - [Running the Application with Docker – Production](#3-running-the-application-with-docker---production)
- [Database Initialization](#database-initialization)
    - [SQL Dump](#1-sql-dump)
    - [Python Script](#2-python-script)
- [Changing Ports](#changing-ports)
    - [Running the Application locally](#running-the-application-locally)
    - [Running the Application with Docker – Development](#running-the-application-with-docker--development)

---

## Application Structure
The application is divided into logically separated folders and files. The basic app structure is shown below:

```
.
├── backend/
│   ├── src/
│   │   ├── api/                    # API interfaces
│   │   ├── config/                 # Server configuration files
│   │   ├── database/               # Database layer
│   │   ├── models/                 # Python type annotations
│   │   ├── otp/                    # Communication with OTP 2
│   │   ├── prediction/             # Model training scripts
│   │   ├── routers/                # Transport mode implementations
│   │   ├── routing_engine/         # Route planning system
│   │   ├── service/                # Dataset processing services
│   │   ├── shared/                 # Shared utility classes
│   │   ├── districts.geojson       # Czech district boundaries
│   │   ├── main.py                 # Main backend entrypoint
│   │   └── tcn_model.pt            # Trained TCN model
│   ├── requirements.dev.txt        # Development Python dependencies
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Production backend build
│   ├── Dockerfile.dev              # Development backend build
│   └── dump.sql                    # Database initialization script
│
├── frontend/
│   ├── public/                     # Static files and images
│   ├── src/                        # Frontend source code
│   ├── Dockerfile                  # Production frontend build
│   ├── Dockerfile.dev              # Development frontend build
│   ├── index.html                  # Main HTML file
│   ├── nginx.conf                  # Web server configuration
│   ├── package.json                # Frontend dependencies
│   └── vite.config.ts              # Vite configuration
│
├── docker-compose.dev.yml          # Development configuration
├── docker-compose.prod.yml         # Production configuration
├── LICENSE                         # Project license
└── README.md                       # Documentation and setup guide
```
---

## Application Startup
There are 3 ways to run the application.

**Each one consists of 3 steps**:
1. [Environment variables](#environment-variables)
2. [Running application](#running-application)
3. [Database initialization](#database-initialization)

**Note:** The server startup can take up to 10 minutes.
**Note:** If the ports used locally or in development Docker are already used on your machine, [click here](#changing-ports) to find out which files to edit.

---

## Environment Variables
The application uses environment variables for configuration. The `.env` files must be created before running the application.

### 1. Backend
The following variables must be defined in `backend/.env` to run the application:

| Variable        | Description               |
|-----------------|---------------------------|
| `LISSY_API_KEY` | Secret key for Lissy API  |
| `BEN_API_KEY`   | Secret key for Ben API    |
| `OPEN_WEATHER_API_KEY`   | Secret key for OpenWeather API    |

### 2. Frontend
The following variables must be defined in `frontend/.env.production` for production Docker build:

| Variable        | Value | Description               |
|-----------------|------- | ---------------------------|
| `VITE_BASE_URL`    | `/routio/`| Subdomain for production deployment   |
| `VITE_API_URL`    | `/routio/api` | API base URL based on nginx.conf   |

**Note:** Based on current nginx.conf `VITE_API_URL` must be `VITE_BASE_URL` + `api`

### 3. Root Directory
The following variables must be defined in `.env` for both development and production Docker build:

| Variable              | Description                                   |
|-----------------------|-----------------------------------------------|
| `POSTGRES_DB`         | Name of the PostgreSQL database               |
| `POSTGRES_USER`       | Username for database authentication          |
| `POSTGRES_PASSWORD`   | Password for the user                         |

---

## Running Application
- [Locally](#1-running-the-application-locally)
- [Development Docker](#2-running-the-application-with-docker---development)
- [Production Docker](#3-running-the-application-with-docker---production)

### 1. Running the Application Locally
Running the application locally consists of starting the backend and frontend. The backend can be run as follows:

1. Go to the backend directory.

```bash
cd backend
```

2. Create and activate virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install development requirements.
```bash
pip install -r requirements.dev.txt
```

4. Run the FastAPI server from `src/`.
```bash
cd src
python main.py
```

5. The server is running on:
```
http://localhost:8000
```

The frontend can be run from the root directory as follows:
1. Go to the frontend directory.
```bash
cd frontend
```

2. Install dependencies.
```bash
npm install
```

3. Run the application frontend.
```bash
npm run dev
```

4. The client is running on:
```bash
http://localhost:5173
```

### 2. Running the Application with Docker - Development

1. Build and start containers.
```bash
docker compose -f docker-compose.dev.yml up --build
```

2. Access the application:
- frontend
```bash
http://localhost:5173
```
- backend
```bash
http://localhost:8000
```

### 3. Running the Application with Docker - Production

1. Build and start containers.
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

2. Access the application:

```bash
http://domain_name/routio
```

---

## Database Initialization
After starting the application in Docker or locally, there are two options to load bike rack data into the database.

### 1. SQL Dump
If `dump.sql` is provided, this option can be used. To initialize database, run:
* Development Docker
```bash
docker compose -f docker-compose.dev.yml exec -T db \
bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backend/dump.sql
```
* Production Docker
```bash
docker compose -f docker-compose.prod.yml exec -T db \
bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backend/dump.sql
```
* Local development in project root directory run
```bash
source .env
psql -U $POSTGRES_USER -d $POSTGRES_DB < backend/dump.sql
```

### 2. Python Script
Initialize database using OSM data, run:
* Development Docker
```bash
docker compose -f docker-compose.dev.yml exec backend python -m database.osm
```
* Production Docker
```bash
docker compose -f docker-compose.prod.yml exec backend python -m database.osm
```
* Local development in `backend/src/` directory, run:
```bash
python -m database.osm
```
**Note:** Development requirements are necessary.  
**Note:** This process may take around 20 minutes depending on the machine.

---

## Changing Ports

### Running the Application Locally

Changing frontend port:

```bash
cd frontend/
npm run dev -- --port port
```

Changing backend port:
```bash
cd backend/
uvicorn main:app --host 127.0.0.1 --port port --reload
```
When changing the backend port, also update the URL in `frontend/src/components/config/config.ts`


### Running the Application with Docker – Development
If there is a need to change port numbers in development Docker, apply changes in `docker-compose.dev.yml`.
When changing the backend port, also update the URL in `frontend/src/components/config/config.ts`.

---
