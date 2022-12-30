import click

from . import schema


@click.group()
def main():
    pass


@main.command("create-db")
def create_db():
    schema.create_tables()
