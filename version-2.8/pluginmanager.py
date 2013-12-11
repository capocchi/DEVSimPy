# -*- coding: utf-8 -*-
# pluginmanager.py

from collections import defaultdict
import sys
import imp
import os

# list of registred plugins
plugins = defaultdict(list)
# list of disable event plugin
disabled_event = []
# list of disbaled plugins
disabled_plugin = []

def idle(*args, **kwargs):
	pass

def register(*events):
	""" This decorator is to be used for registering a function as a plugin for
		a specific event or list of events.
	"""
	def registered_plugin(funct):
		for event in events:
			plugins[event].append(funct)
		return funct
	return registered_plugin

def enable_plugin(plugin):
	""" Remove resp. the plugin and the event from the disabled_plugin and disabled_event lists.
	"""
	for c in plugins.items():
		event, functions = c
		for f in functions:
			if plugin == f.__module__ and event in disabled_event:
				disabled_event.remove(event)
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
				disabled_plugin.append(plugin)


def is_enable(plugin):
	"""
	"""
	if isinstance(plugin, str):
		return plugin in [l[0].__name__ for l in plugins.values()]
	else:
		return plugin in plugins.values()

def trigger_event(event, *args, **kwargs):
	""" Call this function to trigger an event. It will run any plugins that
		have registered themselves to the event. Any additional arguments or
		keyword arguments you pass in will be passed to the plugins.
	"""
	for plugin in plugins[event]:
		if event not in disabled_event:
			plugin(*args, **kwargs)

def load_plugins(module_name):
	""" This reads a plugins list to load. It is so plugin
		imports are more dynamic and you don't need to continue appending
		import statements to the top of a file.
	"""

	try:
		return sys.modules[module_name]
	except KeyError:
		try:
			f, filename, description = imp.find_module(module_name, [os.path.join(HOME_PATH, PLUGINS_DIR)])
			module = imp.load_module(module_name, f, filename, description)
			f.close()
			return module
		except Exception, info:
			sys.stderr.write("Error trying to import plugin %s : %s\n"%(module_name, info))
			return info