import base64
import datetime
import http
import os
import typing as t
import uuid

from aiohttp import web
import cryptography
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import create_async_engine

from . import crypto, schema

routes = web.RouteTableDef()


@routes.post("/comment")
async def submit_comment(request: web.Request) -> web.StreamResponse:
    form = await request.post()
    # The request should contain: site_id, thread, name, url, email, comment.
    # The JWT token with the identity claim should come in as a cookie. If not,
    # we generate a new identity claim.
    site_id = form.get("site_id")

    async with request.app["db"].connect() as conn:
        result = await conn.execute(schema.query_secret_key(site_id))
        try:
            nonce, encrypted_key = result.one()
        except NoResultFound:
            return web.Response(
                text=f"Bad site ID: {site_id}",
                status=http.HTTPStatus.BAD_REQUEST,
            )
    try:
        secret_key = request.app["master_cipher"].decrypt(
            base64.b64decode(nonce.encode("ascii")),
            base64.b64decode(encrypted_key.encode("ascii")),
            site_id.encode("ascii"),
        )
    except cryptography.exceptions.InvalidTag:
        # This should never happen unless there's a database corruption issue
        # or the master key was overwritten.
        return web.Response(
            text=f"Could not decrypt key for {site_id}",
            status=http.HTTPStatus.BAD_REQUEST,
        )

    # We've gotten far enough that we can now check the thread.
    thread = crypto.decode_thread_token(form.get("thread"), secret_key)
    if thread is None:
        return web.Response(
            text="Invalid or missing thread token",
            status=http.HTTPStatus.BAD_REQUEST,
        )

    name = form.get("name")
    # url = form.get("url")
    # email = form.get("email")
    # comment = form.get("coment")
    return web.Response(text=f"name={name} site_id={site_id} thread={thread}")


def init_func(argv: t.List[str], **cfg) -> web.Application:
    async def db_engine(app: web.Application):
        engine = create_async_engine(cfg["db"], echo=True)
        app["db"] = engine
        yield
        await engine.dispose()

    app = web.Application()
    app.update(cfg)
    app.add_routes(routes)
    app.cleanup_ctx.append(db_engine)
    return app
