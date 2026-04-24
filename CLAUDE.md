# Routio — kontext pro Claude

Webová aplikace s backendem (Python/FastAPI), frontendem (Vite/React) a PostGIS databází.

Pro obecné informace o architektuře serveru a deploy workflow viz kořenový [`CLAUDE.md`](../CLAUDE.md).

---

## Routio specifika

| Věc | Hodnota |
|-----|---------|
| URL prefix | `/routio` |
| Proxy kontejner | `routio-proxy` |
| Interní síť | `routioNetwork` |
| Lokální testovací port | `9091` |

---

## Potřebné env proměnné (`.env`)

```env
POSTGRES_DB=routio
POSTGRES_USER=...
POSTGRES_PASSWORD=...
LISSY_API_KEY=...
BEN_API_KEY=...
OPEN_WEATHER_API_KEY=...
```

Šablona je v souboru `env.prod`.
