import datetime

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
from sqlalchemy.sql.expression import Insert, Select, Update, select

from . import crypto

__all__ = [
    "comments",
    "create_db",
    "execute",
    "identities",
    "query_secret_key",
    "sites",
]

metadata = MetaData()

sites = Table(
    "sites",
    metadata,
    Column("site_id", CHAR(36), primary_key=True),
    Column("secret_key", CHAR(64), nullable=False),
    Column("nonce", CHAR(16), nullable=False),
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


async def create_db(db: str) -> None:
    """Create the database.

    This is only intended to be invoked from the CLI.
    """
    engine = create_async_engine(db)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await engine.dispose()


async def execute(db: str, clause) -> None:
    """Execute a statement.

    This is only intended for simple configuration queries run from the CLI.
    """
    engine = create_async_engine(db)
    async with engine.begin() as conn:
        await conn.execute(clause)
        await conn.commit()
    await engine.dispose()


def query_secret_key(site_id: str) -> Select:
    """Generate a query for the decryption nonce and secret key for a given site.

    Args:
        site_id: The site to request the master key nonce and secret key for.

    Returns:
        A SELECT query to fetch the information in question.

    Note:
        The nonce is question is the nonce used with the master key to encrypt
        the secret key.
    """
    return select(sites.c.nonce, sites.c.secret_key).where(sites.c.site_id == site_id)


def insert_site(site_id: str, nonce: bytes, encrypted: bytes, name: str) -> Insert:
    """Generate an INSERT statement to save a site.

    Args:
        site_id: ID to be used for subsequent lookups.
        nonce: The nonce used for encrypting the secret key with the master key.
        encrypted: The encrypted site key.
        name: Human-readable name for the site.

    Returns:
        An INSERT statement.
    """
    return sites.insert().values(
        site_id=site_id,
        nonce=crypto.b64encode(nonce),
        secret_key=crypto.b64encode(encrypted),
        site=name,
    )


def insert_identity(
    identity_id: str,
    confirmation_secret: str,
    site_id: str,
    ttl: datetime.datetime,
    max_ttl: datetime.datetime,
) -> Insert:
    """Generate an INSERT statement to add an identity.

    Args:
        identity_id: ID to use for subsequent lookups.
        confirmation_secret: A secret value shared with the user to allow confirmation.
        site_id: The site the identity is associated with.
        ttl: Time until the identity expires; may be renewed, but cannot exceed `max_ttl`.
        max_ttl: Maximum time until the identity expires.

    Returns:
        The INSERT statement.
    """
    return identities.insert().values(
        identity_id=identity_id,
        confirmation_secret=confirmation_secret,
        site_id=site_id,
        ttl=ttl,
        max_ttl=max_ttl,
    )


def confirm_identity(
    identity_id: str,
    confirmed: datetime.datetime,
) -> Update:
    """Generate an UPDATE statement to confirm an identity.

    Args:
        identity_id: The ID of the identity to confirm.
        confirmed: The time the identity was confirmed.

    Returns:
        The UPDATE statement.
    """
    return (
        identities.update()
        .where(identities.c.identity_id == identity_id)
        .values(
            confirmed=confirmed,
        )
    )


def extend_identity_ttl(
    identity_id: str,
    new_ttl: datetime.datetime,
) -> Update:
    """Generate an UPDATE statement to extend an identity's TTL.

    Args:
        identity_id: The ID of the identity to extend.
        new_ttl: The new TTL for the identity.

    Returns:
        The UPDATE statement.
    """
    return (
        identities.update()
        .where(identities.c.identity_id == identity_id)
        .values(
            ttl=new_ttl,
        )
    )


def insert_comment(
    identity_id: str,
    thread: str,
    submitted: datetime.datetime,
    name: str,
    site: str,
    email: str,
    comment: str,
) -> Insert:
    """Generate an INSERT statement to add a comment.

    Args:
        identity_id: The identity posting the comment.
        thread: The thread the comment is being posted to.
        submitted: The time the comment was submitted.
        name: The name provided with the comment.
        site: The site provided with the comment.
        email: The email provided with the comment.
        comment: The comment text.

    Returns:
        The INSERT statement.
    """
    return comments.insert().values(
        identity_id=identity_id,
        thread=thread,
        submitted=submitted,
        name=name,
        site=site,
        email=email,
        comment=comment,
    )


def publish_comment(
    comment_id: int,
    published: datetime.datetime,
) -> Update:
    """Generate an UPDATE statement to publish a comment.

    Args:
        comment_id: The ID of the comment to publish.
        published: The time the comment was published.

    Returns:
        The UPDATE statement.
    """
    return (
        comments.update()
        .where(comments.c.comment_id == comment_id)
        .values(
            published=published,
        )
    )


def query_comments_by_thread(thread: str) -> Select:
    """Generate a query to fetch published comments for a given thread.

    Args:
        thread: The thread to fetch comments for.

    Returns:
        A SELECT statement to fetch the comments.
    """
    return (
        select(
            comments.c.comment_id,
            comments.c.identity_id,
            comments.c.thread,
            comments.c.submitted,
            comments.c.published,
            comments.c.name,
            comments.c.site,
            comments.c.email,
            comments.c.comment,
        )
        .join(identities, comments.c.identity_id == identities.c.identity_id)
        .where((comments.c.thread == thread) & (comments.c.published.isnot(None) & identities.c.confirmed.isnot(None)))
        .order_by(comments.c.published.asc())
    )
