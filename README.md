# Routio

## Table of contents
- [Application overview](#application-overview)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Running the app](#running-the-app)
- [Environment variables](#environment-variables)

## Application overview
Application Routio was developed as part of the bachelor's thesis at the Faculty of Information Technology, Brno University of Technology, under the supervision of Ing. Jiří Hynek, Ph.D. The application supports both unimodal routing, where only one transport mode is used, and multimodal routing, combining multiple modes within a single journey. Application supports routing for public transport, walking and both private bicycles and shared bicycles.

## Architecture
Application Routio follows a client-server architecture:

The **frontend** is implemented in React and TypeScript. The Material UI components are used as a part of the application. For the map visualization the Leaflet library is used. The application provides support for 3 languages with the i18next support.

The **backend** is implemented in Python and the FastAPI is used.

The architecture is enriched with **data layer**, consisting of open data standards and external services. The used open data standards includes:
- GTFS for public transport,
- GTFS-RT for actual vehicle positions,
- GBFS for information about shared bicycles.

External services includes:
- OpenTripPlanner for routing public transport, walk, bicycle and retrieving information about shared bicycle stations locations,
- Lissy API for retrieving information about route shapes and historical delays of public transport connections,
- Geofabrik for retrieving information about the bicycle racks,
- OpenWeather API for retrieving information about weather,
- Photon for retrieving location suggestions via geocoding,
- Nominatim for reverse geocoding.

---

## Project structure
The application is divided into logically separated folders and files. The basic app structure is shon below:

```
.
|-- backend/
|   |-- src/
|   |-- Dockerfile
|   |-- Dockerfile.dev
|   |-- requirements.txt
|   |-- requirements.dev.txt
|-- frontend/
|   |-- public/
|   |-- src/
|   |-- Dockerfile
|   |-- Dockerfile.dev
|   |-- eslint.config.js
|   |-- index.html
|   |-- nginx.conf
|   |-- package-lock.json
|   |-- package.json
|   |-- tsconfig.app.json
|   |-- tsconfig.json
|   |-- tsconfig.node.json
|   |-- vite.config.ts
|-- .gitignore
|-- docker-compose.dev.yml
|-- docker-compose.prod.yml
|-- LICENSE
|-- Readme.md
```
---

## Running the app
There are 3 possibilities how to run the application.

### 1. Running the Application Locally
The local running consists of starting backend and frontend. The backend can be run as follows:

1. Go to the backend directory

```bash
cd backend
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

3. Install requirements
```bash
pip install -r requirements.txt
```

4. Optionally install development requirements which are necessary for model training and database initialization.
```bash
pip install -r requirements.dev.txt
```

4. Run the FastAPI server from src/
```bash
cd src
python main.py
```

5. The server is running on
```
http://localhost:8000
```

The frontend can be run from root directory as follows:
1. Go to the frontend directory
```bash
cd frontend
```

2. Install dependencies
```bash
npm install
```

3. Run the application frontend
```bash
npm run dev
```

4. The client is running on
```bash
http://localhost:5173
```

### 2. Running the Application with Docker - Development

1. Build and start containers
```bash
docker compose -f docker-compose.dev.yml up --build
```

2. Access application
- frontend
```bash
http://localhost:5173
```
- backend
```bash
http://localhost:8000
```

### 3. Running the Application with Docker - Production

1. Build and start containers
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

2. Access application at address

```bash
http://domain_name/routio
```

## Database initialization
After starting the application in docker or locally, there are two options to load bike rack data into the database.

### 1. SQL Dump
If `dump.sql` is provided this option is possible. To initialize database run:
* Development docker
```bash
docker compose -f docker-compose.dev.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB < dump.sql
```
* Production docker
```bash
docker compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB < dump.sql
```
* Local development in project root directory run
```bash
psql -U $POSTGRES_USER -d $POSTGRES_DB < dump.sql
```

### 2. Python script
Initialize database using OSM data, run:
* Development docker
```bash
docker compose -f docker-compose.dev.yml exec backend python -m database.osm
```
* Production docker
```bash
docker compose -f docker-compose.prod.yml exec backend python -m database.osm
```
* Local development
```bash
python -m database.osm
```
**Note:** Development requirements necessary.
**Note:** This takes a long time around 20 minutes according to machine.

## Environment variables
The application uses environment variables for configuration. The `.env` files have to be created before running the application.

### 1. Backend
The following variables must be defined in `backend/.env` to run the application:

| Variable        | Description               |
|-----------------|---------------------------|
| `LISSY_API_KEY` | Secret key for Lissy API  |
| `BEN_API_KEY`   | Secret key for Ben API    |
| `OPEN_WEATHER_API_KEY`   | Secret key for OpenWeather API    |

### 2. Frontend
The following variables must be defined in `frontend/.env.production` for production docker build:

| Variable        | Description               |
|-----------------|---------------------------|
| `VITE_BASE_URL`    | Subdomain for production deployment   |
| `VITE_API_URL`    | API base URL based on nginx.conf   |

**Note:** Based on current nginx.conf `VITE_API_URL` must be `VITE_BASE_URL` + `api/`

### 3. Root directory
The following variables must be defined in `.env` for both development and production docker build:

| Variable              | Description                                   |
|-----------------------|-----------------------------------------------|
| `POSTGRES_DB`         | Name of the PostgreSQL database               |
| `POSTGRES_USER`       | Username for database authentication          |
| `POSTGRES_PASSWORD`   | Password for the user                         |
