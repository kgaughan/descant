from typing import List

from aiohttp import web

routes = web.RouteTableDef()


@routes.post("/comment")
async def submit_comment(request: web.Request) -> web.StreamResponse:
    form = await request.post()
    # The request should contain: site_id, thread, name, url, email, comment.
    # The JWT token with the identity claim should come in as a cookie. If not,
    # we generate a new identity claim.
    site_id = form.get("site_id")
    thread = form.get("thread")

    name = form.get("name")
    url = form.get("url")
    email = form.get("email")
    comment = form.get("coment")
    return web.Response(text=f"name={name} site_id={site_id} thread={thread}")


def init_func(argv: List[str]) -> web.Application:
    app = web.Application()
    app.add_routes(routes)
    return app
