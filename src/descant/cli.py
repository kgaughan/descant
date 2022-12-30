import base64
import os
import uuid
import configparser

import click
import sqlalchemy

from . import crypto, schema

CONNECTION_STRING = "sqlite:///example.db"


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
        with open(config, "r") as fh:
            parser.read_file(fh)
        ctx.default_map = dict(parser.items())


@main.command("create-db")
def create_db():
    engine = sqlalchemy.create_engine(CONNECTION_STRING, echo=True)
    schema.metadata.create_all(engine)


@main.command("generate-master-key")
@click.option(
    "--cipher",
    default="AESGCM",
    type=click.Choice(list(crypto.CIPHERS.keys())),
)
@click.argument("master-key", default="master.key", type=click.File("w", "ascii"))
def generate_master_key(cipher, master_key):
    master_key.write(crypto.generate_key(cipher))


@main.command("add-site")
@click.option("--master-key", default="master.key", type=click.File("r", "ascii"))
@click.argument("name", required=True)
def add_site(master_key, name):
    site_id = str(uuid.uuid4())
    secret_key = os.urandom(32)  # 256-bits

    master_cipher = crypto.parse_key(master_key.read())
    nonce = os.urandom(12)
    encrypted = master_cipher.encrypt(nonce, secret_key, site_id.encode("ascii"))

    engine = sqlalchemy.create_engine(CONNECTION_STRING)
    ins = schema.sites.insert().values(
        site_id=site_id,
        secret_key=".".join([crypto.b64encode(nonce), crypto.b64encode(encrypted)]),
        site=name,
    )
    conn = engine.connect()
    conn.execute(ins)

    print("Site ID:", site_id)
    print("Secret key:", crypto.b64encode(secret_key))
