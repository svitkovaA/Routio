# Návod na deploy — Routio

Tento návod popisuje, jak nasadit projekt na server **dexter.fit.vutbr.cz**.

---

## Předpoklady

- Přístup na server dexter (SSH)
- Přístup do Docker registry `dexter.fit.vutbr.cz` (přihlašovací údaje od správce)
- Docker a Docker Compose nainstalované lokálně

---

## Architektura na serveru

Na serveru běží globální nginx (`base-nginx-1`), který přijímá veškerý provoz na portech 80 a 443 a podle URL prefixu ho přeposílá na proxy kontejner příslušného projektu. Každý projekt běží ve vlastní Docker síti a do globální sítě (`kristyna-dev`) se připojuje pouze přes svůj proxy kontejner.

```
Internet → base-nginx-1 → kristyna-dev síť → routio-proxy → routio-frontend
                                                           → routio-backend → routio-db
```

---

## Krok 1: Přihlášení do Docker registry

```bash
docker login dexter.fit.vutbr.cz
```

Zadej přihlašovací údaje k registry (získáš od správce serveru).

---

## Krok 2: Build a push obrazů

Lokálně v kořenovém adresáři projektu:

```bash
docker compose -f docker-compose.build.yml build
docker compose -f docker-compose.build.yml push
```

Tím se sestaví Docker obrazy backendu a frontendu a nahrají se do registry.

---

## Krok 3: Příprava souborů na serveru

Na server je potřeba zkopírovat tyto soubory:

| Soubor | Kam na serveru |
|--------|----------------|
| `docker-compose.prod.yml` | `/home/lazy_lemour/jirka/routio/` |
| `nginx.conf` | `/home/lazy_lemour/jirka/routio/` |
| `.env` | `/home/lazy_lemour/jirka/routio/` |

Kopírování přes scp:

```bash
scp docker-compose.prod.yml nginx.conf .env <user>@dexter.fit.vutbr.cz:/home/lazy_lemour/jirka/routio/
```

> **Poznámka:** `.env` obsahuje hesla — nikdy ho neukládej do gitu.

---

## Krok 4: Přidat projekt do globálního nginx

Soubor `dexter.conf` (konfigurace globálního nginx) musí obsahovat záznam pro Routio. Ten už je přidaný:

```nginx
location ^~ /routio {
   set $routio http://routio-proxy;
   proxy_pass $routio$request_uri;
}
```

Pokud jsi `dexter.conf` upravoval, zkopíruj ho na server na správné místo a reloadni globální nginx (viz Krok 6).

---

## Krok 5: Spuštění na serveru

Připoj se na server přes SSH a přejdi do adresáře projektu:

```bash
ssh <user>@dexter.fit.vutbr.cz
cd /home/lazy_lemour/jirka/routio
```

Stáhni nejnovější obrazy z registry a spusť kontejnery:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Ověř, že vše běží:

```bash
docker ps --filter name=routio
```

Měly by běžet čtyři kontejnery: `routio-db`, `routio-backend`, `routio-frontend`, `routio-proxy`.

---

## Krok 6: Reload globálního nginx

Pokud jsi změnil `dexter.conf`, je potřeba reloadnout globální nginx:

```bash
docker exec base-nginx-1 nginx -s reload
```

---

## Krok 7: Ověření

Otevři v prohlížeči: **https://dexter.fit.vutbr.cz/routio**

---

## Import databázového dumpu

Pokud potřebuješ naimportovat data z dumpu (soubor `dump.sql` musí být na serveru):

```bash
docker exec -i routio-db bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < dump.sql
```

Ověření, že tabulky existují:

```bash
docker exec -it routio-db bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'
```

---

## Aktualizace (nová verze aplikace)

Při každé nové verzi opakuj kroky 2 a 5:

```bash
# Lokálně — build a push
docker compose -f docker-compose.build.yml build
docker compose -f docker-compose.build.yml push

# Na serveru — pull a restart
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Docker Compose automaticky rekreuje pouze kontejnery, jejichž obraz se změnil.

---

## Lokální testování před deployem

Chceš-li otestovat prod konfiguraci lokálně před nahráním na server:

```bash
# Jednorázově — vytvoř lokální síť
docker network create kristyna-dev

# Spusť
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml up -d
```

Aplikace bude dostupná na `http://localhost:9091/routio`.

Po otestování:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down
docker network rm kristyna-dev
```

---

## Řešení problémů

**Kontejner nenaběhl:**
```bash
docker logs routio-backend --tail 50
docker logs routio-proxy --tail 50
```

**Stránka vrací 502 Bad Gateway:**
Proxy nemůže dosáhnout na frontend nebo backend. Zkontroluj, zda všechny kontejnery běží (`docker ps --filter name=routio`).

**Stránka vrací 404 Not Found:**
Zkontroluj konfiguraci v `nginx.conf` a zda je záznam v `dexter.conf` správně nastaven.

**Změna `.env` se neprojevila:**
```bash
docker compose -f docker-compose.prod.yml up -d --force-recreate backend
```
