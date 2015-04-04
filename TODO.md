# Tracking
- [ ] Channel tracking
- [ ] User tracking
- [ ] Introspection (what the server sees us as)

## Channel tracking
- [ ] Known channels we've joined
- [ ] Autorejoin on kick/remove
- [ ] Basic support for known users (see user tracking)

## User tracking
- [ ] NAMES tracking
- [ ] NAMESX support (?)
- [ ] multi-prefix support (CAP and *maybe* CLICAP?)
- [ ] WHO/WHOX usage for enhanced user information
- [ ] WHOIS support
- [ ] account-notify/away-notify
- [ ] Various forms of services account tracking
- [ ] MONITOR support for online/offline detection

## Introspection
- [ ] Our present nick (knowing about SANICK/FORCENICK/SVSNICK)
- [ ] Present hostname
- [ ] Present cloak
- [ ] Lag checking

# Standards compliance
- [ ] IRCv3.x
- [ ] CTCP
- [ ] DCC
- [ ] NickServ/Q support

## IRCv3.x
- [ ] Metadata
- [ ] Enhanced SASL methods (challenge methods? certfp?)
- [ ] Batch
- [ ] Examine other features and add them

## CTCP
- [ ] Hooks for CTCP/NCTCP events

## DCC
- [ ] Hooks for DCC events
- [ ] Handle DCC connections including PASV

# Architectural
- [ ] Real event structures passed to callbacks (that have event status,
      data, etc).
- [ ] Outgoing command hooks
- [ ] Automatic dependency loading
- [ ] Generic canned sets of extensions
- [ ] Unit tests
- [ ] asyncio support
- [ ] gevent support
- [ ] stackless (?)
