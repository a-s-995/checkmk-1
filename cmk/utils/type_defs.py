#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""Checkmk wide type definitions"""

import abc
import string
from typing import Union, NamedTuple, NewType, Any, Text, Optional, Dict, Set, List, Tuple

import six

HostName = str
HostAddress = str
HostgroupName = str
ServiceName = Text
ServicegroupName = str
ContactgroupName = str
TimeperiodName = str
RawAgentData = bytes
RulesetName = str
RuleValue = Any  # TODO: Improve this type
RuleSpec = Dict[str, Any]  # TODO: Improve this type
Ruleset = List[RuleSpec]  # TODO: Improve this type
MetricName = str
CheckPluginName = str
InventoryPluginName = str
ActiveCheckPluginName = str
Item = Optional[Text]
TagValue = str
Labels = Dict[Text, Text]
LabelSources = Dict[Text, str]
TagID = str
TaggroupID = str
Tags = Dict[TagID, TagValue]
TagList = Set[TagValue]
TagGroups = Dict[TagID, TaggroupID]
HostNameConditions = Union[None, Dict[str, List[Union[Dict[str, str], str]]],
                           List[Union[Dict[str, str], str]]]
ServiceNameConditions = Union[None, Dict[str, List[Union[Dict[str, Text], Text]]],
                              List[Union[Dict[str, Text], Text]]]
CheckVariables = Dict[str, Any]
Seconds = int
Timestamp = int
TimeRange = Tuple[int, int]

ServiceState = int
HostState = int
ServiceDetails = Text
ServiceAdditionalDetails = Text
# TODO: Specify this  (see cmk/base/checking.py::_convert_perf_data)
Metric = List
ServiceCheckResult = Tuple[ServiceState, ServiceDetails, List[Metric]]

UserId = NewType("UserId", Text)
EventRule = Dict[str, Any]  # TODO Improve this

AgentHash = NewType("AgentHash", str)
BakeryOpSys = NewType("BakeryOpSys", str)
AgentConfig = Dict[str, Any]  # TODO Split into more sub configs
BakeryHostName = Union[bool, None, HostName]

# TODO: TimeperiodSpec should really be a class or at least a NamedTuple! We
# can easily transform back and forth for serialization.
TimeperiodSpec = Dict[str, Union[Text, List[Tuple[str, str]]]]

ContextName = str
DecodedString = Text
DecodedBinary = List[int]
DecodedValues = Union[DecodedString, DecodedBinary]
SNMPValueEncoding = str
SNMPTable = List[List[DecodedValues]]

SectionName = str
SNMPSectionContent = Union[SNMPTable, List[SNMPTable]]
SNMPSections = Dict[SectionName, SNMPSectionContent]
PersistedSNMPSection = Tuple[int, int, SNMPSectionContent]
PersistedSNMPSections = Dict[SectionName, PersistedSNMPSection]
RawSNMPData = SNMPSections

Column = Union[str, int, Tuple[SNMPValueEncoding, str]]
Columns = List[Column]

OID = str
OIDWithColumns = Tuple[OID, Columns]
OIDWithSubOIDsAndColumns = Tuple[OID, List[OID], Columns]

# TODO (CMK-4490): Typing here is just wrong as there is no practical
# difference between an OIDWithColumns and OIDWithSubOIDsAndColumns with
# an empty List[OID].
SingleOIDInfo = Union[OIDWithColumns, OIDWithSubOIDsAndColumns]
MultiOIDInfo = List[SingleOIDInfo]
OIDInfo = Union[SingleOIDInfo, MultiOIDInfo]

RawValue = bytes
SNMPRowInfo = List[Tuple[OID, RawValue]]

# TODO: Be more specific about the possible tuples
# if the credentials are a string, we use that as community,
# if it is a four-tuple, we use it as V3 auth parameters:
# (1) security level (-l)
# (2) auth protocol (-a, e.g. 'md5')
# (3) security name (-u)
# (4) auth password (-A)
# And if it is a six-tuple, it has the following additional arguments:
# (5) privacy protocol (DES|AES) (-x)
# (6) privacy protocol pass phrase (-X)
SNMPCommunity = str
# TODO: This does not work as intended
#SNMPv3NoAuthNoPriv = Tuple[str, str]
#SNMPv3AuthNoPriv = Tuple[str, str, str, str]
#SNMPv3AuthPriv = Tuple[str, str, str, str, str, str]
#SNMPCredentials = Union[SNMPCommunity, SNMPv3NoAuthNoPriv, SNMPv3AuthNoPriv, SNMPv3AuthPriv]
SNMPCredentials = Union[SNMPCommunity, Tuple[str, ...]]

