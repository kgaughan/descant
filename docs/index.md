# Descant

1. A melody or counterpoint sung or played above the theme.<br>
2. A discussion on a theme.

Discant is a comment management system intended to be relatively spam-resistant while also being 100% compatible with the GDPR. It stores no information beyond that which is published publicly, and only requests anything resembling PII to allow the user to be validated. See the [design documentation](design.md) for details.

## Rationale

I would like to enable comments on my sites, but I'd like to do this in as GDRP-compliant a fashion as possible. That means storing _no_ PII and minimal cookie usage by using browser local storage for pre-filled fields.

The system does this by establishing a temporary identity. This is more akin to a browser session than a real identity and expires after a while. It primarily serves to allow the site owner to know that the same entity created the comments, and also allows commenters to edit their comments for a short period after they've been made. This is also a partial anti-spam method, as it requires confirmation of the identity before any comments associated with it can be published, creating a minor initial hurdle; a full anti-spam solution would be more complicated. No actual PII is stored beyond this association, though commenters can optionally opt in to receive notifications too.

It should be easy to self-host, as it's not something I'm terribly interested in providing as a service to others.

*[PII]: Personally Identifiable Information
