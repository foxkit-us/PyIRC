# Tracking
- [x] Channel tracking
- [x] User tracking
- [x] Introspection (what the server sees us as)

## Channel tracking
- [x] Known channels we've joined
- [x] Autorejoin on kick/remove
- [x] Basic support for known users (see user tracking)

## User tracking
- [x] NAMES tracking
- [x] NAMESX support (worth doing?)
- [x] multi-prefix support
- [x] WHO/WHOX usage for enhanced user information
- [x] WHOIS support
- [x] account-notify/away-notify
- [x] Various forms of services account tracking
- [ ] MONITOR support for online/offline detection

## Introspection
- [x] Our present nick (knowing about SANICK/FORCENICK/SVSNICK)
- [x] Present hostname (mostly)
- [x] Present cloak
- [x] Lag checking

# Standards compliance
- [x] IRCv3.x (mostly)
- [x] CTCP
- [ ] DCC
- [x] NickServ/Q support
- [x] PROTOCTL

## IRCv3
- [ ] Metadata (3.2+)
- [ ] Enhanced SASL methods (challenge methods? external?)
- [ ] Batch (3.2+)
- [ ] Examine other features and add them

## Enhanced SASL
- [ ] ECDSA-NIST256P-CHALLENGE
- [x] EXTERNAL (SSL machinery is there)

## CTCP
- [x] Hooks for CTCP/NCTCP events

## DCC
- [ ] Hooks for DCC events
- [ ] Handle DCC connections including PASV

# Architectural
- [x] Real event structures passed to callbacks (that have event status,
      data, etc).
- [x] Outgoing command hooks
- [x] Automatic dependency loading
- [x] Unit tests (some)
- [x] asyncio support
- [x] eventlet support
- [ ] gevent support
- [x] Allow addition of extensions without deleting every instance
- [ ] Clean way to reload extensions
