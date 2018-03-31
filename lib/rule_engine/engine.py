#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  rule_engine/engine.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the project nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import functools

from . import ast
from . import errors
from . import parser

def resolve_attribute(thing, name):
	if not hasattr(thing, name):
		raise errors.SymbolResolutionError(name)
	return getattr(thing, name)

def resolve_item(thing, name):
	if not name in thing:
		raise errors.SymbolResolutionError(name)
	return thing[name]

def _type_resolver(type_map, name):
	return type_map[name]

def type_resolver_from_dict(dictionary):
	type_map = {key: ast.DataType.from_value(value) for key, value in dictionary.items()}
	return functools.partial(_type_resolver, type_map)

class Context(object):
	def __init__(self, regex_flags=0, resolver=None, type_resolver=None):
		self.regex_flags = regex_flags
		self.symbols = set()
		self.__type_resolver = type_resolver or (lambda _: ast.DataType.UNDEFINED)
		self.__resolver = resolver or resolve_item

	def resolve(self, thing, name):
		return self.__resolver(thing, name)

	def resolve_type(self, name):
		return self.__type_resolver(name)

class Rule(object):
	parser = parser.Parser()
	def __init__(self, text, context=None):
		context = context or Context()
		self.text = text
		self.context = context
		self.statement = self.parser.parse(text, context)

	def __repr__(self):
		return "<{0} text={1!r} >".format(self.__class__.__name__, self.text)

	def filter(self, things):
		yield from (thing for thing in things if self.matches(thing))

	@classmethod
	def is_valid(cls, text):
		try:
			cls.parser.parse(text)
		except errors.RuleSyntaxError:
			return False
		return True

	def matches(self, thing):
		return bool(self.statement.evaluate(self.context, thing))