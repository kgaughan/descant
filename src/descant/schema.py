from sqlalchemy import (
    CHAR,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.expression import Insert, Select, select

from . import crypto

__all__ = [
    "sites",
    "identities",
    "comments",
    "create_db",
    "execute",
    "query_secret_key",
]

metadata = MetaData()

sites = Table(
    "sites",
    metadata,
    Column("site_id", CHAR(36), primary_key=True),
    Column("secret_key", CHAR(81), nullable=False),
    Column("site", String(255)),
)

identities = Table(
    "identities",
    metadata,
    Column("identity_id", CHAR(36), primary_key=True),
    Column("confirmation_secret", CHAR(64), nullable=False),
    Column("site_id", CHAR(36), ForeignKey(sites.c.site_id), nullable=False),
    Column("ttl", DateTime(), nullable=False),
    Column("max_ttl", DateTime(), nullable=False),
    Column("confirmed", DateTime()),
)

comments = Table(
    "comments",
    metadata,
    Column("comment_id", Integer(), autoincrement="auto", primary_key=True),
    Column(
        "identity_id",
        CHAR(36),
        ForeignKey(identities.c.identity_id),
        nullable=False,
    ),
    Column("thread", CHAR(64), nullable=False),
    Column("submitted", DateTime(), nullable=False),
    Column("published", DateTime()),
    Column("name", String(255), nullable=False),
    Column("site", String(255)),
    Column("email", String(255)),
    Column("comment", Text(), nullable=False),
)


async def create_db(db):
    engine = create_async_engine(db)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await engine.dispose()


async def execute(db, clause):
    engine = create_async_engine(db)
    async with engine.begin() as conn:
        await conn.execute(clause)
        await conn.commit()
    await engine.dispose()


def query_secret_key(site_id: str) -> Select:
    return select(sites.c.secret_key).where(sites.c.site_id == site_id)


def insert_site(site_id: str, nonce: bytes, encrypted: bytes, name: str) -> Insert:
    return sites.insert().values(
        site_id=site_id,
        secret_key=".".join([crypto.b64encode(nonce), crypto.b64encode(encrypted)]),
        site=name,
    )
