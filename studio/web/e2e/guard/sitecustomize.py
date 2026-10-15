"""Cooperative runtime guard inherited by the host and its Python workers.

This is a regression-test boundary, not an OS security sandbox.
"""
import ipaddress
import os
import socket
import sys


def audit(event, args):
    if event not in {'socket.connect', 'socket.getaddrinfo'}:
        return
    address = args[1] if event == 'socket.connect' else args[0]
    host = address[0] if isinstance(address, tuple) else address
    if event == 'socket.connect' and args[0].family == socket.AF_UNIX:
        return
    try:
        allowed = ipaddress.ip_address(host).is_loopback
    except ValueError:
        allowed = host == 'localhost'
    if not allowed:
        with open(os.environ['HARNESS_NETWORK_LOG'], 'a') as stream:
            stream.write(f'{os.getpid()} {event} {host!r}: non-loopback access blocked\n')
        raise RuntimeError('Harness runtime forbids non-loopback network access')


sys.addaudithook(audit)
