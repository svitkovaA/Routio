import os
import httpx
import osmium
import asyncpg
from typing import Optional
from config.datasets import OSM_PBF_PATH, OSM_PBF_URL

class BicycleRackHandler(osmium.SimpleHandler):
    def __init__(self, conn: asyncpg.Connection):
        super().__init__()
        self.conn = conn
        self.buffer = []

    def node(self, n: osmium.osm.Node):
        if n.tags.get("amenity") != "bicycle_parking":
            return

        if not n.location.valid():
            return

        osm_id = n.id
        lat = n.location.lat
        lon = n.location.lon

        capacity: Optional[int] = None
        if "capacity" in n.tags:
            try:
                capacity = int(n.tags["capacity"])
            except ValueError:
                pass

        self.buffer.append((osm_id, lat, lon, capacity))

async def bike_racks_empty(conn: asyncpg.Connection) -> bool:
    exists = await conn.fetchval("""
        SELECT EXISTS (SELECT 1 FROM bicycle_racks LIMIT 1)
    """)
    return not exists

async def insert_batches(conn: asyncpg.Connection, rows, batch_size=1000):
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        await conn.executemany(
            """
            INSERT INTO bicycle_racks (osm_id, lat, lon, capacity, geom)
            VALUES (
                $1, $2, $3, $4,
                ST_SetSRID(ST_MakePoint($3, $2), 4326)
            )
            ON CONFLICT (osm_id) DO NOTHING
            """,
            batch,
        )
        print(f"Inserted {len(batch)} bicycle racks")

async def download_osm_pbf() -> None:
    if os.path.exists(OSM_PBF_PATH):
        os.remove(OSM_PBF_PATH)

    os.makedirs(os.path.dirname(OSM_PBF_PATH), exist_ok=True)

    print("Downloading OSM PBF from Geofabrik")

    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
        async with client.stream("GET", OSM_PBF_URL) as response:
            response.raise_for_status()
            with open(OSM_PBF_PATH, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)

    print("Downloaded OSM PBF")

async def load_bike_racks(conn: asyncpg.Connection) -> None:
    await download_osm_pbf()

    if not os.path.exists(OSM_PBF_PATH):
        raise FileNotFoundError(f"OSM PBF not found: {OSM_PBF_PATH}")
    
    handler = BicycleRackHandler(conn)
    handler.apply_file(OSM_PBF_PATH, locations=True)

    await insert_batches(conn, handler.buffer)

    print("Finished OSM import")

# End of file osm.py
