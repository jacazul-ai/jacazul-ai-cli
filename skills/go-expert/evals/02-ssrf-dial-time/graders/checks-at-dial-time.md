---
type: llm
---

- The protection checks the IP address that is actually dialed, for
  example in a `net.Dialer` `Control` or `ControlContext` hook, or in a
  custom `DialContext`, not only the host name parsed from the URL.
- The answer states that checking the host name before the request is not
  enough, because a name can resolve to an internal address or resolve
  differently between the check and the connection.
- The check rejects at least loopback, private and link-local addresses.
- Redirects cannot bypass the protection, either because the check lives
  in the dialer used for every connection or because redirects are
  explicitly handled.
