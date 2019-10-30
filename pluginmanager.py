# -*- coding: utf-8 -*-
# pluginmanager.py

from collections import defaultdict
from Utilities import listf
from traceback import format_exception

import sys
import imp
import os
import importlib

# list of registred plug-ins
plugins = defaultdict(list)
# list of enable/disable event plug-in
enabled_event = []
disabled_event = []
# list of enable/disabled plug-ins
enabled_plugin = []
disabled_plugin = []

def idle(*args, **kwargs):
	pass

def register(*events):
	""" This decorator is to be used for registering a function as a plug-in for
		a specific event or list of events.
	"""
	def registered_plugin(funct):
		for event in events:
			plugins[event].append(funct)
		return funct
	return registered_plugin

def enable_plugin(plugin):
	""" Remove resp. the plug-in and the event from the disabled_plugin and disabled_event lists.
	"""
	for event, functions in list(plugins.items()):
		for f in functions:
			if plugin == f.__module__ and event in disabled_event:
				if event not in enabled_event: enabled_event.append(event)
				if event in disabled_event: disabled_event.remove(event)
				if plugin not in enabled_plugin: enabled_plugin.append(plugin)
				if plugin in disabled_plugin: disabled_plugin.remove(plugin)

def disable_plugin(plugin):
	""" Append resp. the plug-in and the event to the disabled_plugin and disabled_event lists.
	"""

	for event, functions in list(plugins.items()):
		for f in functions:
			if plugin == f.__module__ and event not in disabled_event:
				if hasattr(sys.modules[plugin],'UnConfig'):
					sys.modules[plugin].UnConfig(*())

				if event in enabled_event: enabled_event.remove(event)
				if event not in disabled_event: disabled_event.append(event)
				if plugin in enabled_plugin: enabled_plugin.remove(plugin)
				if plugin not in disabled_plugin: disabled_plugin.append(plugin)


def is_enable(plugin):
	""" Enable plugin
	"""
	if isinstance(plugin, str):
		return plugin in enabled_plugin
		#return plugin in [l[0].__name__ for l in plugins.values() if l != [] ]
	else:
		return plugin in list(plugins.values())

def trigger_event(event, *args, **kwargs):
	""" Call this function to trigger an event. It will run any plug-ins that
		have registered themselves to the event. Any additional arguments or
		keyword arguments you pass in will be passed to the plugins.
	"""
	for plugin in plugins[event]:
		if event not in disabled_event:
			plugin(*args, **kwargs)

def load_plugins(modulename):
	""" This reads a plugins list to load. It is so plug-in
		imports are more dynamic and you don't need to continue appending
		import statements to the top of a file.
	"""

	try:
		return sys.modules[modulename]
	except KeyError:
		try:
			if PLUGINS_PATH not in sys.path:
				sys.path.append(PLUGINS_PATH)
			name,ext = os.path.splitext(modulename)
			pkg = '.'.join(modulename.split('.')[0:-1])
			module = importlib.import_module(name, package=pkg)
			return module
		except Exception as info:
			msg = _("Path of plugins directory is wrong.") if not os.path.exists(PLUGINS_PATH) else str(sys.exc_info()[0]) +"\r\n" + listf(format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
			sys.stderr.write(_("Error trying to import plugin %s : %s\n%s")%(modulename, info, msg))
			return info