# TODO: Cleanup to named tuple
SNMPTiming = Dict


# Wraps the configuration of a host into a single object for the SNMP code
class SNMPHostConfig(
        NamedTuple("SNMPHostConfig", [
            ("is_ipv6_primary", bool),
            ("hostname", HostName),
            ("ipaddress", HostAddress),
            ("credentials", SNMPCredentials),
            ("port", int),
            ("is_bulkwalk_host", bool),
            ("is_snmpv2or3_without_bulkwalk_host", bool),
            ("bulk_walk_size_of", int),
            ("timing", SNMPTiming),
            ("oid_range_limits", list),
            ("snmpv3_contexts", list),
            ("character_encoding", Optional[str]),
            ("is_usewalk_host", bool),
            ("is_inline_snmp_host", bool),
            ("record_stats", bool),
        ])):
    @property
    def is_snmpv3_host(self):
        # type: () -> bool
        return isinstance(self.credentials, tuple)

    def update(self, **kwargs):
        # type: (Dict[str, Any]) -> SNMPHostConfig
        """Return a new SNMPHostConfig with updated attributes."""
        cfg = self._asdict()
        cfg.update(**kwargs)
        return SNMPHostConfig(**cfg)


class OIDSpec(object):  # pylint: disable=bad-option-value, useless-object-inheritance
    """Basic class for OID spec of the form ".1.2.3.4.5" or "2.3"
    """
    VALID_CHARACTERS = '.' + string.digits

    @classmethod
    def validate(cls, value):
        # type: (str) -> None
        if not isinstance(value, str):
            raise TypeError("expected a non-empty string: %r" % (value,))
        if not value:
            raise ValueError("expected a non-empty string: %r" % (value,))

        invalid = ''.join(c for c in value if c not in cls.VALID_CHARACTERS)
        if invalid:
            raise ValueError("invalid characters in OID descriptor: %r" % invalid)

        if value.endswith('.'):
            raise ValueError("%r should not end with '.'" % (value,))

    def __init__(self, value):
        # type: (str) -> None
        self.validate(value)
        self._value = value

    def __add__(self, right):
        # type: (Any) -> OIDSpec
        """Concatenate two OID specs

        We only allow adding (left to right) a "base" (starting with a '.')
        to an "column" (not starting with '.').
        We preserve the type of the column, which may signal caching or byte encoding.
        """
        if not isinstance(right, OIDSpec):
            raise TypeError("cannot add %r" % (right,))
        if not self._value.startswith('.') or right._value.startswith('.'):
            raise ValueError("can only add full OIDs to partial OIDs")
        return right.__class__("%s.%s" % (self, right))

    def __eq__(self, other):
        # type: (Any) -> bool
        if other.__class__ != self.__class__:
            return False
        return self._value == other._value

    def __str__(self):
        # type: () -> str
        return self._value

    def __repr__(self):
        # type: () -> str
        return "%s(%r)" % (self.__class__.__name__, self._value)


# The old API defines OID_END = 0.  Once we can drop the old API,
# replace every occurence of this with OIDEnd.
CompatibleOIDEnd = int


class ABCSNMPTree(six.with_metaclass(abc.ABCMeta)):
    # pylint: disable=no-init

    @property
    @abc.abstractmethod
    def base(self):
        # type: () -> OIDSpec
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def oids(self):
        # type: () -> List[Union[OIDSpec, CompatibleOIDEnd]]
        raise NotImplementedError()


# TODO: We should really parse our configuration file and use a
# class/NamedTuple, see above.
def timeperiod_spec_alias(timeperiod_spec, default=u""):
    # type: (TimeperiodSpec, Text) -> Text
    alias = timeperiod_spec.get("alias", default)
    if isinstance(alias, Text):
        return alias
    raise Exception("invalid timeperiod alias %r" % (alias,))
