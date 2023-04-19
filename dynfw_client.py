#!/usr/bin/env python3

import os
import re
import tempfile
import argparse
import urllib.request

import zmq
import zmq.auth
import msgpack


TMP_CERT_LOCATION = os.path.join(tempfile.gettempdir(), "dynfw_client_certificates")
DOWNLOADED_SERVER_KEY_PATH = os.path.join(tempfile.gettempdir(), "dynfw_client_certificates", "server.pub")

SN_MSG_REGEXP = "^([a-z0-9_]+/)*[a-z0-9_]+$"
SN_MSG = re.compile(SN_MSG_REGEXP)


def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", "-s",
                        metavar="URL",
                        required=False,
                        default="sentinel.turris.cz",
                        help="URL of Sentinel DynFW publisher"
                        )
    parser.add_argument("--port", "-p",
                        required=False,
                        default=7087,
                        type=int,
                        help="Port to connect to"
                        )
    cert_def = parser.add_mutually_exclusive_group()
    cert_def.add_argument("--cert-file", "-c",
                          metavar="PATH",
                          required=False,
                          help="Path to server's certificate"
                          )
    cert_def.add_argument("--download-cert", "-d",
                          metavar="URL",
                          required=False,
                          default="https://repo.turris.cz/sentinel/dynfw.pub",
                          help="URL of published certificate"
                          )

    return parser


def process_message(msg_type, payload):
    """Message processing

    Put something cool here!
    """
    def make_report(data, preview_len=3):
        return "{{'version': {}, 'serial': {}, 'ts': {}, list: Length {}, {}{}}}".format(
            data["version"],
            data["serial"],
            data["ts"],
            len(data["list"]),
            ", ".join(data["list"][:preview_len]),
            "..." if len(data["list"]) > preview_len else ""
        )

    if msg_type == "dynfw/delta":
        print(msg_type, payload, sep=": ")

    elif msg_type == "dynfw/event":
        print(msg_type, payload, sep=": ")

    elif msg_type == "dynfw/list":
        print(msg_type, make_report(payload), sep=": ")

    else:
        print("Whow, unknown message type! There is something new in Turris:Sentinel project.")


def main():
    args = get_arg_parser().parse_args()

    prepare_tmp_dir()

    if args.cert_file:
        server_key_file = args.cert_file
    else:
        download_certificate(args.download_cert)
        server_key_file = DOWNLOADED_SERVER_KEY_PATH

    ctx = zmq.Context.instance()
    sub = prepare_socket(ctx, args.server, args.port, server_key_file)

    print("DynFW client connected and running...")
    while True:
        msg = sub.recv_multipart()
        msg_type, payload = parse_msg(msg)

        process_message(msg_type, payload)


def prepare_tmp_dir():
    if not os.path.exists(TMP_CERT_LOCATION):
        os.mkdir(TMP_CERT_LOCATION, mode=0o700)


def download_certificate(url):
    response = urllib.request.urlopen(url)
    with open(DOWNLOADED_SERVER_KEY_PATH, "wb") as f:
        f.write(response.read())


def prepare_socket(ctx, addr, port, keyfile):
    sub = ctx.socket(zmq.SUB)
    sub.ipv6 = True

    client_public, client_secret = prepare_certificates()
    server_public = load_server_key(keyfile)

    sub.curve_secretkey = client_secret
    sub.curve_publickey = client_public
    sub.curve_serverkey = server_public
    sub.connect("tcp://{}:{}".format(addr, port))

    # I want to subscribe to all messages
    sub.setsockopt(zmq.SUBSCRIBE, b"dynfw/")

    return sub


def prepare_certificates():
    key_path = os.path.join(TMP_CERT_LOCATION, "client.key_secret")
    if not os.path.exists(key_path):
        public, secret = zmq.auth.create_certificates(TMP_CERT_LOCATION, "client")
        assert public
        assert secret

    client_public, client_secret = zmq.auth.load_certificate(key_path)

    return client_public, client_secret


def load_server_key(keyfile):
    public, _ = zmq.auth.load_certificate(keyfile)

    return public


class InvalidMsgError(Exception):
    pass


def parse_msg(data):
    try:
        msg_type = str(data[0], encoding="UTF-8")
        if not SN_MSG.match(msg_type):
            raise InvalidMsgError("Bad message type definition")
        payload = msgpack.unpackb(data[1])

    except IndexError:
        raise InvalidMsgError("Not enough parts in message")

    except (TypeError, msgpack.exceptions.UnpackException, UnicodeDecodeError):
        raise InvalidMsgError("Broken message")

    return msg_type, payload


if __name__ == "__main__":
    main()
