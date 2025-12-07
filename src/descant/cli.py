import asyncio
import configparser
import os

from aiohttp import web
import click

from . import crypto, schema, site


@click.group(help="A secure comments system.")
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
        with open(config) as fh:
            parser.read_file(fh)
        ctx.default_map = {key: dict(sect) for key, sect in parser.items() if key != configparser.DEFAULTSECT}


@main.command("create-db", help="Configure the database")
@click.option("--db", required=True, hidden=True)
def create_db(db):
    asyncio.run(schema.create_db(db))


@main.command("generate-master-key", help="Generate the master key")
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


@main.command("add-site", help="Register a site")
@click.option("--db", required=True)
@click.option("--master-key", default="master.key", type=click.File("r", "ascii"))
@click.argument("site", required=True)
def add_site(db, master_key, site):
    master_cipher = crypto.parse_key(master_key.read())
    site_id, nonce, site_key = crypto.generate_site(master_cipher)
    asyncio.run(schema.execute(db, schema.insert_site(site_id, nonce, site_key, site)))
    print("Site ID:", site_id)
    print("Encrypted site key:", crypto.b64encode(site_key))


@main.command("serve", help="Run the service using the development server")
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
            db=db,
            ttl=ttl,
            max_ttl=max_ttl,
            master_cipher=crypto.parse_key(master_key.read()),
        ),
        host="localhost",
    )
