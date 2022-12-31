import asyncio
import configparser
import os
import uuid

from aiohttp import web
import click

from . import crypto, schema, site


@click.group()
@click.option(
    "--config",
    default="~/.descant.ini",
    type=click.Path(),
    envvar="DESCANT_CONFIG",
)
@click.pass_context
def main(ctx, config):
    if os.path.exists(config):
        parser = configparser.ConfigParser()
        for section in main.commands:
            parser.add_section(section)
        with open(config, "r") as fh:
            parser.read_file(fh)
        ctx.default_map = {
            key: dict(sect)
            for key, sect in parser.items()
            if key != configparser.DEFAULTSECT
        }


@main.command("create-db")
@click.option("--db", required=True, hidden=True)
def create_db(db):
    asyncio.run(schema.create_db(db))


@main.command("generate-master-key")
@click.option(
    "--cipher",
    default="AESGCM",
    type=click.Choice(list(crypto.CIPHERS.keys())),
    help="Cipher to use for the master key.",
    show_choices=True,
)
@click.argument("master-key", default="master.key", type=click.File("w", "ascii"))
def generate_master_key(cipher, master_key):
    master_key.write(crypto.generate_key(cipher))


@main.command("add-site")
@click.option("--db", required=True, hidden=True)
@click.option("--master-key", default="master.key", type=click.File("r", "ascii"))
@click.argument("site", required=True)
def add_site(db, master_key, site):
    site_id = str(uuid.uuid4())
    secret_key = os.urandom(32)  # 256-bits

    master_cipher = crypto.parse_key(master_key.read())
    nonce = os.urandom(12)
    encrypted = master_cipher.encrypt(nonce, secret_key, site_id.encode("ascii"))

    asyncio.run(schema.execute(db, schema.insert_site(site_id, nonce, encrypted, site)))

    print("Site ID:", site_id)
    print("Secret key:", crypto.b64encode(secret_key))


@main.command("serve")
@click.option("--db", required=True, hidden=True)
@click.option(
    "--ttl",
    default=600,
    type=click.INT,
    hidden=True,
    help="Seconds before the identity claim must be refreshed.",
)
@click.option(
    "--max-ttl",
    default=604800,
    type=click.INT,
    hidden=True,
    help="Seconds before the identity claim expires if not refreshed.",
)
@click.option(
    "--master-key",
    default="master.key",
    type=click.File("r", "ascii"),
    hidden=True,
)
def serve(db, ttl, max_ttl, master_key):
    web.run_app(
        site.init_func(
            [],
            db=db,
            ttl=ttl,
            max_ttl=max_ttl,
            master_cipher=crypto.parse_key(master_key.read()),
        ),
        host="localhost",
    )
