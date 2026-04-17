"""
file: osm.py

OSM data loader.
"""

import asyncio
import os
import httpx
import osmium
import asyncpg          # type: ignore[import-untyped]
from typing import List, Tuple
from database.db import close_pool, create_conn, init_pool
from config.datasets import OSM_PBF_PATH, OSM_PBF_URL

class AddressHandler(osmium.SimpleHandler):
    """
    OSM handler that extracts address nodes.
    """
    def __init__(self):
        super().__init__()
        self.buffer: List[Tuple[int, str, str, float, float]] = []

    def node(self, n):
        """
        Process OSM node and collect address information.
        """
        street = n.tags.get("addr:street")
        streetnumber = n.tags.get("addr:streetnumber")

        # Skip nodes without full address information
        if not street or not streetnumber:
            return

        # Skip nodes without full address information
        if not n.location.valid():
            return

        lat = n.location.lat
        lon = n.location.lon

        # Skip nodes without valid coordinates
        self.buffer.append(
            (n.id, street, streetnumber, lat, lon)
        )

async def insert_addresses(conn: asyncpg.Connection, rows):
    """
    Insert address records into the database.

    Args:
        conn: Active database connection
        rows: Address rows extracted from OSM
    """
    await conn.executemany(
        """
        INSERT INTO osm_addresses
        (osm_id, street, streetnumber, lat, lon, geom)
        VALUES (
            $1,$2,$3,$4,$5,
            ST_SetSRID(ST_MakePoint($5,$4),4326)
        )
        ON CONFLICT DO NOTHING
        """,
        rows
    )

class BicycleRackHandler(osmium.SimpleHandler):
    """
    OSM handler that extracts bicycle parking nodes.
    """
    def __init__(self, conn: asyncpg.Connection):
        super().__init__()
        self.conn = conn
        self.buffer: List[Tuple[int, float, float, int | None]]= []

    def node(self, n):
        """
        Process OSM node and collect bicycle rack information.
        """

        # Only process bicycle parking nodes
        if n.tags.get("amenity") != "bicycle_parking":
            return

        if not n.location.valid():
            return

        osm_id = n.id
        lat = n.location.lat
        lon = n.location.lon

        capacity: int | None = None
        # Attempt to parse capacity tag
        if "capacity" in n.tags:
            try:
                capacity = int(n.tags["capacity"])
            except ValueError:
                pass

        self.buffer.append((osm_id, lat, lon, capacity))

async def bike_racks_empty(conn: asyncpg.Connection) -> bool:
    """
    Check whether the bicycle_racks table is empty.
    """
    exists = await conn.fetchval("""
        SELECT EXISTS (SELECT 1 FROM bicycle_racks LIMIT 1)
    """)
    return not exists

async def insert_batches(conn: asyncpg.Connection, rows, batch_size: int = 1000):
    """
    Insert bicycle rack records in batches.

    Args:
        conn: Active database connection
        rows: Rack records extracted from OSM
        batch_size: Number of rows inserted per batch
    """
    processed = []
    for osm_id, lat, lon, capacity in rows:
        processed.append((osm_id, lat, lon, capacity))

    for i in range(0, len(processed), batch_size):
        batch = processed[i:i + batch_size]

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

async def resolve_rack_addresses(conn: asyncpg.Connection):
    """
    Assign names to bicycle racks.
    """

    print("Resolving rack addresses")

    await conn.execute("""
        UPDATE bicycle_racks r
        SET name = COALESCE(
            (
                SELECT street || ' ' || streetnumber
                FROM osm_addresses
                WHERE ST_DWithin(
                    r.geom,
                    geom,
                    0.0005
                )
                ORDER BY r.geom <-> geom
                LIMIT 1
            ),
            'BikeRack (' ||
            ROUND(r.lat::numeric, 5) || ', ' ||
            ROUND(r.lon::numeric, 5) || ')'
        )
        WHERE r.name IS NULL;
    """)

    print("Finished resolving addresses")

async def download_osm_pbf() -> None:
    """
    Download the OSM PBF dataset from Geofabrik
    """

    # Remove old dataset if it exists
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
    """
    Import bicycle rack data from OSM.
    
    Args:
        conn: Active database connection
    """
    await download_osm_pbf()

    if not os.path.exists(OSM_PBF_PATH):
        raise FileNotFoundError(f"OSM PBF not found: {OSM_PBF_PATH}")

    # Extract addresses from OSM nodes
    addr_handler = AddressHandler()
    addr_handler.apply_file(OSM_PBF_PATH, locations=True)

    await insert_addresses(conn, addr_handler.buffer)
    
    # Extract bicycle racks
    handler = BicycleRackHandler(conn)
    handler.apply_file(OSM_PBF_PATH, locations=True)

    await insert_batches(conn, handler.buffer)

    # Assign rack names
    await resolve_rack_addresses(conn)

    print("Finished OSM import")

async def main() -> None:
    """
    Executes bike rack loading to database.
    """
    await init_pool()
    with create_conn() as conn:
        await load_bike_racks(conn)

    await close_pool()

if __name__ == "__main__":
    asyncio.run(main())

# End of file osm.py
