# Routio — kontext pro Claude

## O projektu

Webová aplikace s backendem (Python/FastAPI), frontendem (Vite/React) a PostGIS databází.
Deploy server: **dexter.fit.vutbr.cz**

---

## Architektura deploy serveru (dexter)

### Síťová topologie

```
Internet → base-nginx-1 (nginx:alpine, porty 80/443)
               ↓ kristyna-dev network
           <projekt>-proxy (nginx:1.19)
               ↓ <projekt>Network
           <projekt>-frontend    <projekt>-backend
                                      ↓ backend-db network
                                 <projekt>-db
```

- **`base-nginx-1`** — globální nginx, SSL termination, routuje podle path prefixu (`/routio`, `/carpub`, …)
- **`kristyna-dev`** — sdílená externí Docker síť, do které se připojuje proxy každého projektu
- **`<projekt>-proxy`** — per-projektový nginx, routuje `/api` na backend a statiku na frontend
- Každý projekt má vlastní interní síť `<projekt>Network`

### Konvence pojmenování

| Věc | Vzor | Příklad |
|-----|------|---------|
| Docker image | `dexter.fit.vutbr.cz/<projekt>/<projekt>-<služba>` | `dexter.fit.vutbr.cz/routio/routio-backend` |
| Container name | `<projekt>-<služba>` | `routio-proxy`, `routio-db` |
| Interní síť | `<projekt>Network` | `routioNetwork` |
| URL prefix | `/<projekt>` | `/routio` |

---

## Soubory projektu pro deploy

### `docker-compose.prod.yml` — pro server

- Používá **`image:`** (ne `build:`), obrazy z registry `dexter.fit.vutbr.cz`
- Obsahuje služby: `db`, `backend`, `frontend`, `proxy`
- Proxy je jediná služba připojená do `kristyna-dev`
- Env vars z root `.env` (přes `env_file: .env` + `environment:`)

### `docker-compose.build.yml` — pro lokální build a push

- Obsahuje jen `backend` a `frontend` s `build:` + `image:`
- Slouží výhradně k buildu a pushnutí obrazů do registry

### `docker-compose.local.yml` — pro lokální testování prod buildu

- Override soubor, přidá port na proxy kontejner
- Používá se spolu s `docker-compose.prod.yml`

### `nginx.conf` — projektový proxy (root adresáře)

- Routuje `/routio/api/` na backend (strippuje prefix)
- Routuje `/routio` na frontend (zachovává prefix)
- Mountuje se do `<projekt>-proxy` kontejneru

### `frontend/nginx.conf` — nginx uvnitř frontend image

- Pouze servuje statické soubory z `/usr/share/nginx/html`
- **Neobsahuje** proxy_pass na backend — to řeší projektový proxy

### `.env` (root, není v gitu)

- Obsahuje všechny proměnné: DB credentials i API klíče
- Docker Compose ho načítá automaticky pro substituci `${VAR}`
- Backend ho dostává přes `env_file: .env`

---

## Workflow: první deploy

### 1. Lokálně — build a push

```bash
docker login dexter.fit.vutbr.cz
docker compose -f docker-compose.build.yml build
docker compose -f docker-compose.build.yml push
```

### 2. Přidat projekt do globálního nginx (`dexter.conf`)

Do SSL server bloku přidat (vzor podle ostatních projektů):

```nginx
location ^~ /<projekt> {
   set $<projekt> http://<projekt>-proxy;
   proxy_pass $<projekt>$request_uri;
}
```

### 3. Na serveru — připravit soubory

Zkopírovat na server do adresáře projektu:
- `docker-compose.prod.yml`
- `nginx.conf`
- `.env`
- aktualizovaný `dexter.conf` → do umístění globálního nginx configu

### 4. Na serveru — spustit

```bash
# Síť kristyna-dev již existuje (sdílená), není třeba vytvářet
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### 5. Reloadnout globální nginx

```bash
docker exec base-nginx-1 nginx -s reload
```

---

## Workflow: aktualizace (nový build)

```bash
# Lokálně
docker compose -f docker-compose.build.yml build
docker compose -f docker-compose.build.yml push

# Na serveru
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

---

## Lokální testování prod buildu

```bash
# Vytvořit síť (jednorázově)
docker network create kristyna-dev

# Spustit
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml up -d

# Aplikace dostupná na http://localhost:<port>/<projekt>

# Po otestování
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down
docker network rm kristyna-dev
```

Port v `docker-compose.local.yml` zvolit volný (ověřit co je obsazené).

---

## Import DB dumpu

```bash
docker exec -i <projekt>-db bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < dump.sql
```

Ověření:
```bash
docker exec -it <projekt>-db bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'
```

---

## Vzorový `nginx.conf` (projektový proxy)

```nginx
events {}

http {
    include mime.types;

    upstream be {
        server <projekt>-backend:8000;
    }

    upstream fe {
        server <projekt>-frontend;
    }

    server {
        listen 80;

        include /etc/nginx/mime.types;

        location /<projekt>/api/ {
            proxy_pass http://be/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /<projekt> {
            proxy_pass http://fe/<projekt>/;
        }
    }
}
```

## Vzorový `frontend/nginx.conf`

```nginx
server {
    listen 80;

    root /usr/share/nginx/html;
    index index.html;

    location /<projekt>/ {
        try_files $uri $uri/ /<projekt>/index.html;
    }
}
```

Frontend Dockerfile kopíruje build do `/usr/share/nginx/html/<projekt>`:
```dockerfile
COPY --from=build /app/dist /usr/share/nginx/html/<projekt>
```

---

## Užitečné příkazy na serveru

```bash
# Stav kontejnerů projektu
docker ps --filter name=<projekt>

# Logy proxy
docker logs <projekt>-proxy --tail 50

# Reload globálního nginx
docker exec base-nginx-1 nginx -s reload

# Restart konkrétní služby
docker compose -f docker-compose.prod.yml restart backend
```
