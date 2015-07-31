# -*- coding: utf-8 -*-
# pluginmanager.py

from collections import defaultdict
import sys
import imp
import os

# list of registred plug-ins
plugins = defaultdict(list)
# list of disable event plug-in
disabled_event = []
# list of disabled plug-ins
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
	for c in plugins.items():
		event, functions = c
		for f in functions:
			if plugin == f.__module__ and event in disabled_event:
				disabled_event.remove(event)
				if plugin in disabled_plugin:
					disabled_plugin.remove(plugin)

def disable_plugin(plugin):
	""" Append resp. the plugin and the event to the disabled_plugin and disabled_event lists.
	"""

	for c in plugins.items():
		event, functions = c
		for f in functions:
			if plugin == f.__module__ and event not in disabled_event:
				if hasattr(sys.modules[plugin],'UnConfig'):
					apply(sys.modules[plugin].UnConfig,())
				disabled_event.append(event)
				if plugin not in disabled_plugin:
					disabled_plugin.append(plugin)


def is_enable(plugin):
	"""
	"""
	if isinstance(plugin, str):
		return plugin in [l[0].__name__ for l in plugins.values()]
	else:
		return plugin in plugins.values()

def trigger_event(event, *args, **kwargs):
	""" Call this function to trigger an event. It will run any plug-ins that
		have registered themselves to the event. Any additional arguments or
		keyword arguments you pass in will be passed to the plug-ins.
	"""
	for plugin in plugins[event]:
		if event not in disabled_event:
			plugin(*args, **kwargs)

def load_plugins(module_name):
	""" This reads a plug-ins list to load. It is so plug-in
		imports are more dynamic and you don't need to continue appending
		import statements to the top of a file.
	"""

	try:
		return sys.modules[module_name]
	except KeyError:
		try:
			f, filename, description = imp.find_module(module_name, [PLUGINS_PATH])
			module = imp.load_module(module_name, f, filename, description)
			f.close()
			return module
		except Exception, info:
			msg = _("Path of plug-ins directory is wrong.") if not os.path.exists(PLUGINS_PATH) else ""
			sys.stderr.write("Error trying to import plug-in %s : %s\n%s"%(module_name, info, msg))
			return info