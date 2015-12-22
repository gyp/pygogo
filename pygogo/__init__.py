# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:expandtab

"""
pygogo
~~~~~~

A Python logging library with super powers

Examples:
    basic usage::

        >>> logger = Gogo('basic').logger
        >>> logger.debug('hello world')
        hello world

    intermediate usage::

        >>> formatter = logging.Formatter('IP: %(ip)s - %(message)s')
        >>> kwargs = {'low_formatter': formatter}
        >>> logger = Gogo('intermediate', **kwargs).get_logger(ip='1.1.1.1')
        >>> logger.debug('hello world')
        IP: 1.1.1.1 - hello world

    advanced usage::

        >>> kwargs = {'monolog': True, 'high_hdlr': handlers.stdout_hdlr()}
        >>> logger = Gogo('adv', **kwargs).get_structured_logger(ip='1.1.1.1')
        >>> logger.debug('hello world')
        {"ip": "1.1.1.1", "message": "hello world"}
        >>> logger.error('hello world')
        {"ip": "1.1.1.1", "message": "hello world"}
"""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import logging
import hashlib
import sys

from copy import copy
from . import formatters, handlers, utils

__version__ = '0.6.2'

__all__ = ['formatters', 'handlers', 'utils']
__title__ = 'pygogo'
__author__ = 'Reuben Cummings'
__description__ = 'A Python logging library with super powers'
__email__ = 'reubano@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Reuben Cummings'

hdlr = logging.StreamHandler(sys.stdout)
fltr = logging.Filter(name='%s.init' % __name__)
hdlr.addFilter(fltr)  # prevent handler from logging `pygogo.main` events
module_logger = logging.getLogger(__name__)
module_logger.addHandler(hdlr)


