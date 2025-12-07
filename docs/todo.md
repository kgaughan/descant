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

* Where should rendering happen: the client (with moustache.js or something
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
