# Development

It's recommended you install [uv] and [just] to manage your development
environment.

!!! note

    The following assumes you've made sure to install the `sqlite` group
    with `uv sync --group sqlite`. If you've configured your development
    environment with `just devel`, this should be the case.

Create a file called `descant.ini`: this will store various settings, including
the locations of your master key and the database connection string:

```ini
[DEFAULT]
db = sqlite+aiosqlite:///descant.db
master_key = master.key
```

You can pass a path to this using the `descant` global flag `--config`. Various
flags for the commands that follow will be filled in from this file.

Generate a master key for your development site:

```console
$ uv run descant --config descant.ini generate-master-key
```

A file called `master.key` will appear in the root of the project.

Create the database:

```console
$ uv run descant --config descant.ini create-db
```

Currently only SQLite is tested, but other engines should work.

You can now add a site:

```console
$ uv run descant --config descant.ini add-site "My blog"
Site ID: 3b67e004-6756-4aa7-8ba6-06fc78c1f2e3
Secret key: *redacted*
```

You should store these for later. The site ID is used to identify your site,
while the secret key is stored in the database having been encrypted by your
master key.

You should now be able to bring up the development server:

```console
$ uv run descant --config descant.ini serve
======== Running on http://localhost:8080 ========
(Press CTRL+C to quit)
```

[uv]: https://docs.astral.sh/uv/
[just]: https://just.systems/

## Configuring PostgreSQL

!!! note

    You'll need to have run `uv sync --group postgres` to make sure the
    drivers are installed as expected.

Assuming you already have a superuser you can use for doing things like
database and user creation, do:

```console
$ createuser --login --pwprompt descant
...
$ createdb descant
```

```console
$ psql descant
descant=# GRANT CREATE, CONNECT ON DATABASE descant TO descant;
GRANT
descant=# GRANT USAGE, CREATE ON SCHEMA public TO descant;
GRANT
descant=# GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO descant;
GRANT
```

If you configure `descant.ini` with:

```ini
db = postgresql+asyncpg://descant:<redacted>@localhost:5432/descant
```

Replacing the password you used for `<redacted>` in the example above, you
should now now be able to use the `create-db` subcommand to populate the
database with an appropriate schema.
