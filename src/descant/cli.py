import base64
import configparser
import os
import uuid

from aiohttp import web
import click
import sqlalchemy

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
    engine = sqlalchemy.create_engine(db, echo=True)
    schema.metadata.create_all(engine)


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
@click.argument("name", required=True)
def add_site(db, master_key, name):
    site_id = str(uuid.uuid4())
    secret_key = os.urandom(32)  # 256-bits

    master_cipher = crypto.parse_key(master_key.read())
    nonce = os.urandom(12)
    encrypted = master_cipher.encrypt(nonce, secret_key, site_id.encode("ascii"))

    ins = schema.sites.insert().values(
        site_id=site_id,
        secret_key=".".join([crypto.b64encode(nonce), crypto.b64encode(encrypted)]),
        site=name,
    )
    sqlalchemy.create_engine(db).connect().execute(ins)

    print("Site ID:", site_id)
    print("Secret key:", crypto.b64encode(secret_key))


@main.command("serve")
def serve():
    web.run_app(site.init_func([]), host="localhost")
