# Deploy — Routio

Pro serverové detaily a obecný workflow viz kořenový [`README.md`](../README.md).

---

## Build a push

```bash
docker compose -f docker-compose.build.yml build
docker compose -f docker-compose.build.yml push
```

---

## Spuštění na serveru

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker ps --filter name=routio
```

---

## Lokální testování

```bash
docker network create kristyna-dev
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml up -d
# dostupné na http://localhost:9091/routio

docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down
docker network rm kristyna-dev
```

---

## Import DB dumpu

```bash
bash configure/configure.sh
```
