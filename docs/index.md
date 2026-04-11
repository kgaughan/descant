---
title: Descant
author: Keith Gaughan
date: 2026-04-11
lang: en
abstract: |
  1. A melody or counterpoint sung or played above the theme.
  2. A discussion on a theme.
  
  Descant is a comment management system intended to be relatively
  spam-resistant while also being 100% compatible with the GDPR. It stores no
  information beyond that which is published publicly, and only requests
  anything resembling PII to allow the user to be validated.
---

# Rationale

I would like to enable comments on my sites, but I'd like to do this in as
GDPR-compliant a fashion as possible. That means storing _no_ PII (Personally
Identifiable Information) and minimal cookie usage by using browser local
storage for pre-filled fields.

The system does this by establishing a temporary identity. This is more akin to
a browser session than a real identity and expires after a while. It primarily
serves to allow the site owner to know that the same entity created the
comments, and also allows commenters to edit their comments for a short period
after they've been made. This is also a partial anti-spam method, as it
requires confirmation of the identity before any comments associated with it
can be published, creating a minor initial hurdle; a full anti-spam solution
would be more complicated. No actual PII is stored beyond this association,
though commenters can optionally opt in to receive notifications too.

It should be easy to self-host, as it's not something I'm terribly interested
in providing as a service to others.

# Design

Descant consists of two parts:

* A thin JavaScript layer that runs in the browser and manages basic
  interactions. This uses [htmx] to manage communication with the server.
* A small, self-hosted server written in Python. This is where most of the
  logic resides.

It must avoid storing _any_ PII. Things like names and website URLs that the
user wishes to make public are stored, but email addresses are _not_ unless
the user opts into email notifications for new comments.

## Schema and basic theory of operation of the server

There are three tables: _sites_, _identities_, and _comments_.

### Sites

```sql
CREATE TABLE sites (
    site_id    CHAR(36)     NOT NULL,
    nonce      CHAR(16)     NOT NULL,
    secret_key CHAR(64)     NOT NULL,
    site       VARCHAR(256),

    PRIMARY KEY (site_id)
);
```

The _sites_ table stores basic metadata about a given comment site. The
_site\_id_ is a public UUID that identifies the site in question, while
_secret\_key_ is a shared secret used for signing the _thread ID_. The _site_
is the public name for the site in question. _secret\_key_ is not stored in
plaintext, but is encrypted by a master key that's stored in the environment.

### Identities

```sql
CREATE TABLE identities (
    identity_id         CHAR(36)  NOT NULL,
    confirmation_secret CHAR(64)  NOT NULL,
    site_id             CHAR(36)  NOT NULL,
    ttl                 TIMESTAMP NOT NULL,
    max_ttl             TIMESTAMP NOT NULL,
    confirmed           TIMESTAMP NULL,

    PRIMARY KEY (identity_id),
    FOREIGN KEY (site_id) REFERENCES sites (site_id)
);

CREATE INDEX ix_site ON identities (site_id);
```

An identity is a temporary authorisation to post on a given site. The first
time a commenter attempts to post a comment, a new identity is created, and
random confirmation secret is sent to an email they are required to provide.
This is tied to a site by _site\_id_, and the _ttl_ (the time before the
identity TTL should be extended) and the _max\_ttl_ (the time before the
identity expires completely) are set.

If an identity is used within its _ttl_, no updates to _ttl_ or _max\_ttl_
occur. If an identity is used between _ttl_ and _max\_ttl_, the _ttl_ and
_max\_ttl_ are extended. Once an identity is at or beyond _max\_ttl_, it is
considered invalid. As long as the owner of the identity is actively
commenting, no reconfirmation should be needed.

The email that's sent out contains a link to a form containing the identity ID
and confirmation secret. Once the identity is confirmed, _ttl_ and _max\_ttl_
are updated based off of the current time, and _confirmed_ is set to the
current time. Comments associated with this identity can now be processed.

### Comments

```sql
CREATE TABLE comments (
    comment_id  INTEGER      NOT NULL AUTOINCREMENT,
    identity_id CHAR(36)     NOT NULL,
    thread      CHAR(64)     NOT NULL,
    submitted   TIMESTAMP    NOT NULL,
    published   TIMESTAMP    NULL,
    name        VARCHAR(256) NOT NULL,
    site        VARCHAR(256) NULL,
    email       VARCHAR(256) NULL,
    comment     TEXT         NOT NULL,

    PRIMARY KEY (comment_id),
    FOREIGN KEY (identity_id) REFERENCES identities (identity_id)
);

CREATE INDEX ix_thread ON comments (thread);
```

This is where the meat of the system lives. _comment\_id_ is for identifying a
given comment in the system. This is the one place where an autoincremented
integer seems like a reasonable choice as the information leakage (the
approximate number of comments in the system) is minimal. It's never used
without _thread_.

_identity\_id_ ties a comment to a temporary authorisation. Once the identity
is confirmed, the associated comments get processed.

The _thread_ is an identifier constructed by the site from the _site\_id_ and
site's own thread identifier (such as a stub, URL, post ID, &c.). In transit,
this is signed using _sites.secret\_key_, but here it's stored in its raw form.
Initially, this will take the form `SHA256(site_id || '|' || site_thread_id)`.
This isn't considered sensitive information and is mainly to maintain the
external key at a fixed size.

