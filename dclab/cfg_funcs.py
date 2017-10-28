#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import sys

if sys.version_info[0] == 2:
    str_types = (str, unicode)
else:
    str_types = str


def fbool(value):
    """boolean"""
    if isinstance(value, str_types):
        value = value.lower()
        if value == "false":
            value = False
        elif value == "true":
            value = True
        elif value:
            value = bool(float(value))
        else:
            raise ValueError("empty string")
    else:
        value = bool(float(value))
    return value


def fintlist(alist):
    """A list of integers"""
    outlist = []
    if not isinstance(alist, (list, tuple)):
        # we have a string (comma-separated integers)
        alist = alist.strip().strip("[] ").split(",")
    for it in alist:
        if it:
            outlist.append(int(it))
    return outlist


def lcstr(astr):
    """lower-case string"""
    return astr.lower()


func_types = {fbool: bool,
              fintlist: list}
