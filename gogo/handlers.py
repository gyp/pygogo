# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:expandtab

"""
gogo.handlers
~~~~~~~~~~~~~

Log handlers

Examples:
    literal blocks::

        python example_google.py

Attributes:
    ENCODING (str): The module encoding
"""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import sys
import logging
import socket

from os import environ
from logging import handlers as hdlrs
from gogo import ENCODING


def stdout_hdlr(**kwargs):
    return logging.StreamHandler(sys.stdout)


def stderr_hdlr(**kwargs):
    return logging.StreamHandler(sys.stderr)


def file_hdlr(filename, mode='a', encoding=ENCODING, delay=False, **kwargs):
    kwargs = {'mode': mode, 'encoding': encoding, 'delay': delay}
    return logging.FileHandler(filename, **kwargs)


def socket_hdlr(host='localhost', port=None, udp=True, **kwargs):
    address = (host, environ.get('SOCKET_PORT', 520))
    handler = hdlrs.DatagramHandler if udp else hdlrs.SocketHandler
    return handler(*address)


def syslog_hdlr(host='localhost', port=None, udp=True, **kwargs):
    address = (host, environ.get('SYSLOG_UDP_PORT', 514))
    socktype = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    return hdlrs.SysLogHandler(address, socktype=socktype)


def buffered_hdlr(target, capacity=2 ** 12, level='ERROR', **kwargs):
    args = (capacity, getattr(logging, level), target)
    return hdlrs.MemoryHandler(*args)


def webhook_hdlr(url, host='localhost', port=None, post=True, **kwargs):
    method = 'POST' if post else 'GET'
    host = '%s:%s' % (host, port) if port else host
    return hdlrs.HTTPHandler(host, url, method=method)


def email_hdlr(subject=None, **kwargs):
    """Sends an email

    Args:
        subject (str): The email subject (default: You've got mail.).

    Kwargs:
        recipients (List[str]): The email recipients.
        host (str): The email host server (default: localhost).
        sender (str): The email sender.

    Examples:
        >>> to = 'reubano@gmail.com'
        >>> email('hello world')  # doctest: +ELLIPSIS
        <smtplib.SMTP instance at 0x...>
    """
    host = kwargs.get('host', 'localhost')
    port = kwargs.get('port')
    address = (host, port) if port else host
    sender = kwargs.get('sender', '%s@gmail.com' % environ.get('USER'))
    def_recipient = '%s@gmail.com' % environ.get('USER')
    recipients = kwargs.get('recipients', [def_recipient])
    subject = kwargs.get('subject', "You've got mail.")
    username = kwargs.get('username')
    password = kwargs.get('password')

    args = (address, sender, recipients, subject)
    credentials = (username, password) if username or password else None
    return hdlrs.SMTPHandler(*args, credentials=credentials)