When a comment is first submitted, the _submitted_ timestamp is set, along
with at least _name_ and _comment_. _submitted_ is primarily for the site
owner's convenience. When the associated identity is confirmed, _published_ is
set to `NOW() + INTERVAL x MINUTES`, where _x_ is a cooldown period in which
the commenter can edit the comment. Once the cooldown period expires, the
comment is considered public and cannot be edited.

If the commenter has opted into email notifications, their encrypted email
address is stored in _email_. This is encrypted using the master key. If this
field is null, the commenter has not opted into receiving emails.

### Design principles

Generally, UUIDs are used for public IDs to avoid creating guessable
identifiers. The comment ID is the one exception for this as it must always be
used with the _thread_ identifier, and this is always signed in transit.

Rather than using booleans as flags, we use nullable timestamps. If set, this
is the equivalent of _true_, and lets us know when the event happened.

### Open questions

* Should there be a distinct _threads_ table? This may allow threads to be
  closed after a time, but would complicate things somewhat. A max thread age
  could be set on the site, and entries could be added here dynamically. It
  might store the maximum thread age based on when the comment was first made
  if it was running in a kind of 'promiscuous mode', but for a timeout based
  on when the original post was first published, the client would need to
  include a timestamp for the publication date of the thread. A max thread
  age would give us an opportunity to wipe out _comments.email_, as it's no
  longer necessary.
* Would it be better to use the site's _secret\_key_ rather than the master
  key for encrypting the emails? It's a good argument to be made either way,
  but this may be more secure as it would leak less information in case of a
  database compromise.
* Encrypted and hashed fields should contain some information on how they're
  encrypted/hashed. The space dedicated to the encrypted fields in almost
  certainly too small, and I'll need to make some decisions based off of what
  I see before I come up with the final sizing.

## Likely implementation

The identity is likely going to be a [JWT]. We need to guarantee that its
contents cannot be tampered with, but the contents of the token can be
disclosed safely to the commenter, so long as TLS is used to avoid
[Man-in-the-middle attacks](https://en.wikipedia.org/wiki/Man-in-the-middle_attack).

[htmx]: https://htmx.org/
[JWT]: https://www.rfc-editor.org/rfc/rfc7519 "JSON Web Token"

## Protocol

The site is first registered with Descant, yielding a site ID and secret key.
The secret key is base64-encoded. This is used by...

It's up to the client to decide how to construct its thread identifier, but
the identifier should be run through a SHA-256 hash, as it may be a maximum of
64-bytes long.

# Development

It's recommended you install [uv] and [just] to manage your development
environment.

**Note:** The following assumes you've made sure to install the `sqlite` group
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

**Note:** You'll need to have run `uv sync --group postgres` to make sure the
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
should now be able to use the `create-db` subcommand to populate the
database with an appropriate schema.

# To do

* We can add new sites, and there's an endpoint for submitting comments, but
  wouldn't it be a good idea to present an endpoint for rendering a comments
  thread first?

* Should there be a separate daemon that gets spun up for handling encryption
  services? My thinking here is that the encryption service could be the only
  thing with access to the master key, and thus putting it in its own process
  would mean that if the external internet-facing service is compromised,
  there's less chance that any actual data will be exposed. However, this
  is no panacea as the the web side of things would still be capable of
  sending data to the encryption service to get back decrypted data.

* The comment submission endpoint doesn't yet handle comment submission, only
  the generation of the identity. There's nothing that subsequently queues
  up whatever actions are needed for contacting the user, nor anything that
  inserts the comment.

* Spam. We need to deal with spam. The initial version might be able to skimp
  on this, but not any subsequent versions.

* Moderation.

* This is potentially a great way to end up getting a bad mailserver
  reputation. Before an identity can be processed for the first time, there
  needs to be a queue to allow the site owner to trigger the sending of the
  identity confirmations.

* Where should rendering happen: the client (with mustache.js or something
  like it), or the server? For user-editable templates, Mustache on both the
  client and server would likely be safest. For server-side rendering,
  [Chevron](https://github.com/noahmorrison/chevron) looks like the best bet
  while client-side, it's [mustache.js](https://github.com/janl/mustache.js).
  The fact the two repos haven't been updated in 4 years and 2 years
  respectively is a tad worrying, but at least for JavaScript, there's the
  option of [Handlebars.js](https://github.com/handlebars-lang/handlebars.js),
  though even that hasn't seen an actual release since 2023. There's a
  [Python implementation of Handlebars](https://github.com/vintasoftware/python-handlebars)
  too, but the repo doesn't look very actively maintained.

* Database migrations with [Alembic](https://alembic.sqlalchemy.org/). I want
  to integrate this into the descant command line tool rather than leaning on
  Alembic itself, mainly because I want the user to be able to use the same
  configuration file. I'm not sure how much work this'll actually take but
  it seems non-trivial going off of my initial attempt. I think that
  [Flask-Migrate](https://github.com/miguelgrinberg/Flask-Migrate/) might be
  a reasonable inspiration for how to get this working. I based my initial
  attempt off of the contents of the generated `env.py` file, but it seems
  the alembic command line tool does some setup magic in the background.
