# Example client for Turris:Sentinel DynFW

This simple script is an example of code that is able to connect to the DynFW
server and obtain published data for further processing.

## Introduction

Some terminology first:

### Turris:Sentinel

Turris:Sentinel - or simply Sentinel - is a new data collect platform. It is a
replacement of old uCollect technology. The main changes are made in our server
infrastructure, but there are new SW clients at routers too.

### DynFW

Dynamic FireWall - aka DynFW - is one of the new parts of our project. We obtain
security alerts from several sources and with this knowledge we build a list of
bad guys.

This list is built real-time and the whole interface is accessible. So, everyone
is able to consume real-time data in any manner they want.

## Protocol overview

Our server publishes several types of messages. Currently, there are 2 main
types: `dynfw/list` and `dynfw/delta`.

The idea is as follows:

`dynfw/list` message contains the whole list of the bad guys but the list is
usually long with only small changes. The message is published every 10 seconds
(currently). This is the way how to get your initial list, but it shouldn't be
abused to keep it up to date. For that use dynfw/delta messages.

`dynfw/delta` message is produced exactly at the moment when we decide to put
the address to the list or remove it.

The fully functional client should do:

- Subscribe to the `dynfw/list` topic.
- Wait for `dynfw/list` message. You shouldn't wait longer than 10 seconds.
- Use the list to set stuff up - e.g. for first initialization of firewall.
- Unsubscribe from `dynfw/list` topic.
- Subscribe to `dynfw/delta` topic.
- Add/remove addresses to/from your list according to incoming deltas.

There is one special value in delta message: `serial`. This should be an
increasing number. If you observe a big gap between 2 messages you probably want
to unsubscribe `dynfw/delta` topic and repeat the previous process. If you get
non-consecutive numbers, you should repeat the initialization process as well.
We reset the number time to time if we need to force the clients to make reload.

## Example client dependencies/installation

This code must run in reasonably new Python3 and has following dependencies:

- zmq
- msgpack
- urllib3

So:

```
pip install zmq msgpack urllib3
./dynfw_client.py
```
works perfectly fine.
