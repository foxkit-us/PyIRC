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
- [ ] extensions
- [ ] io
- [ ] base
- [ ] util

## Extension docs
- [ ] autojoin.AutoJoin
- [ ] basicrfc.BasicRFC
- [ ] cap.CapNegotiate
- [ ] channeltrack.Channel
- [ ] channeltrack.ChannelTrack
- [ ] ctcp.CTCP
- [ ] isupport.ISupport
- [ ] lag.LagCheck
- [ ] sasl.SASLBase
- [ ] sasl.SASLPlain
- [ ] services.ServicesLogin
- [ ] starttls.StartTLS
- [ ] usertrack.User
- [ ] usertrack.UserTrack

## IO docs
- [ ] asyncio.IRCProtocol
- [ ] socket.IRCSocket

## Base docs
- [ ] auxparse.prefix\_parse
- [ ] auxparse.mode\_parse
- [ ] auxparse.who\_flag\_parse
- [ ] auxparse.isupport\_parse
- [ ] auxparse.CTCPMessage
- [ ] base.IRCBase
- [ ] casemapping.IRCString
- [ ] event.EventState
- [ ] event.Event
- [ ] event.HookEvent
- [ ] event.LineEvent
- [ ] event.EventManager
- [ ] extension.HookGenerator
- [ ] extension.BaseExtension
- [ ] extension.ExtensionManager
- [ ] line.Tags
- [ ] line.Hostmask
- [ ] line.Line
- [ ] numerics.Numerics (perhaps not all the members...)