class Gogo(object):
    """A logging class that logs events via different handlers depending on the
    severity

    http://stackoverflow.com/a/28743317/408556

    Attributes:
        loggers (set[str]): Set of existing loggers

        monolog (bool): Log high level events only to high pass handler.

        name (string): The logger name.

        high_level (string): The min level to log to high_hdlr.

        low_level (string): The min level to log to low_hdlr.

        high_hdlr (obj): The high pass log handler.

        low_hdlr (obj): The low pass log handler.

        high_formatter (obj): The high pass log formatter.

        low_formatter (obj): The low pass log formatter.

        +----------------------------+-------------------------+
        | messages level             | message handler         |
        +============================+=========================+
        | < low_level                | none                    |
        +----------------------------+-------------------------+
        | >= low_level, < high_level | low_hdlr                |
        +----------------------------+-------------------------+
        | >= high_level              | low_hdlr and high_hdlr* |
        +----------------------------+-------------------------+

        * This is the case when :attr:`monolog` is `False`. If :attr:`monolog`
          is True, then :attr:`high_hdlr` will be the only message handler

    Args:
        name (string): The logger name.

        high_level (string): The min level to log to high_hdlr
            (default: warning).

        low_level (string): The min level to log to low_hdlr
            (default: debug).

        kwargs (dict): Keyword arguments.

    Kwargs:
        high_hdlr (obj): The high pass log handler (a :class:`logging.handlers`
            instance, default: `stderr` StreamHandler).

        low_hdlr (obj): The low pass log handler (a :class:`logging.handlers`
            instance, default: `stdout` StreamHandler).

        high_formatter (obj): The high pass log formatter (a
            :class:`logging.Formatter` instance, default:
            :data:`pygogo.formatters.basic_formatter`).

        low_formatter (obj): The low pass log formatter (a
            :class:`logging.Formatter` instance, default:
            :data:`pygogo.formatters.basic_formatter`).

        verbose (bool): If False, set low level to `info`, if True, set low
            level to `debug`, overrides `low_level` if specified
            (default: None).

        monolog (bool): Log high level events only to high pass handler (
            default: False)

    Returns:
        New instance of :class:`pygogo.Gogo`

    Examples:
        >>> Gogo('name').logger.debug('message')
        message
    """

    def __init__(self, name='root', high_level=None, low_level=None, **kwargs):
        """Initialization method.

        Examples:
            >>> Gogo('name') # doctest: +ELLIPSIS
            <pygogo.Gogo object at 0x...>
        """
        verbose = kwargs.get('verbose')
        high_level = high_level or 'warning'

        if verbose is None:
            low_level = low_level or 'debug'
        elif verbose:
            low_level = 'debug'
        else:
            low_level = 'info'

        self.high_level = getattr(logging, high_level.upper(), None)
        self.low_level = getattr(logging, low_level.upper(), None)

        if not isinstance(self.high_level, int):
            raise ValueError('Invalid high_level: %s' % self.high_level)
        elif not isinstance(self.low_level, int):
            raise ValueError('Invalid low_level: %s' % self.low_level)
        elif not self.high_level >= self.low_level:
            raise ValueError('high_level must be >= low_level')

        self.loggers = set([])
        self.name = name
        self.high_hdlr = kwargs.get('high_hdlr')
        self.low_hdlr = kwargs.get('low_hdlr')
        self.high_formatter = kwargs.get('high_formatter')
        self.low_formatter = kwargs.get('low_formatter')
        self.monolog = kwargs.get('monolog')

    @property
    def logger(self):
        """The logger property.

        Returns:
            New instance of :class:`logging.Logger`

        Examples:
            >>> from testfixtures import LogCapture
            >>> logger = Gogo('default').logger
            >>> logger # doctest: +ELLIPSIS
            <logging.Logger object at 0x...>
            >>> logger.debug('stdout')
            stdout
            >>> kwargs = {'low_level': 'info', 'monolog': True}
            >>> logger = Gogo('ignore_if_lt_info', **kwargs).logger
            >>> logger.debug('ignored')
            >>> logger.info('stdout')
            stdout
            >>> with LogCapture() as l:
            ...     logger.warning('stderr')
            ...     print(l)
            ignore_if_lt_info.base WARNING
              stderr
        """
        return self.get_logger()

    def copy_hdlr(self, hdlr):
        """Safely copy a handler and its associated filters.

        Args:
            hdlr (obj): A :class:`logging.handlers` instance.

        See also:
            :meth:`pygogo.Gogo.get_logger`

            :meth:`pygogo.Gogo.get_structured_logger`

        Returns:
            New instance of :class:`logging.handlers`

        Examples:
            >>> hdlr = logging.StreamHandler(sys.stdout)
            >>> Gogo().copy_hdlr(hdlr) # doctest: +ELLIPSIS
            <logging.StreamHandler object at 0x...>
        """
        copied_hdlr = copy(hdlr)
        copied_hdlr.filters = map(copy, hdlr.filters)
        return copied_hdlr

    def update_hdlr(self, hdlr, level, formatter=None, monolog=False, **kwargs):
        """Update a handler with a formatter, level, and filters.

        Args:
            hdlr (obj): A :class:`logging.handlers` instance.

            level (int): The min level to log to to `hdlr`.

            formatter (obj): The log formatter (a :class:`logging.Formatter`
                instance, default: :data:`pygogo.formatters.basic_formatter`)

            monolog (bool): Log high level events only to high pass handler (
                default: False)

            kwargs (dict): Keyword arguemnts passed to
                `pygogo.utils.get_structured_filter`

        See also:
            :meth:`pygogo.Gogo.get_logger`

            :meth:`pygogo.Gogo.get_structured_logger`

            :func:`pygogo.utils.LogFilter`

            :func:`pygogo.utils.get_structured_filter`

        Examples:
            >>> hdlr = logging.StreamHandler(sys.stdout)
            >>> going = Gogo(low_hdlr=hdlr, monolog=True)
            >>> hdlr = going.low_hdlr
            >>> [hdlr.formatter, hdlr.filters, hdlr.level]
            [None, [], 0]
            >>> kwargs = {'monolog': going.monolog}
            >>> going.update_hdlr(hdlr, going.low_level, **kwargs)
            >>> [hdlr.formatter, hdlr.filters, hdlr.level]  # doctest: +ELLIPSIS
            [<logging.Formatter obj...>, [<pygogo.utils.LogFilter obj...>], 10]
        """
        formatter = formatter or formatters.basic_formatter
        hdlr.setLevel(level)

        if monolog:
            log_filter = utils.LogFilter(self.high_level)
            hdlr.addFilter(log_filter)

        if kwargs:
            structured_filter = utils.get_structured_filter(**kwargs)
            hdlr.addFilter(structured_filter)

        hdlr.setFormatter(formatter)

    def zip(self, *fmtrs):
        """Format high/low handler properties so that they can be conveniently
            passed to `update_hdlr`.

        Args:
            fmtrs (seq[obj]): A sequence of :class:`logging.Formatter`
                instances.

        See also:
            :meth:`pygogo.Gogo.update_hdlr`

            :meth:`pygogo.Gogo.get_logger`

            :meth:`pygogo.Gogo.get_structured_logger`

        Returns:
            New instance of :class:`logging.handlers`

        Examples:
            >>> hdlr = logging.StreamHandler(sys.stdout)
            >>> Gogo().copy_hdlr(hdlr) # doctest: +ELLIPSIS
            <logging.StreamHandler object at 0x...>
        """
        self_hdlrs = [self.high_hdlr, self.low_hdlr]
        def_hdlrs = [handlers.stderr_hdlr(), handlers.stdout_hdlr()]

        hdlrs = [s or d for s, d in zip(self_hdlrs, def_hdlrs)]
        levels = [self.high_level, self.low_level]
        fmtrs = [self.high_formatter, self.low_formatter]
        monologs = [False, self.monolog]
        return zip(hdlrs, levels, fmtrs, monologs)

    def get_logger(self, name='base', **kwargs):
        """Retrieve a named logger.

        Args:
            name (string): The logger name.

        See also:
            :meth:`pygogo.Gogo.copy_hdlr`

            :meth:`pygogo.Gogo.update_hdlr`

            :meth:`pygogo.Gogo.zip`

        Returns:
            New instance of :class:`logging.Logger`

        Examples:
            >>> going = Gogo()
            >>> logger = going.get_logger('default')
            >>> logger # doctest: +ELLIPSIS
            <logging.Logger object at 0x...>
            >>> logger.info('from default')
            from default
            >>> going.get_logger('new').info('from new')
            from new
        """
        lggr_name = '%s.%s' % (self.name, name)
        logger = logging.getLogger(lggr_name)

        if lggr_name not in self.loggers:
            self.loggers.add(lggr_name)

            if kwargs:
                kwargs['name'] = lggr_name

            for zipped in self.zip(self.high_formatter, self.low_formatter):
                hdlr, level, fmtr, monolog = zipped
                copied_hdlr = self.copy_hdlr(hdlr)
                self.update_hdlr(copied_hdlr, level, fmtr, monolog, **kwargs)
                logger.addHandler(copied_hdlr)

            logger.setLevel(self.low_level)

        return logger

    def get_structured_logger(self, name=None, **kwargs):
        """Retrieve a structured data logger

        Args:
            name (string): The logger name.

            kwargs (dict): Keyword arguments to include in every log message.

        See also:
            :meth:`pygogo.Gogo.copy_hdlr`

            :meth:`pygogo.Gogo.update_hdlr`

            :meth:`pygogo.Gogo.zip`

            :class:`pygogo.utils.StructuredAdapter`

        Returns:
            New instance of :class:`pygogo.utils.StructuredAdapter`

        Examples
            >>> logger = Gogo('structured').get_structured_logger(all='true')
            >>> logger  # doctest: +ELLIPSIS
            <pygogo.utils.StructuredAdapter object at 0x...>
            >>> logger.debug('hello')
            {"all": "true", "message": "hello"}
            >>> logger.debug('hello', extra={'key': 'value'})
            {"all": "true", "message": "hello", "key": "value"}
        """
        values = frozenset(kwargs.iteritems())
        name = name or hashlib.md5(str(values)).hexdigest()
        lggr_name = '%s.structured.%s' % (self.name, name)
        logger = logging.getLogger(lggr_name)

        if lggr_name not in self.loggers:
            self.loggers.add(lggr_name)
            formatter = formatters.basic_formatter

            for zipped in self.zip(formatter, formatter):
                hdlr, level, fmtr, monolog = zipped
                copied_hdlr = self.copy_hdlr(hdlr)
                self.update_hdlr(copied_hdlr, level, fmtr, monolog)
                logger.addHandler(copied_hdlr)

            logger.setLevel(self.low_level)

        return utils.StructuredAdapter(logger, kwargs)
