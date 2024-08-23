# Design

Descant consists of two parts:

- A thin JavaScript layer that runs in the browser and manages basic interactions. This uses [htmx] to manage communication with the server.
- A small, self-hosted server written in Python. This is where most of the logic resides.

It must avoid storing _any_ PII. Things like names and website URLs that the user wishes to make public are stored, but email addresses are _not_ unless the user opts into email notifications for new comments.

## Schema and basic theory of operation of server

The are three tables: _sites_, _identities_, and _comments_.

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

The _sites_ table stores basic metadata about a given comment site. The _site_id_ is a public UUID that identifies the site in question, while _secret_key_ is a shared secret used for signing the _thread ID_. The _site_ is the public name for the site in question. _secret_key_ is not stored in plaintext, but is encrypted by a master key that's stored in the environment.

### Identities

```sql
CREATE TABLE identities (
    identity_id         CHAR(36)  NOT NULL,
    confirmation_secret CHAR(64)  NOT NULL,
    site_id             CHAR(36)  NOT NULL,
    ttl                 TIMESTAMP NOT NULL,
    max_ttl             TIMESTAMP NOT NULL,
    confirmed           TIMESTAMP NULL,

    PRIMARY KEY (indentity_id),
    FOREIGN KEY (site_id) REFERENCES sites (site_id)
);

CREATE INDEX ix_site ON identities (site_id);
```

An identity is a temporary authorisation to post on a given site. The first time a commenter attempts to post a comment, a new identity is created, and random conformation secret is sent to an email they are required to provide. This is tied to a site by _site_id_, and the _ttl_ (the time before the identity TTL should be extended) and the _max_ttl_ (the time before the identity expires completely) are set.

If an identity is used within its _ttl_, no updates to _ttl_ or _max_ttl_ occur. If an identity is used between _ttl_ and _max_ttl_, the _ttl_ and _max_ttl_ are extended. Once an identity is at or beyond _max_ttl_, it is considered invalid. As long as the owner of the identity is actively commenting 

The email that's sent out contains a link to a form containing the identity ID and confirmation secret. Once the identity is confirmed, _ttl_ and _max_ttl_ are updated based off of the current time, and _confirmed_ is set to the current time. Comments assocated with this identity can now be processed.

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

This is where the meat of the system lives. _comment_id_ is for identifying a given comment in the system. This is the one place where an autoincremented integer seems like a reasonable choice as the information leakage (the approximate number of comments in the system) is minimal. It's never used without _thread_.

_identity_id_ ties a comment to a temporary authorisation. Once the identity is confirmed, the associated comments get processed.

The _thread_ is an identifier constructed by the site from the _site_id_ and site's own thread identifier (such as a stub, URL, post ID, &c.). In transit, this is signed using _sites.secret_key_, but here it's stored in its raw form. Initially, this will take the form `SHA256(site_id || '|' || site_thread_id)`. This isn't considered sensitive information and is mainly to maintain the external key at a fixed size.

When a comment is first submitted, the _submitted_ timestamp is set, along with at least _name_ and _comment_. _submitted_ is primarily for the site owner's convenience. When the associated identity is confirmed, _published_ is set to `NOW() + INTERVAL x MINUTES`, where _x_ is a cooldown period in which the commenter can edit the comment. Once the cooldown period expires, the comment is considered public and cannot be edited.

If the commenter has opted into email notifications, their encrypted email address is stored in _email_. This encrypted using the master key. If this field is null, the commenter has not opted into receiving emails.

### Design principals

Generally, UUIDs are used for public IDs to avoid creating guessable identifiers. The comment ID is the one exception for this as it must always be used with the _thread_ identfier, and this is always signed in transit.

Rather than using booleans as flags, we use nullable timestamps. If set, this is the equivalent of _true_, and lets us know when the event happened.

### Open questions

* Should there be a distinct _threads_ table? This may allow threads to be closed after a time, but would complicate things somewhat. A max thread age could be set on the site, and entries could be added here dynamically. It might store the maximum thread age based on when the comment was first made if it was running in a kind of 'promiscuous mode', but for a timeout based on when the original post was first published, the client would need to include a timestamp for the publication date of the thread. A max thread age would give us an opportunity to wipe out _comments.email_, as it's no longer necessary.
* Would it be better to use the site's _secret_key_ rather than the master key for encrypting the emails? It's a good argument to be made either way, but this may be more secure as it would leak less information in case of a database compromise.
* Encrypted and hashed fields should contain some information on how they're encrypted/hashed. The space dedicated to the encrypted fields in almost certainly too small, and I'll need to make some decisions based off of what I see before I come up with the final sizing.

## Likely implementation

The identity is likely going to be a [JWT]. We need to guarantee that its contents cannot be tampered with, but the contents of the token can be disclosed safely to the commenter, so long as TLS is used to avoid MITM attacks.

[htmx]: https://htmx.org/
[JWT]: https://www.rfc-editor.org/rfc/rfc7519 "JSON Web Token"

*[PII]: Personally Identifiable Information
*[MITM]: Man-in-the-Middle

## Protocol

The site is first registered with Descant, yielding a site ID and secret key. The secret key is base64-encoded. This is used by 

It's up to the client to decide how to construct its thread identifier, but the identifier should be run through a SHA-256 hash, as it may be a maximum of 64-bytes long.
