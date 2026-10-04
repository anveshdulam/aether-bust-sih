import asyncio
from app.db.client import connect_db
from data.generator import generate_run

async def main():
    await connect_db()
    generate_run('smoke_test_run', '.')

asyncio.run(main())
