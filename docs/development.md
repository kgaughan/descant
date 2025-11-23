# Development

It's recommended you install [uv] and [just] to manage your development
environment.

Generate a master key for your development site:

```console
$ uv run descant generate-master-key
```

A file called `master.key` will appear in the root of the project.

Then create the database, supplying the connection string with `--db`:

```console
$ uv run descant create-db --db sqlite+aiosqlite:///descant.db
```

Currently only SQLite is tested, but other engines should work.

You can now add a site:

```console
$ uv run descant add-site --db sqlite+aiosqlite:///descant.db "My blog"
Site ID: 3b67e004-6756-4aa7-8ba6-06fc78c1f2e3
Secret key: *redacted*
```

You should store these for later. The site ID is used to identify your site,
while the secret key is stored in the database having been encrypted by your
master key.

Create a file called `descant.ini`: this will store various settings, including
the locations of your master key and the database connection string:

```ini
[DEFAULT]
db = sqlite+aiosqlite:///descant.db
master_key = master.key
```

You can pass a path to this using the `descant` global flag `--config`.

You should now be able to bring up the development server:

```console
$ uv run descant --config=descant.ini serve
======== Running on http://localhost:8080 ========
(Press CTRL+C to quit)
```

[uv]: https://docs.astral.sh/uv/
[just]: https://just.systems/
