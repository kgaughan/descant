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
    create_engine,
)

metadata = MetaData()

sites = Table(
    "sites",
    metadata,
    Column("site_id", CHAR(36), primary_key=True),
    Column("secret_key", CHAR(64), nullable=False),
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


def create_tables():
    metadata.create_all(create_engine("sqlite:///example.db", echo=True))
