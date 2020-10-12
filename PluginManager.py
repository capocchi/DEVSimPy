# -*- coding: utf-8 -*-
# pluginmanager.py

from collections import defaultdict
from Utilities import listf
from traceback import format_exception

import sys
import os
import importlib

import gettext
_ = gettext.gettext

class PluginManager(object):

	#def __init__(self):
	# list of registred plug-ins
	plugins = defaultdict(list)
	# list of enable/disable event plug-in
	enabled_event = []
	disabled_event = []
	# list of enable/disabled plug-ins
	enabled_plugin = []
	disabled_plugin = []

	@staticmethod
	def register(*events):
		""" This decorator is to be used for registering a function as a plug-in for
			a specific event or list of events.
		"""
		def registered_plugin(funct):
			for event in events:
				PluginManager.plugins[event].append(funct)
			return funct
		return registered_plugin

	@staticmethod
	def enable_plugin(plugin):
		""" Remove resp. the plug-in and the event from the disabled_plugin and disabled_event lists.
		"""
		for event, functions in list(PluginManager.plugins.items()):
			for f in functions:
				if plugin == f.__module__:
					if event not in PluginManager.enabled_event: PluginManager.enabled_event.append(event)
					if event in PluginManager.disabled_event: PluginManager.disabled_event.remove(event)
					if plugin not in PluginManager.enabled_plugin: PluginManager.enabled_plugin.append(plugin)
					if plugin in PluginManager.disabled_plugin: PluginManager.disabled_plugin.remove(plugin)

	@staticmethod
	def disable_plugin(plugin):
		""" Append resp. the plug-in and the event to the disabled_plugin and disabled_event lists.
		"""

		for event, functions in list(PluginManager.plugins.items()):
			for f in functions:
				if plugin == f.__module__:
					if hasattr(sys.modules[plugin],'UnConfig'):
						sys.modules[plugin].UnConfig(*())
					if event in PluginManager.enabled_event: PluginManager.enabled_event.remove(event)
					if event not in PluginManager.disabled_event: PluginManager.disabled_event.append(event)
					if plugin in PluginManager.enabled_plugin: PluginManager.enabled_plugin.remove(plugin)
					if plugin not in PluginManager.disabled_plugin: PluginManager.disabled_plugin.append(plugin)

	@staticmethod
	def is_enable(plugin):
		""" Enable plugin.
		"""
		
		if isinstance(plugin, str):
			return plugin in PluginManager.enabled_plugin
			#return plugin in [l[0].__name__ for l in plugins.values() if l ]
		else:
			return plugin in list(PluginManager.plugins.values())
	
	@staticmethod
	def trigger_event(event, *args, **kwargs):
		""" Call this function to trigger an event. It will run any plug-ins that
			have registered themselves to the event. Any additional arguments or
			keyword arguments you pass in will be passed to the plugins.
		"""
		for plugin in PluginManager.plugins[event]:
			if event not in PluginManager.disabled_event:
				plugin(*args, **kwargs)

	@staticmethod
	def load_plugins(modulename):
		""" This reads a plugins list to load. It is so plug-in
			imports are more dynamic and you don't need to continue appending
			import statements to the top of a file.
		"""

		if modulename in sys.modules:
			return sys.modules[modulename]
		else:
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
