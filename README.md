# Example client for Turris Sentinel DynFW

This simple script is an example of code that is able to connect to the DynFW
server and obtain published data for further processing.


## Introduction

Some terminology first:


### Turris Sentinel

Turris [Sentinel](https://docs.turris.cz/basics/sentinel/intro/) - or simply
Sentinel - is a threat detection and cyber attack prevention system.
It records interactions with potential malware or cyber-criminals on Turris
routers. Based on the gathered data we detect malicious IP addresses - attackers
and block them on all the devices.


### DynFW

Dynamic FireWall - aka DynFW - is one of the parts of Sentinel. It receives
events related to cyber threats from several sources and, based on this knowledge,
builds and publishes a list of potentially malicious IP addresses - attackers.

This list is built real-time and the whole interface is accessible. So, everyone
is able to consume real-time data in any manner they want.


## Protocol overview

A client communicates with a server by [ZeroMQ](https://zeromq.org/)
[PUB/SUB](https://zguide.zeromq.org/docs/chapter1/#Getting-the-Message-Out)
pattern. Server publishes ZMQ multipart messages containing exactly two parts.

The first part is a string identifying a message topic.
It is same as the ZMQ PUB/SUB subscribe string (Your application should
subscribe for these topics.)
Currently there are following topics published by a server:
- `dynfw/list`
- `dynfw/delta`
- `dynfw/event`

The second part is a payload of a message. In general it is a dictionary
serialized to stream of bytes by [message pack](https://msgpack.org/).
To read it the client must de-serialize (unpack) it first.
The keys of the dictionary are always strings. The values can be arbitrary
data type.


### dynfw/list

This message contains the whole list of potentially malicious IP addresses.
The list is usually long with only small changes during the time.
It should be used only for the first initialization of the list but *not* for
keeping it up to date! To keep the list up to date `dynfw/delta` message should
be used. See later chapter for that.

The structure of a message *payload* is as follows:
```
"version" : version - u64, version of a list, it is an increasing number, currently it is equal to time stamp
"serial" : serial - u64, incremented by one with every update (dynfw/delta message)
"list" : list_of_addresses, - array/list of strings, each one is an IP address
"ts" : timestamp - u64, Unix time of when a message was generated
```


### dynfw/delta

`dynfw/delta` message is produced exactly at the moment when an IP address is
added or removed to the list. This should be used to keep an initialized list
up-to-date.

The structure of message *payload* is as follows:
```
"serial" : serial - u64, incremented by one with every update
"delta": delta - string, can be either "positive" (given IP address added) or "negative" (given IP address removed)
"ip": ip - string, IP address that was removed/added from/to the list
"ts" : timestamp - u64, Unix time of when a message was generated
```


### dynfw/event

`dynfw/event` is produced when DynFW receives an notification about potentially 
malicious event.

The structure of message *payload* is as follows:
```
"event": event - string, identifying type of an event
"ip": ip - string, IP address that caused the event
"ts" : timestamp - u64, Unix time of when a message was generated
```

The following event types are currently recognized:

#### Events obtained from project [HaaS](https://docs.turris.cz/basics/sentinel/threat-detection/#haas-honeypot-as-a-service):
```
"haas_not_logged" - not logged to SSH Honeypot
"haas_logged" - logged to SSH Honeypot
"haas_logged_active" - logged and active in SSH Honeypot
```

#### Events captured by [Minipots](https://docs.turris.cz/basics/sentinel/threat-detection/#minipot):
```
"telnet_connect" - connection to a Telnet minipot
"telnet_login" - login to a Telnet minipot
"telnet_invalid" - invalid interaction with Telnet minipot

"ftp_connect" - connection to a FTP minipot
"ftp_login" - login to a FTP minipot
"ftp_invalid" - invalid interaction with FTP minipot

"smtp_connect" - connection to a SMTP minipot
"smtp_login" - login to a SMTP minipot
"smtp_invalid" - invalid interaction with SMTP minipot

"http_connect" - connection to a HTTP minipot
"http_message" - request sent to HTTP minipot
"http_login" - request containing "Authorization" header sent to a HTTP minipot
"http_invalid" - invalid interaction with HTTP minipot
```

#### Events captured by [Firewall monitoring](https://docs.turris.cz/basics/sentinel/threat-detection/#firewall-monitoring):
```
"fwlogs_small_port_scan" - small part scan
"fwlogs_big_port_scan" - big port scan
```

## Authentication and connection within DynFW server

Communication between a server and a client is secured by ZMQ
[CURVE](http://api.zeromq.org/master:zmq-curve) mechanism for secure
authentication and confidentiality. Server allows connection to all clients
from all domains.

To connect to DynFW server you need to:
- Download the server public certificate from `https://repo.turris.cz/sentinel/dynfw.pub`
- Create and/or load a client certificate
- Connect to the server at ZMQ endpoint `tcp://sentinel.turris.cz:7087`


## General client workflow

The fully functional client should do:

- Subscribe to the `dynfw/list` topic.
- Wait for `dynfw/list` message.
- Use the list to set stuff up - e.g. for first initialization of firewall.
- Unsubscribe from `dynfw/list` topic.
- Subscribe to `dynfw/delta` topic.
- Add/remove addresses to/from your list according to incoming deltas.

There is one special value in delta message: `serial`. This should be an
increasing number. If you observe a big gap between two messages you probably
want to unsubscribe `dynfw/delta` topic and repeat the previous process.
If you get non-consecutive numbers, you should repeat the initialization process
as well. The `version` is sometimes reset to 0.


## Example client dependencies and installation

This code must run in reasonably new Python 3 and has following dependencies:

- zmq
- msgpack
- urllib3

So:

```
pip install zmq msgpack urllib3
./dynfw_client.py
```
works perfectly fine.
