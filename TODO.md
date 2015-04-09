# Tracking
- [x] Channel tracking
- [x] User tracking
- [ ] Introspection (what the server sees us as) (partial)

## Channel tracking
- [x] Known channels we've joined (mostly)
- [ ] Autorejoin on kick/remove
- [x] Basic support for known users (see user tracking)

## User tracking
- [x] NAMES tracking
- [ ] NAMESX support (?)
- [x] multi-prefix support
- [x] WHO/WHOX usage for enhanced user information
- [x] WHOIS support
- [x] account-notify/away-notify
- [ ] Various forms of services account tracking
- [ ] MONITOR support for online/offline detection

## Introspection
- [x] Our present nick (knowing about SANICK/FORCENICK/SVSNICK)
- [x] Present hostname (mostly)
- [ ] Present cloak
- [x] Lag checking

# Standards compliance
- [x] IRCv3.x (mostly)
- [x] CTCP
- [ ] DCC
- [ ] NickServ/Q support

## IRCv3.x
- [ ] Metadata
- [ ] Enhanced SASL methods (challenge methods? certfp?)
- [ ] Batch
- [ ] Examine other features and add them

## CTCP
- [x] Hooks for CTCP/NCTCP events

## DCC
- [ ] Hooks for DCC events
- [ ] Handle DCC connections including PASV

# Architectural
- [x] Real event structures passed to callbacks (that have event status,
      data, etc).
- [ ] Outgoing command hooks
- [ ] Automatic dependency loading
- [x] Generic canned sets of extensions
- [ ] Unit tests
- [ ] asyncio support
- [ ] gevent support
- [ ] stackless (?)
