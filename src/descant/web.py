from aiohttp import web


async def handle(request):
    name = request.match_info.get("name", "Anonymous")
    return web.Response(text=f"Hello, {name}")


app = web.Application()
app.add_routes(
    [
        web.get("/", handle),
        web.get("/{name}", handle),
    ]
)


def main():
    web.run_app(app, host="localhost")


if __name__ == "__main__":
    main()
