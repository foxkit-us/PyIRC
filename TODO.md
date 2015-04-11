# Tracking
- [x] Channel tracking
- [x] User tracking
- [x] Introspection (what the server sees us as) (mostly done)

## Channel tracking
- [x] Known channels we've joined (mostly done)
- [ ] Autorejoin on kick/remove
- [x] Basic support for known users (see user tracking)

## User tracking
- [x] NAMES tracking
- [ ] NAMESX support (?)
- [x] multi-prefix support
- [x] WHO/WHOX usage for enhanced user information
- [x] WHOIS support
- [x] account-notify/away-notify
- [x] Various forms of services account tracking
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
- [ ] PROTOCTL (?)

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
- [x] Automatic dependency loading
- [x] Generic canned sets of extensions
- [ ] Unit tests
- [x] asyncio support
- [ ] gevent support
- [ ] stackless (?)

# Docs
- [x] extensions
- [ ] io
- [ ] base
- [ ] util

## Extension docs
- [x] autojoin.AutoJoin
- [x] basicrfc.BasicRFC
- [x] cap.CapNegotiate
- [x] channeltrack.Channel
- [x] channeltrack.ChannelTrack
- [x] ctcp.CTCP
- [x] isupport.ISupport
- [x] lag.LagCheck
- [x] sasl.SASLBase
- [x] sasl.SASLPlain
- [x] services.ServicesLogin
- [x] starttls.StartTLS
- [x] usertrack.User
- [x] usertrack.UserTrack

## IO docs
- [ ] asyncio.IRCProtocol
- [ ] socket.IRCSocket

## Base docs
- [x] auxparse.prefix\_parse
- [x] auxparse.mode\_parse
- [x] auxparse.who\_flag\_parse
- [x] auxparse.isupport\_parse
- [x] auxparse.CTCPMessage
- [x] base.IRCBase
- [x] casemapping.IRCString
- [ ] event.EventState
- [ ] event.Event
- [ ] event.HookEvent
- [ ] event.LineEvent
- [ ] event.EventManager
- [x] extension.HookGenerator
- [x] extension.BaseExtension
- [ ] extension.ExtensionManager
- [x] line.Tags
- [x] line.Hostmask
- [x] line.Line
- [ ] numerics.Numerics (perhaps not all the members...)
