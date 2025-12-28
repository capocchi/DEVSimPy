# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PreferencesGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import wx
import os
import builtins
import shutil
import sys
import configparser
import copy
import importlib
import logging

import wx.lib.filebrowsebutton as filebrowse

_ = wx.GetTranslation

logger = logging.getLogger(__name__)

from HtmlWindow import HtmlFrame

from PluginsGUI import PluginsPanel, GeneralPluginsList
from Utilities import playSound, GetUserConfigDir, GetWXVersionFromIni, AddToInitFile, DelToInitFile, install, getTopLevelWindow, load_and_resize_image
from Decorators import BuzyCursorNotification
from AIAdapter import AdapterFactory

import ReloadModule
import Menu

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASSES DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class GeneralPanel(wx.Panel):
	""" General preferences panel with modern UI
	"""

	### wxPython version
	wxv = [wx.VERSION_STRING]

	def __init__(self, parent):
		"""Constructor."""
		wx.Panel.__init__(self, parent)
		self.default_wxv = GetWXVersionFromIni()
		self.InitUI()

	def InitUI(self):
		"""Initialize user interface with modern layout"""
		
		# Main sizer
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# ============================================================
		# Section 1: Directories
		# ============================================================
		dirBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Directories'))
		
		# Plugins directory
		self.plugin_dir = filebrowse.DirBrowseButton(
			self, wx.NewIdRef(), 
			startDirectory=PLUGINS_PATH,
			labelText=_("Plugins:"),
			toolTip=_("Change the plugins directory"),
			dialogTitle=_("Select plugins directory...")
		)
		self.plugin_dir.SetValue(PLUGINS_PATH)
		dirBox.Add(self.plugin_dir, 0, wx.EXPAND|wx.ALL, 5)
		
		# Library directory
		self.domain_dir = filebrowse.DirBrowseButton(
			self, wx.NewIdRef(),
			startDirectory=DOMAIN_PATH,
			labelText=_("Libraries:"),
			toolTip=_("Change the library directory"),
			dialogTitle=_("Select libraries directory...")
		)
		self.domain_dir.SetValue(DOMAIN_PATH)
		dirBox.Add(self.domain_dir, 0, wx.EXPAND|wx.ALL, 5)
		
		# Output directory
		self.out_dir = filebrowse.DirBrowseButton(
			self, wx.NewIdRef(),
			startDirectory=OUT_DIR,
			labelText=_("Output:"),
			toolTip=_("Change the output directory"),
			dialogTitle=_("Select output directory...")
		)
		self.out_dir.SetValue(OUT_DIR)
		dirBox.Add(self.out_dir, 0, wx.EXPAND|wx.ALL, 5)
		
		mainSizer.Add(dirBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 2: General Settings
		# ============================================================
		settingsBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('General Settings'))
		settingsGrid = wx.FlexGridSizer(4, 2, 10, 10)
		settingsGrid.AddGrowableCol(1, 1)
		
		# Number of recent files
		st1 = wx.StaticText(self, label=_("Recent files:"))
		st1.SetToolTip(_("Maximum number of recent opened files in the menu"))
		self.nb_opened_file = wx.SpinCtrl(self, wx.NewIdRef(), '')
		self.nb_opened_file.SetRange(2, 20)
		self.nb_opened_file.SetValue(NB_OPENED_FILE)
		settingsGrid.Add(st1, 0, wx.ALIGN_CENTER_VERTICAL)
		settingsGrid.Add(self.nb_opened_file, 1, wx.EXPAND)
		
		# Undo/Redo history depth
		st3 = wx.StaticText(self, label=_("History depth:"))
		st3.SetToolTip(_("Number of undo/redo operations to keep in memory"))
		self.nb_history_undo = wx.SpinCtrl(self, wx.NewIdRef(), '')
		self.nb_history_undo.SetRange(2, 100)
		self.nb_history_undo.SetValue(NB_HISTORY_UNDO)
		settingsGrid.Add(st3, 0, wx.ALIGN_CENTER_VERTICAL)
		settingsGrid.Add(self.nb_history_undo, 1, wx.EXPAND)
		
		# Font size
		st2 = wx.StaticText(self, label=_("Font size:"))
		st2.SetToolTip(_("Default font size for block labels"))
		self.font_size = wx.SpinCtrl(self, wx.NewIdRef(), '')
		self.font_size.SetRange(6, 24)
		self.font_size.SetValue(FONT_SIZE)
		settingsGrid.Add(st2, 0, wx.ALIGN_CENTER_VERTICAL)
		settingsGrid.Add(self.font_size, 1, wx.EXPAND)
		
		# wxPython version
		st4 = wx.StaticText(self, label=_("wxPython version:"))
		st4.SetToolTip(_("wxPython version to use (requires restart)"))
		self.cb2 = wx.ComboBox(self, wx.NewIdRef(), self.default_wxv, 
							   choices=GeneralPanel.wxv, style=wx.CB_READONLY)
		settingsGrid.Add(st4, 0, wx.ALIGN_CENTER_VERTICAL)
		settingsGrid.Add(self.cb2, 1, wx.EXPAND)
		
		settingsBox.Add(settingsGrid, 0, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(settingsBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 3: Options
		# ============================================================
		optionsBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Options'))
		
		# Transparency checkbox
		self.cb1 = wx.CheckBox(self, wx.NewIdRef(), _('Enable window transparency'))
		self.cb1.SetToolTip(_("Apply transparency to detached diagram frames"))
		self.cb1.SetValue(getattr(builtins, 'TRANSPARENCY'))
		optionsBox.Add(self.cb1, 0, wx.ALL, 5)
		
		# Notification checkbox
		self.cb11 = wx.CheckBox(self, wx.NewIdRef(), _('Enable notifications'))
		self.cb11.SetToolTip(_("Show notification messages for important events"))
		self.cb11.SetValue(getattr(builtins, 'NOTIFICATION'))
		optionsBox.Add(self.cb11, 0, wx.ALL, 5)
		
		mainSizer.Add(optionsBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 4: Information
		# ============================================================
		infoBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Information'))
		
		infoGrid = wx.FlexGridSizer(3, 2, 5, 10)
		infoGrid.AddGrowableCol(1, 1)
		
		# wxPython version info
		infoGrid.Add(wx.StaticText(self, label=_("Current wxPython:")), 0, 
					wx.ALIGN_CENTER_VERTICAL)
		infoGrid.Add(wx.StaticText(self, label=wx.VERSION_STRING), 0, 
					wx.ALIGN_CENTER_VERTICAL)
		
		# Python version info
		infoGrid.Add(wx.StaticText(self, label=_("Python version:")), 0, 
					wx.ALIGN_CENTER_VERTICAL)
		infoGrid.Add(wx.StaticText(self, label=sys.version.split()[0]), 0, 
					wx.ALIGN_CENTER_VERTICAL)
		
		# Platform info
		infoGrid.Add(wx.StaticText(self, label=_("Platform:")), 0, 
					wx.ALIGN_CENTER_VERTICAL)
		infoGrid.Add(wx.StaticText(self, label=sys.platform), 0, 
					wx.ALIGN_CENTER_VERTICAL)
		
		infoBox.Add(infoGrid, 0, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(infoBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# Add stretch spacer at the end
		mainSizer.AddStretchSpacer(1)
		
		# Set sizer
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)

	def OnApply(self, event):
		"""Apply all changes"""
		
		# Safe copy of default_wxv to manage wx version changing
		old_wxv = copy.copy(self.default_wxv)
		
		# Apply all changes
		changes = []
		
		if self.OnNbOpenedFileChanged(event):
			changes.append(_("Recent files limit"))
		if self.OnNbHistoryUndoChanged(event):
			changes.append(_("History depth"))
		if self.OnFontSizeChanged(event):
			changes.append(_("Font size"))
		if self.OnDomainPathChanged(event):
			changes.append(_("Library directory"))
		if self.OnPluginsDirChanged(event):
			changes.append(_("Plugins directory"))
		if self.OnOutDirChanged(event):
			changes.append(_("Output directory"))
		if self.OnTransparancyChanged(event):
			changes.append(_("Transparency"))
		if self.OnNotificationChanged(event):
			changes.append(_("Notifications"))
		if self.OnwxPythonVersionChanged(event):
			changes.append(_("wxPython version"))
		
		# Show summary of changes
		if changes:
			msg = _("The following settings have been updated:\n\n")
			msg += "\n".join(f"• {c}" for c in changes)
			
			# Check if restart is required
			if self.default_wxv != old_wxv:
				msg += _("\n\nDEVSimPy requires a restart to load the new wxPython version.")
				icon = wx.ICON_WARNING
			else:
				icon = wx.ICON_INFORMATION
			
			dlg = wx.MessageDialog(self, msg, _('Settings Updated'), 
								  wx.OK | icon)
			dlg.ShowModal()
			dlg.Destroy()

	def OnNbOpenedFileChanged(self, event):
		"""Update the number of recent opened files"""
		new_val = self.nb_opened_file.GetValue()
		old_val = getattr(builtins, 'NB_OPENED_FILE')
		
		if new_val != old_val:
			setattr(builtins, 'NB_OPENED_FILE', new_val)
			return True
		return False

	def OnNbHistoryUndoChanged(self, event):
		"""Update the history depth for undo/redo"""
		new_val = self.nb_history_undo.GetValue()
		old_val = getattr(builtins, 'NB_HISTORY_UNDO')
		
		if new_val != old_val:
			setattr(builtins, 'NB_HISTORY_UNDO', new_val)
			return True
		return False

	def OnFontSizeChanged(self, event):
		"""Update font size"""
		new_val = self.font_size.GetValue()
		old_val = getattr(builtins, 'FONT_SIZE')
		
		if new_val != old_val:
			setattr(builtins, 'FONT_SIZE', new_val)
			return True
		return False

	def OnDomainPathChanged(self, event):
		"""Update the domain path"""
		new_domain_dir = self.domain_dir.GetValue()
		old_domain_dir = getattr(builtins, 'DOMAIN_PATH')
		
		# If value has changed, clean the library control panel
		if old_domain_dir != new_domain_dir:
			
			old_parent_domain_dir = os.path.dirname(old_domain_dir)
			
			# Remove the parent of Domain directory if not in devsimpy package
			if old_parent_domain_dir != DEVSIMPY_PACKAGE_PATH:
				if old_parent_domain_dir in sys.path:
					sys.path.remove(old_parent_domain_dir)
			
			# Remove paths from sys.path to update import process
			for path in [p for p in sys.path if old_domain_dir in p]:
				sys.path.remove(path)
			
			# Update builtin
			setattr(builtins, 'DOMAIN_PATH', new_domain_dir)
			
			# Update library tree
			try:
				mainW = getTopLevelWindow()
				nb1 = mainW.GetControlNotebook()
				tree = nb1.GetTree()
				root = tree.GetRootItem()
				
				# Remove all children
				for item in tree.GetItemChildren(root):
					tree.Delete(item)
				
				# Save settings
				mainW.SaveUserSettings()
			except Exception as e:
				wx.LogError(f"Error updating library tree: {str(e)}")
			
			return True
		return False

	def OnPluginsDirChanged(self, event):
		"""Update plugins path"""
		new_val = self.plugin_dir.GetValue()
		old_val = getattr(builtins, 'PLUGINS_PATH')
		
		if new_val != old_val:
			setattr(builtins, 'PLUGINS_PATH', new_val)
			return True
		return False

	def OnOutDirChanged(self, event):
		"""Update output directory"""
		new_val = os.path.basename(self.out_dir.GetValue())
		old_val = getattr(builtins, 'OUT_DIR')
		
		if new_val != old_val:
			setattr(builtins, 'OUT_DIR', new_val)
			return True
		return False

	def OnTransparancyChanged(self, event):
		"""Update window transparency option"""
		new_val = self.cb1.GetValue()
		old_val = getattr(builtins, 'TRANSPARENCY')
		
		if new_val != old_val:
			setattr(builtins, 'TRANSPARENCY', new_val)
			return True
		return False

	def OnNotificationChanged(self, event):
		"""Update notification option"""
		new_val = self.cb11.GetValue()
		old_val = getattr(builtins, 'NOTIFICATION')
		
		if new_val != old_val:
			setattr(builtins, 'NOTIFICATION', new_val)
			return True
		return False

	def OnwxPythonVersionChanged(self, event):
		"""Update wxPython version (deprecated with wx 4.x)"""
		
		# New value
		new_wxv = self.cb2.GetValue()
		
		if new_wxv == self.default_wxv:
			return False
		
		self.default_wxv = new_wxv
		
		# Update ini file in user config directory
		parser = configparser.ConfigParser()
		path = os.path.join(GetUserConfigDir(), 'devsimpy.ini')
		
		# Read existing config
		if os.path.exists(path):
			parser.read(path)
		
		section, option = ('wxversion', 'to_load')
		
		# Remove old section if exists
		if parser.has_section(section):
			parser.remove_section(section)
		
		# Add new section and value
		parser.add_section(section)
		parser.set(section, option, self.default_wxv)
		
		# Write config
		try:
			with open(path, 'w') as f:
				parser.write(f)
			return True
		except IOError as e:
			wx.LogError(f"Error saving wxPython version: {str(e)}")
			return False


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER CONFIGURATION DIALOG
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerConfigDialog(wx.Dialog):
	""" Dialog for configuring broker settings (MQTT, Kafka, etc.)
	"""

	def __init__(self, parent, broker_name):
		""" Initialize broker configuration dialog
		
		Args:
			parent: Parent window
			broker_name: Name of the broker (MQTT, Kafka, etc.)
		"""
		self.broker_name = broker_name
		self.config = {}
		
		# Load existing configuration if available
		self._load_config()
		
		# Calculate dialog size based on number of config items
		# Each field needs ~35 pixels, plus title, info, and buttons
		num_fields = len(self.config)
		dialog_width = 550
		dialog_height = min(200 + (num_fields * 40), 600)  # Cap at 600px
		
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 
						 f"{broker_name} " + _("Broker Configuration"),
						 size=(dialog_width, dialog_height))
		
		# Create UI
		self._create_ui()

	def _load_config(self):
		""" Load broker configuration from config file or builtins
		"""
		import builtins
		import configparser
		from Utilities import GetUserConfigDir
		
		broker_lower = self.broker_name.lower()
		
		# Default configurations per broker
		defaults = {
			'mqtt': {
				'address': 'localhost',
				'port': '1883',
				'username': '',
				'password': '',
				'qos': '1',
				'keepalive': '60',
				'use_tls': False,
			},
			'kafka': {
				'bootstrap': 'localhost:9092',
				'group_id': 'devsimpy',
				'timeout': '30',
			},
			'rabbitmq': {
				'host': 'localhost',
				'port': '5672',
				'username': 'guest',
				'password': 'guest',
			},
		}
		
		self.config = defaults.get(broker_lower, {})
		
		# Try to load from config file
		try:
			config_file = os.path.join(GetUserConfigDir(), 'devsimpy')
			if os.path.exists(config_file):
				cfg = configparser.ConfigParser()
				cfg.read(config_file)
				
				section_name = f'BROKER_{broker_lower.upper()}'
				if cfg.has_section(section_name):
					for key in self.config.keys():
						if cfg.has_option(section_name, key):
							value = cfg.get(section_name, key)
							# Convert boolean strings
							if value.lower() in ('true', 'false'):
								self.config[key] = value.lower() == 'true'
							else:
								self.config[key] = value
					logger.info(f"Loaded {self.broker_name} configuration from file")
					return
		except Exception as e:
			logger.warning(f"Could not load config from file: {e}")
		
		# Fall back to builtins
		try:
			saved_key = f'BROKER_CONFIG_{broker_lower.upper()}'
			if hasattr(builtins, saved_key):
				saved_config = getattr(builtins, saved_key, {})
				self.config.update(saved_config)
		except Exception as e:
			logger.warning(f"Could not load config from builtins: {e}")

	def _create_ui(self):
		""" Create the configuration UI
		"""
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		# Title
		title = wx.StaticText(self, label=f"{_('Configure')} {self.broker_name}")
		font = title.GetFont()
		font.PointSize = 12
		font = font.Bold()
		title.SetFont(font)
		sizer.Add(title, 0, wx.ALL, 10)
		
		# Configuration fields based on broker type
		grid = wx.FlexGridSizer(rows=len(self.config), cols=2, vgap=10, hgap=10)
		grid.AddGrowableCol(1, 1)
		
		self.config_controls = {}
		
		for key, value in self.config.items():
			# Create label
			label = wx.StaticText(self, label=f"{key.replace('_', ' ').title()}:")
			
			# Create control based on value type
			if isinstance(value, bool):
				ctrl = wx.CheckBox(self)
				ctrl.SetValue(value)
			else:
				ctrl = wx.TextCtrl(self, value=str(value))
			
			self.config_controls[key] = ctrl
			grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
			grid.Add(ctrl, 1, wx.EXPAND)
		
		sizer.Add(grid, 1, wx.EXPAND|wx.ALL, 10)
		
		# Info text
		info_text = wx.StaticText(
			self,
			label=self._get_broker_info()
		)
		info_text.SetForegroundColour(wx.Colour(100, 100, 100))
		sizer.Add(info_text, 0, wx.EXPAND|wx.ALL, 10)
		
		# Buttons
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		test_btn = wx.Button(self, wx.ID_ANY, _("Test Connection"))
		test_btn.Bind(wx.EVT_BUTTON, self.OnTestConnection)
		btn_sizer.Add(test_btn, 0, wx.RIGHT, 5)
		
		ok_btn = wx.Button(self, wx.ID_OK, _("OK"))
		cancel_btn = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
		btn_sizer.Add(ok_btn, 0, wx.RIGHT, 5)
		btn_sizer.Add(cancel_btn, 0)
		
		sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
		
		self.SetSizer(sizer)
		
		# Bind OK button to save configuration
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)

	def OnOK(self, evt):
		""" Save configuration when OK is clicked
		"""
		import builtins
		import configparser
		from Utilities import GetUserConfigDir
		
		# Gather configuration from controls
		config = {}
		for key, ctrl in self.config_controls.items():
			if isinstance(ctrl, wx.CheckBox):
				config[key] = str(ctrl.GetValue())
			else:
				config[key] = ctrl.GetValue()
		
		# Save to builtins
		broker_lower = self.broker_name.lower()
		saved_key = f'BROKER_CONFIG_{broker_lower.upper()}'
		setattr(builtins, saved_key, config)
		
		# Save to .devsimpy config file
		try:
			config_file = os.path.join(GetUserConfigDir(), 'devsimpy')
			cfg = configparser.ConfigParser()
			
			# Read existing config
			if os.path.exists(config_file):
				cfg.read(config_file)
			
			# Ensure BROKERS section exists
			if not cfg.has_section('BROKERS'):
				cfg.add_section('BROKERS')
			
			# Save broker-specific config
			section_name = f'BROKER_{broker_lower.upper()}'
			if not cfg.has_section(section_name):
				cfg.add_section(section_name)
			
			for key, value in config.items():
				cfg.set(section_name, key, str(value))
			
			# Write to file
			with open(config_file, 'w') as f:
				cfg.write(f)
			
			logger.info(f"Saved {self.broker_name} configuration to {config_file}")
		except Exception as e:
			logger.error(f"Error saving broker config to file: {e}")
		
		# Also update mqttconfig if MQTT
		if self.broker_name == 'MQTT':
			try:
				setattr(builtins, 'MQTT_BROKER_ADDRESS', config.get('address', 'localhost'))
				setattr(builtins, 'MQTT_BROKER_PORT', int(config.get('port', 1883)))
				setattr(builtins, 'MQTT_USERNAME', config.get('username') or None)
				setattr(builtins, 'MQTT_PASSWORD', config.get('password') or None)
				logger.info(f"Saved MQTT configuration: {config.get('address')}:{config.get('port')}")
			except Exception as e:
				logger.error(f"Error saving MQTT config: {e}")
		
		# Close dialog
		self.EndModal(wx.ID_OK)

	def _get_broker_info(self):
		""" Get information about the broker
		"""
		info_dict = {
			'MQTT': 'MQTT (MQ Telemetry Transport) - Lightweight pub/sub messaging protocol.\nDefault: localhost:1883',
			'Kafka': 'Apache Kafka - Distributed event streaming platform.\nDefault: localhost:9092',
			'RabbitMQ': 'RabbitMQ - Open source message broker.\nDefault: localhost:5672',
		}
		return info_dict.get(self.broker_name, f"Configure {self.broker_name} broker settings.")

	def OnTestConnection(self, evt):
		""" Test the broker connection
		"""
		# Gather configuration
		config = {}
		for key, ctrl in self.config_controls.items():
			if isinstance(ctrl, wx.CheckBox):
				config[key] = ctrl.GetValue()
			else:
				config[key] = ctrl.GetValue()
		
		# Test connection based on broker type
		try:
			if self.broker_name == 'MQTT':
				self._test_mqtt_connection(config)
			elif self.broker_name == 'Kafka':
				self._test_kafka_connection(config)
			elif self.broker_name == 'RabbitMQ':
				self._test_rabbitmq_connection(config)
			else:
				wx.MessageBox(
					_("Connection test not implemented for this broker"),
					_("Not Implemented"),
					wx.OK | wx.ICON_INFORMATION
				)
		except Exception as e:
			wx.MessageBox(
				f"{_('Connection failed')}:\n{str(e)}",
				_("Error"),
				wx.OK | wx.ICON_ERROR
			)

	def _test_mqtt_connection(self, config):
		""" Test MQTT broker connection
		"""
		try:
			import paho.mqtt.client as mqtt
			
			address = config.get('address', 'localhost')
			port = int(config.get('port', 1883))
			username = config.get('username', '') or None
			password = config.get('password', '') or None
			keepalive = int(config.get('keepalive', 60))
			
			# Try VERSION2 API first (paho-mqtt 2.x)
			try:
				client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="devsimpy-test")
			except (TypeError, AttributeError):
				try:
					client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="devsimpy-test")
				except (TypeError, AttributeError):
					client = mqtt.Client(client_id="devsimpy-test")
			
			if username:
				client.username_pw_set(username, password or "")
			
			client.connect(address, port, keepalive)
			client.loop_start()
			
			# Give it time to connect
			import time
			time.sleep(1)
			
			client.loop_stop()
			client.disconnect()
			
			wx.MessageBox(
				f"{_('Successfully connected to')} {address}:{port}",
				_("Connection Successful"),
				wx.OK | wx.ICON_INFORMATION
			)
		except ImportError:
			wx.MessageBox(
				_("paho-mqtt is not installed. Install with: pip install paho-mqtt"),
				_("Missing Library"),
				wx.OK | wx.ICON_ERROR
			)
		except Exception as e:
			raise

	def _test_kafka_connection(self, config):
		""" Test Kafka broker connection
		"""
		try:
			from confluent_kafka.admin import AdminClient
			
			bootstrap = config.get('bootstrap', 'localhost:9092')
			admin = AdminClient({'bootstrap.servers': bootstrap})
			admin.list_topics(timeout=5)
			
			wx.MessageBox(
				f"{_('Successfully connected to')} {bootstrap}",
				_("Connection Successful"),
				wx.OK | wx.ICON_INFORMATION
			)
		except ImportError:
			wx.MessageBox(
				_("confluent-kafka is not installed. Install with: pip install confluent-kafka"),
				_("Missing Library"),
				wx.OK | wx.ICON_ERROR
			)
		except Exception as e:
			raise

	def _test_rabbitmq_connection(self, config):
		""" Test RabbitMQ broker connection
		"""
		try:
			import pika
			
			host = config.get('host', 'localhost')
			port = int(config.get('port', 5672))
			username = config.get('username', 'guest')
			password = config.get('password', 'guest')
			
			credentials = pika.PlainCredentials(username, password)
			connection = pika.BlockingConnection(
				pika.ConnectionParameters(host=host, port=port, credentials=credentials)
			)
			connection.close()
			
			wx.MessageBox(
				f"{_('Successfully connected to')} {host}:{port}",
				_("Connection Successful"),
				wx.OK | wx.ICON_INFORMATION
			)
		except ImportError:
			wx.MessageBox(
				_("pika is not installed. Install with: pip install pika"),
				_("Missing Library"),
				wx.OK | wx.ICON_ERROR
			)
		except Exception as e:
			raise


class SimulationPanel(wx.Panel):
	""" Simulation Panel with modern UI
	"""

	def __init__(self, parent):
		""" Constructor.
		"""
		wx.Panel.__init__(self, parent)
		
		# Initialize paths
		self.sim_success_sound_path = SIMULATION_SUCCESS_SOUND_PATH
		self.sim_error_sound_path = SIMULATION_ERROR_SOUND_PATH
		self.default_devs_dir = DEFAULT_DEVS_DIRNAME
		self.sim_defaut_strategy = DEFAULT_SIM_STRATEGY
		self.sim_defaut_plot_dyn_freq = DEFAULT_PLOT_DYN_FREQ
		
		# Broker selection attributes - initialize from saved settings
		self._has_broker_selection = False
		self.cb_msg_format = None
		self.cb_broker = None
		self.msgFormatLabel = None
		self.brokerLabel = None
		self.brokerInfoBtn = None
		self.selected_message_format = getattr(builtins, 'SELECTED_MESSAGE_FORMAT', 'DEVSStreaming')
		self.selected_broker = getattr(builtins, 'SELECTED_BROKER', 'Kafka')
		
		self.InitUI()
	
	def _load_mqtt_config_from_file(self):
		""" Load MQTT configuration from .devsimpy file into builtins
		"""
		import configparser
		from Utilities import GetUserConfigDir
		
		try:
			config_file = os.path.join(GetUserConfigDir(), 'devsimpy')
			if os.path.exists(config_file):
				cfg = configparser.ConfigParser()
				cfg.read(config_file)
				
				section_name = 'BROKER_MQTT'
				if cfg.has_section(section_name):
					address = cfg.get(section_name, 'address', fallback='localhost')
					port = cfg.get(section_name, 'port', fallback='1883')
					username = cfg.get(section_name, 'username', fallback='')
					password = cfg.get(section_name, 'password', fallback='')
					
					setattr(builtins, 'MQTT_BROKER_ADDRESS', address)
					setattr(builtins, 'MQTT_BROKER_PORT', int(port))
					setattr(builtins, 'MQTT_USERNAME', username or None)
					setattr(builtins, 'MQTT_PASSWORD', password or None)
					
					# Only log at debug level, not info
					logger.debug(f"Loaded MQTT config from file: {address}:{port}, username={'(set)' if username else 'None'}")
		except Exception as e:
			logger.debug(f"Could not load MQTT config from file: {e}")
	
	def InitUI(self):
		""" Initialize the UI with modern layout
		"""
		
		# Main sizer
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# ============================================================
		# Section 1: DEVS Kernel
		# ============================================================
		devsBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('DEVS Kernel'))
		
		devsGrid = wx.FlexGridSizer(0, 3, 10, 10)  # 0 rows means auto-calculate
		devsGrid.AddGrowableCol(1, 1)
		
		# DEVS Package selection
		devsLabel = wx.StaticText(self, label=_("Package:"))
		devsLabel.SetToolTip(_("Select the DEVS kernel package (PyDEVS, PyPDEVS, etc.)"))
		self.cb3 = wx.ComboBox(self, wx.NewIdRef(), DEFAULT_DEVS_DIRNAME, 
							   choices=list(DEVS_DIR_PATH_DICT.keys()), 
							   style=wx.CB_READONLY)
		self.cb3.Bind(wx.EVT_COMBOBOX, self.onCb3)
		
		# Documentation button
		self.devs_doc_btn = wx.Button(self, wx.ID_HELP, _("Help"))
		self.devs_doc_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_HELP, wx.ART_BUTTON))
		self.devs_doc_btn.SetToolTip(_("View documentation for the selected DEVS package"))
		self.devs_doc_btn.Bind(wx.EVT_BUTTON, self.OnAbout)
		
		devsGrid.Add(devsLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		devsGrid.Add(self.cb3, 1, wx.EXPAND)
		devsGrid.Add(self.devs_doc_btn, 0, wx.ALIGN_CENTER_VERTICAL)
		
		# Strategy selection
		strategyLabel = wx.StaticText(self, label=_("Strategy:"))
		strategyLabel.SetToolTip(_("Select the default simulation strategy"))
		
		# Get strategies based on current DEVS package
		strategies = list(getattr(builtins, 
								  f'{self.cb3.GetValue().upper()}_SIM_STRATEGY_DICT').keys())
		self.cb4 = wx.ComboBox(self, wx.NewIdRef(), DEFAULT_SIM_STRATEGY, 
							   choices=strategies, style=wx.CB_READONLY)
		self.cb4.SetToolTip(_("Simulation algorithm strategy (see documentation for details)"))
		self.cb4.Bind(wx.EVT_COMBOBOX, self.onCb4)
		
		# Info button for strategy
		strategyInfoBtn = wx.Button(self, wx.NewIdRef(), _("Info"))
		strategyInfoBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_BUTTON))
		strategyInfoBtn.SetToolTip(_("Information about the selected strategy"))
		strategyInfoBtn.Bind(wx.EVT_BUTTON, self.OnStrategyInfo)
		
		devsGrid.Add(strategyLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		devsGrid.Add(self.cb4, 1, wx.EXPAND)
		devsGrid.Add(strategyInfoBtn, 0, wx.ALIGN_CENTER_VERTICAL)
		
		# Message Format and Broker selection (for BrokerDEVS with nested strategies)
		# Create broker UI elements (will be added to grid conditionally)
		self.msgFormatLabel = wx.StaticText(self, label=_("Message Format:"))
		self.msgFormatLabel.SetToolTip(_("Select the message standardization (DEVSStreaming, Custom, etc.)"))
		self.msgFormatLabel.Hide()  # Hidden by default
		
		self.cb_msg_format = wx.ComboBox(self, wx.NewIdRef(), "", choices=[], style=wx.CB_READONLY)
		self.cb_msg_format.SetToolTip(_("Message format for broker communication"))
		self.cb_msg_format.Bind(wx.EVT_COMBOBOX, self.onMessageFormatChange)
		self.cb_msg_format.Hide()  # Hidden by default
		
		# Broker selection
		self.brokerLabel = wx.StaticText(self, label=_("Broker:"))
		self.brokerLabel.SetToolTip(_("Select the message broker (Kafka, MQTT, etc.)"))
		self.brokerLabel.Hide()  # Hidden by default
		
		self.cb_broker = wx.ComboBox(self, wx.NewIdRef(), "", choices=[], style=wx.CB_READONLY)
		self.cb_broker.SetToolTip(_("Message broker for distributed simulation"))
		self.cb_broker.Bind(wx.EVT_COMBOBOX, self.onBrokerChange)
		self.cb_broker.Hide()  # Hidden by default
		
		# Broker info button
		self.brokerInfoBtn = wx.Button(self, wx.NewIdRef(), _("Config"))
		self.brokerInfoBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_CDROM, wx.ART_BUTTON))
		self.brokerInfoBtn.SetToolTip(_("Configure broker settings"))
		self.brokerInfoBtn.Bind(wx.EVT_BUTTON, self.OnBrokerConfig)
		self.brokerInfoBtn.Hide()  # Hidden by default
		
		# Store reference to the grid for dynamic updates
		self.devsGrid = devsGrid
		
		# Check if current strategy dict is nested (message format + broker)
		strategy_dict = getattr(builtins, 
							   f'{self.cb3.GetValue().upper()}_SIM_STRATEGY_DICT')
		self._has_broker_selection = isinstance(list(strategy_dict.values())[0] if strategy_dict else {}, dict)
		
		# Add broker UI to grid only if package supports it
		if self._has_broker_selection:
			self._populate_broker_ui_elements(strategy_dict)
			self._add_broker_rows_to_grid()
		
		devsBox.Add(devsGrid, 0, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(devsBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 2: Simulation Options
		# ============================================================
		optionsBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Simulation Options'))
		
		# No Time Limit checkbox
		self.cb2 = wx.CheckBox(self, wx.NewIdRef(), 
							   _('No Time Limit (stop when all models are idle)'))
		self.cb2.SetValue(NTL)
		self.cb2.SetToolTip(_("Simulation stops automatically when all models are idle"))
		optionsBox.Add(self.cb2, 0, wx.ALL, 5)
		
		# Plot refresh frequency
		plotSizer = wx.BoxSizer(wx.HORIZONTAL)
		plotLabel = wx.StaticText(self, label=_("Plot refresh frequency (ms):"))
		plotLabel.SetToolTip(_("Frequency for dynamic plot updates during simulation"))
		self.sc = wx.SpinCtrl(self, wx.NewIdRef(), 
							 str(self.sim_defaut_plot_dyn_freq),
							 min=10, max=10000)
		self.sc.Bind(wx.EVT_SPINCTRL, self.onSc)
		
		plotSizer.Add(plotLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
		plotSizer.Add(self.sc, 0)
		optionsBox.Add(plotSizer, 0, wx.ALL, 5)
		
		mainSizer.Add(optionsBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 3: Sound Notifications
		# ============================================================
		soundBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Sound Notifications'))
		
		# Enable notifications checkbox
		self.cb1 = wx.CheckBox(self, wx.NewIdRef(), _('Enable sound notifications'))
		self.cb1.SetValue(self.sim_success_sound_path != os.devnull)
		self.cb1.SetToolTip(_("Play sounds when simulation completes or encounters errors"))
		self.cb1.Bind(wx.EVT_CHECKBOX, self.onCb1Check)
		soundBox.Add(self.cb1, 0, wx.ALL, 5)
		
		# Sound selection grid
		soundGrid = wx.FlexGridSizer(2, 3, 10, 10)
		soundGrid.AddGrowableCol(1, 1)
		
		# Success sound
		successLabel = wx.StaticText(self, label=_("Success:"))
		self.sim_success_sound_btn = wx.Button(self, wx.NewIdRef(), 
											   os.path.basename(self.sim_success_sound_path),
											   name='success')
		self.sim_success_sound_btn.SetToolTip(_("Sound played when simulation completes successfully"))
		self.sim_success_sound_btn.Enable(self.sim_success_sound_path != os.devnull)
		self.sim_success_sound_btn.Bind(wx.EVT_BUTTON, self.OnSelectSound)
		
		successPlayBtn = wx.Button(self, wx.NewIdRef(), _("Play"))
		successPlayBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_BUTTON))
		successPlayBtn.SetToolTip(_("Preview this sound"))
		successPlayBtn.Bind(wx.EVT_BUTTON, lambda e: self.OnPlaySound('success'))
		
		soundGrid.Add(successLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		soundGrid.Add(self.sim_success_sound_btn, 1, wx.EXPAND)
		soundGrid.Add(successPlayBtn, 0)
		
		# Error sound
		errorLabel = wx.StaticText(self, label=_("Error:"))
		self.sim_error_sound_btn = wx.Button(self, wx.NewIdRef(),
											 os.path.basename(self.sim_error_sound_path),
											 name='error')
		self.sim_error_sound_btn.SetToolTip(_("Sound played when simulation encounters an error"))
		self.sim_error_sound_btn.Enable(self.sim_error_sound_path != os.devnull)
		self.sim_error_sound_btn.Bind(wx.EVT_BUTTON, self.OnSelectSound)
		
		errorPlayBtn = wx.Button(self, wx.NewIdRef(), _("Play"))
		errorPlayBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_BUTTON))
		errorPlayBtn.SetToolTip(_("Preview this sound"))
		errorPlayBtn.Bind(wx.EVT_BUTTON, lambda e: self.OnPlaySound('error'))
		
		soundGrid.Add(errorLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		soundGrid.Add(self.sim_error_sound_btn, 1, wx.EXPAND)
		soundGrid.Add(errorPlayBtn, 0)
		
		soundBox.Add(soundGrid, 0, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(soundBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# Add stretch spacer
		mainSizer.AddStretchSpacer(1)
		
		# Set sizer
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)

	def OnAbout(self, evt):
		""" Show documentation for selected DEVS package
		"""
		choice = self.cb3.GetValue()
		doc_path = os.path.join(
			os.path.dirname(getattr(builtins, 'DEVS_DIR_PATH_DICT').get(choice)), 
			'doc', 'index.html'
		)

		frame = HtmlFrame(self, f"{choice} Documentation", (800, 600))
		
		if os.path.exists(doc_path):
			frame.LoadFile(doc_path)
		else:
			html_content = f"""
			<html>
			<body>
			<h2>{choice} Documentation</h2>
			<p>Documentation directory not found at:</p>
			<p><code>{doc_path}</code></p>
			<p>Please check that the documentation is installed.</p>
			</body>
			</html>
			"""
			frame.SetPage(html_content)

		frame.Show()

	def OnStrategyInfo(self, evt):
		""" Show information about the selected strategy
		"""
		strategy = self.cb4.GetValue()
		devs_package = self.cb3.GetValue()
		
		strategy_dict = getattr(builtins, 
							   f'{devs_package.upper()}_SIM_STRATEGY_DICT')
		
		if strategy in strategy_dict:
			strategy_class = strategy_dict[strategy]
			
			# Handle nested strategy dicts (BrokerDEVS)
			if isinstance(strategy_class, dict):
				# For nested dicts, get the selected message format and broker
				msg_format = getattr(builtins, 'SELECTED_MESSAGE_FORMAT', 'DEVSStreaming')
				broker = getattr(builtins, 'SELECTED_BROKER', 'Kafka')
				
				if msg_format in strategy_class and broker in strategy_class[msg_format]:
					strategy_class = strategy_class[msg_format][broker]
				else:
					wx.MessageBox(
						_("Strategy configuration not found for selected message format and broker"),
						_("Strategy Information"),
						wx.OK | wx.ICON_WARNING
					)
					return
			
			doc = strategy_class.__doc__ or _("No documentation available")
			
			msg = f"{_('Strategy')}: {strategy}\n\n"
			msg += f"{_('Class')}: {strategy_class.__name__}\n\n"
			msg += f"{_('Description')}:\n{doc}"
			
			dlg = wx.MessageDialog(self, msg, 
								  _('Strategy Information'),
								  wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()

	def OnSelectSound(self, evt):
		""" Select a sound file
		"""
		dlg = wx.FileDialog(
			wx.GetTopLevelParent(self),
			_("Choose a sound file"),
			defaultDir=os.path.join(DEVSIMPY_PACKAGE_PATH, 'sounds'),
			wildcard=_("Sound files (*.mp3;*.wav)|*.mp3;*.wav|MP3 files (*.mp3)|*.mp3|WAV files (*.wav)|*.wav"),
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
		)

		if dlg.ShowModal() == wx.ID_OK:
			val = dlg.GetPath()
			btn = evt.GetEventObject()
			name = btn.GetName()
			
			try:
				# Update button label and path
				btn.SetLabel(os.path.basename(val))
				
				if name == 'success':
					self.sim_success_sound_path = val
				elif name == 'error':
					self.sim_error_sound_path = val
				
				# Auto-play the selected sound
				playSound(val)
				
			except Exception as e:
				wx.MessageBox(str(e), _("Error"), wx.OK | wx.ICON_ERROR)

		dlg.Destroy()

	def OnPlaySound(self, sound_type):
		""" Preview a sound
		"""
		try:
			if sound_type == 'success':
				path = self.sim_success_sound_path
			elif sound_type == 'error':
				path = self.sim_error_sound_path
			else:
				return
			
			if path and path != os.devnull and os.path.exists(path):
				playSound(path)
			else:
				wx.MessageBox(_("No sound file selected"), _("Info"), 
							wx.OK | wx.ICON_INFORMATION)
				
		except Exception as e:
			wx.MessageBox(str(e), _("Error"), wx.OK | wx.ICON_ERROR)

	def onCb1Check(self, evt):
		""" Enable/disable sound notifications
		"""
		enabled = evt.GetEventObject().GetValue()
		
		self.sim_success_sound_btn.Enable(enabled)
		self.sim_error_sound_btn.Enable(enabled)
		
		if enabled:
			self.sim_success_sound_path = SIMULATION_SUCCESS_SOUND_PATH
			self.sim_error_sound_path = SIMULATION_ERROR_SOUND_PATH
			self.sim_success_sound_btn.SetLabel(os.path.basename(self.sim_success_sound_path))
			self.sim_error_sound_btn.SetLabel(os.path.basename(self.sim_error_sound_path))
		else:
			self.sim_success_sound_path = os.devnull
			self.sim_error_sound_path = os.devnull

	def onCb4(self, evt):
		""" Strategy selection changed
		"""
		self.sim_defaut_strategy = evt.GetEventObject().GetValue()

	def onCb3(self, evt):
		""" DEVS package selection changed
		"""
		val = evt.GetEventObject().GetValue()

		# Update strategy list based on selected DEVS package  
		strategies = list(getattr(builtins, 
								 f'{val.upper()}_SIM_STRATEGY_DICT').keys())
		
		if strategies:
			self.cb4.Clear()
			self.cb4.Set(strategies)
			self.cb4.SetValue(strategies[0])

			# Update default values
			self.default_devs_dir = val
			self.sim_defaut_strategy = self.cb4.GetValue()
		
		# Check if new package has broker selection (nested strategy dict)
		strategy_dict = getattr(builtins, f'{val.upper()}_SIM_STRATEGY_DICT')
		has_broker_selection = isinstance(list(strategy_dict.values())[0] if strategy_dict else {}, dict)
		
		# Update broker UI based on package type
		if has_broker_selection and not self._has_broker_selection:
			# Transitioning TO BrokerDEVS - add rows
			self._populate_broker_ui_elements(strategy_dict)
			self._add_broker_rows_to_grid()
			self._has_broker_selection = True
		elif not has_broker_selection and self._has_broker_selection:
			# Transitioning FROM BrokerDEVS - remove rows
			self._remove_broker_rows_from_grid()
			self._has_broker_selection = False
		elif has_broker_selection and self._has_broker_selection:
			# Already in broker mode - just update options
			self._populate_broker_ui_elements(strategy_dict)
		
		# Force complete layout refresh
		self.devsGrid.Layout()
		self.Layout()
		self.GetParent().Layout()
		self.GetParent().Refresh()
		self.GetParent().Update()
	
	def _add_broker_rows_to_grid(self):
		""" Add broker UI rows to the grid
		"""
		# Show widgets before adding to grid
		self.msgFormatLabel.Show()
		self.cb_msg_format.Show()
		self.brokerLabel.Show()
		self.cb_broker.Show()
		self.brokerInfoBtn.Show()
		
		self.devsGrid.Add(self.msgFormatLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		self.devsGrid.Add(self.cb_msg_format, 1, wx.EXPAND)
		self.devsGrid.Add(wx.StaticText(self, label=""), 0)  # Empty cell for button column
		
		self.devsGrid.Add(self.brokerLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		self.devsGrid.Add(self.cb_broker, 1, wx.EXPAND)
		self.devsGrid.Add(self.brokerInfoBtn, 0, wx.ALIGN_CENTER_VERTICAL)
	
	def _remove_broker_rows_from_grid(self):
		""" Remove broker UI rows from the grid
		"""
		# Hide broker widgets
		self.msgFormatLabel.Hide()
		self.cb_msg_format.Hide()
		self.brokerLabel.Hide()
		self.cb_broker.Hide()
		self.brokerInfoBtn.Hide()
		
		# Remove broker rows by clearing and re-adding only non-broker items
		self.devsGrid.Clear(False)  # False to NOT delete child windows
		
		# Re-add non-broker rows
		devsLabel = wx.StaticText(self, label=_("Package:"))
		self.devsGrid.Add(devsLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		self.devsGrid.Add(self.cb3, 1, wx.EXPAND)
		self.devsGrid.Add(self.devs_doc_btn, 0, wx.ALIGN_CENTER_VERTICAL)
		
		strategyLabel = wx.StaticText(self, label=_("Strategy:"))
		self.devsGrid.Add(strategyLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		self.devsGrid.Add(self.cb4, 1, wx.EXPAND)
		
		# Strategy info button - need to recreate since we cleared
		strategyInfoBtn = wx.Button(self, wx.NewIdRef(), _("Info"))
		strategyInfoBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_BUTTON))
		strategyInfoBtn.SetToolTip(_("Information about the selected strategy"))
		strategyInfoBtn.Bind(wx.EVT_BUTTON, self.OnStrategyInfo)
		self.devsGrid.Add(strategyInfoBtn, 0, wx.ALIGN_CENTER_VERTICAL)
	

	
	def _init_broker_ui_elements(self):
		""" Initialize broker UI elements as None (created dynamically if needed)
		"""
		self.cb_msg_format = None
		self.cb_broker = None
		self.msgFormatLabel = None
		self.brokerLabel = None
		self.brokerInfoBtn = None
	
	def _populate_broker_ui_elements(self, strategy_dict):
		""" Populate broker UI elements with options from the strategy dict
		"""
		# Get message formats
		msg_formats = list(strategy_dict.keys())
		default_msg_format = self.selected_message_format if self.selected_message_format in msg_formats else (msg_formats[0] if msg_formats else "")
		
		# Update message format dropdown
		self.cb_msg_format.Clear()
		self.cb_msg_format.Set(msg_formats)
		if default_msg_format:
			self.cb_msg_format.SetValue(default_msg_format)
			self.selected_message_format = default_msg_format
		
		# Update broker list based on selected message format
		if msg_formats and default_msg_format in strategy_dict:
			brokers = list(strategy_dict[default_msg_format].keys())
			default_broker = self.selected_broker if self.selected_broker in brokers else (brokers[0] if brokers else "")
		else:
			brokers = []
			default_broker = ""
		
		self.cb_broker.Clear()
		self.cb_broker.Set(brokers)
		if default_broker:
			self.cb_broker.SetValue(default_broker)
			self.selected_broker = default_broker
	
	def onMessageFormatChange(self, evt):
		""" Message format selection changed
		"""
		msg_format = evt.GetEventObject().GetValue()
		self.selected_message_format = msg_format
		
		# Update global config
		builtins.SELECTED_MESSAGE_FORMAT = msg_format
		
		# Update broker list based on selected message format
		strategy_dict = getattr(builtins, 
							   f'{self.cb3.GetValue().upper()}_SIM_STRATEGY_DICT')
		
		if msg_format in strategy_dict and isinstance(strategy_dict[msg_format], dict):
			brokers = list(strategy_dict[msg_format].keys())
			if self.cb_broker:
				self.cb_broker.Clear()
				self.cb_broker.Set(brokers)
				if brokers:
					self.cb_broker.SetValue(brokers[0])
					self.selected_broker = brokers[0]
					builtins.SELECTED_BROKER = brokers[0]
	
	def onBrokerChange(self, evt):
		""" Broker selection changed
		"""
		broker = evt.GetEventObject().GetValue()
		self.selected_broker = broker
		
		# Update global config
		builtins.SELECTED_BROKER = broker
		
		# Load MQTT config if MQTT is selected
		if broker and broker.upper() == 'MQTT':
			self._load_mqtt_config_from_file()
	
	def OnBrokerConfig(self, evt):
		""" Open broker configuration dialog
		"""
		if not self.selected_broker:
			wx.MessageBox(_("Please select a broker first"), 
						 _("No Broker Selected"), wx.OK | wx.ICON_INFORMATION)
			return
		
		# Create configuration dialog based on selected broker
		dlg = BrokerConfigDialog(self, self.selected_broker)
		dlg.ShowModal()
		dlg.Destroy()

	def onSc(self, evt):
		""" Plot frequency changed
		"""
		self.sim_defaut_plot_dyn_freq = evt.GetEventObject().GetValue()

	def OnApply(self, evt):
		""" Apply all changes
		"""
		changes = []
		
		# Check if DEVS kernel changed
		if DEFAULT_DEVS_DIRNAME != self.default_devs_dir:
			# Change builtin before recompiling modules
			setattr(builtins, 'DEFAULT_DEVS_DIRNAME', self.default_devs_dir)

			try:
				# Recompile core modules
				ReloadModule.recompile("DomainInterface.DomainBehavior")
				ReloadModule.recompile("DomainInterface.DomainStructure")
				ReloadModule.recompile("DomainInterface.MasterModel")

				# Update library tree
				mainW = getTopLevelWindow()
				nb1 = mainW.GetControlNotebook()
				tree = nb1.GetTree()
				tree.UpdateAll()
				
				changes.append(_("DEVS kernel package"))
				
			except Exception as e:
				wx.LogError(f"Error reloading modules: {str(e)}")

		# Enable/disable priority icon based on DEVS kernel
		try:
			mainW = getTopLevelWindow()
			tb = mainW.GetToolBar()
			tb.EnableTool(Menu.ID_PRIORITY_DIAGRAM, 
						 'PyPDEVS' not in self.default_devs_dir)
		except:
			pass

		# Update all settings
		old_sound_success = getattr(builtins, 'SIMULATION_SUCCESS_SOUND_PATH')
		old_sound_error = getattr(builtins, 'SIMULATION_ERROR_SOUND_PATH')
		old_strategy = getattr(builtins, 'DEFAULT_SIM_STRATEGY')
		old_freq = getattr(builtins, 'DEFAULT_PLOT_DYN_FREQ')
		old_ntl = getattr(builtins, 'NTL')
		old_msg_format = getattr(builtins, 'SELECTED_MESSAGE_FORMAT', 'DEVSStreaming')
		old_broker = getattr(builtins, 'SELECTED_BROKER', 'Kafka')
		
		# Apply changes
		setattr(builtins, 'SIMULATION_SUCCESS_SOUND_PATH', self.sim_success_sound_path)
		setattr(builtins, 'SIMULATION_ERROR_SOUND_PATH', self.sim_error_sound_path)
		setattr(builtins, 'DEFAULT_SIM_STRATEGY', self.sim_defaut_strategy)
		setattr(builtins, 'DEFAULT_DEVS_DIRNAME', self.default_devs_dir)
		setattr(builtins, 'DEFAULT_PLOT_DYN_FREQ', self.sim_defaut_plot_dyn_freq)
		setattr(builtins, 'NTL', self.cb2.GetValue())
		
		# Save broker and message format settings if BrokerDEVS is selected
		if self._has_broker_selection and self.cb_msg_format and self.cb_broker:
			setattr(builtins, 'SELECTED_MESSAGE_FORMAT', self.cb_msg_format.GetValue())
			setattr(builtins, 'SELECTED_BROKER', self.cb_broker.GetValue())
			if old_msg_format != self.cb_msg_format.GetValue():
				changes.append(_("Message format"))
			if old_broker != self.cb_broker.GetValue():
				changes.append(_("Broker"))
		
		# Track changes
		if old_sound_success != self.sim_success_sound_path:
			changes.append(_("Success sound"))
		if old_sound_error != self.sim_error_sound_path:
			changes.append(_("Error sound"))
		if old_strategy != self.sim_defaut_strategy:
			changes.append(_("Simulation strategy"))
		if old_freq != self.sim_defaut_plot_dyn_freq:
			changes.append(_("Plot refresh frequency"))
		if old_ntl != self.cb2.GetValue():
			changes.append(_("No Time Limit option"))
		
		# Show summary
		if changes:
			msg = _("The following simulation settings have been updated:\n\n")
			msg += "\n".join(f"• {c}" for c in changes)
			
			dlg = wx.MessageDialog(self, msg, _('Settings Updated'),
								  wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()


class EditorPanel(wx.Panel):
	""" Editor preferences panel with modern UI
	"""

	EDITORS = {
		'spyder': {
			'name': 'Spyder',
			'description': _('Scientific Python Development Environment'),
			'url': 'https://www.spyder-ide.org/'
		},
		'pyzo': {
			'name': 'Pyzo',
			'description': _('Python IDE for scientific computing'),
			'url': 'https://pyzo.org/'
		}
	}

	def __init__(self, parent):
		""" Constructor.
		"""
		wx.Panel.__init__(self, parent)
		self.parent = parent
		self.InitUI()
	
	def InitUI(self):
		""" Initialize the UI with modern layout
		"""
		
		# Main sizer
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# ============================================================
		# Section 1: Editor Selection
		# ============================================================
		editorBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Code Editor'))
		
		# Local editor checkbox
		self.cb = wx.CheckBox(self, wx.NewIdRef(), 
							 _('Use DEVSimPy built-in code editor'))
		self.cb.SetValue(LOCAL_EDITOR)
		self.cb.SetToolTip(
			_("Use the integrated editor for Python files.\n"
			  "Note: Code modification during simulation is disabled with this option."))
		self.cb.Bind(wx.EVT_CHECKBOX, self.OnCheck)
		editorBox.Add(self.cb, 0, wx.ALL, 5)
		
		# Separator
		editorBox.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
		
		# External editor section
		externalLabel = wx.StaticText(self, label=_('External Editor'))
		font = externalLabel.GetFont()
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		externalLabel.SetFont(font)
		editorBox.Add(externalLabel, 0, wx.ALL, 5)
		
		# External editor selection grid
		externalGrid = wx.FlexGridSizer(2, 3, 10, 10)
		externalGrid.AddGrowableCol(1, 1)
		
		# Choice label and control
		choiceLabel = wx.StaticText(self, label=_("Select editor:"))
		
		# Populate choices based on installed editors
		choices = []
		self.editor_status = {}
		
		for editor_key, editor_info in EditorPanel.EDITORS.items():
			is_installed = importlib.util.find_spec(editor_key) is not None
			self.editor_status[editor_key] = is_installed
			
			if is_installed:
				choices.append(editor_info['name'])
		
		self.choice = wx.Choice(self, wx.NewIdRef(), choices=choices)
		
		# Set selection based on config
		if EXTERNAL_EDITOR_NAME == "" or not choices:
			self.choice.SetSelection(0 if choices else wx.NOT_FOUND)
		else:
			# Find the editor in EDITORS dict
			for idx, (key, info) in enumerate(EditorPanel.EDITORS.items()):
				if key == EXTERNAL_EDITOR_NAME or info['name'] == EXTERNAL_EDITOR_NAME:
					if idx < len(choices):
						self.choice.SetSelection(idx)
					break
		
		self.choice.Enable(not self.cb.IsChecked())
		
		# Info button
		infoBtn = wx.Button(self, wx.NewIdRef(), _("Info"))
		infoBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_BUTTON))
		infoBtn.SetToolTip(_("Information about the selected editor"))
		infoBtn.Bind(wx.EVT_BUTTON, self.OnEditorInfo)
		
		externalGrid.Add(choiceLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		externalGrid.Add(self.choice, 1, wx.EXPAND)
		externalGrid.Add(infoBtn, 0, wx.ALIGN_CENTER_VERTICAL)
		
		# Update and install buttons
		updateBtn = wx.Button(self, wx.ID_REFRESH, _("Refresh"))
		updateBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_BUTTON))
		updateBtn.SetToolTip(_("Refresh the list of installed editors"))
		updateBtn.Bind(wx.EVT_BUTTON, self.OnRefreshEditors)
		
		installBtn = wx.Button(self, wx.NewIdRef(), _("Install"))
		installBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_BUTTON))
		installBtn.SetToolTip(_("Install additional code editors"))
		installBtn.Bind(wx.EVT_BUTTON, self.OnInstallEditor)
		
		externalGrid.Add(wx.StaticText(self, label=""), 0)  # Spacer
		
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer.Add(updateBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(installBtn, 0)
		externalGrid.Add(btnSizer, 0)
		
		editorBox.Add(externalGrid, 0, wx.EXPAND|wx.ALL, 5)
		
		mainSizer.Add(editorBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 2: Installed Editors
		# ============================================================
		installedBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Installed Editors'))
		
		# List of installed editors
		self.editorList = wx.ListCtrl(self, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
		self.editorList.InsertColumn(0, _('Editor'), width=150)
		self.editorList.InsertColumn(1, _('Status'), width=100)
		self.editorList.InsertColumn(2, _('Description'), width=300)
		
		self.UpdateEditorList()
		
		installedBox.Add(self.editorList, 1, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(installedBox, 1, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 3: Information
		# ============================================================
		infoBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Information'))
		
		infoText = wx.StaticText(self, label=
			_("• Built-in editor: Simple integrated editor for quick edits\n"
			  "• External editors: Professional IDEs with advanced features\n"
			  "• Spyder: Ideal for scientific computing and data analysis\n"
			  "• Pyzo: Lightweight IDE with interactive shell"))
		
		infoBox.Add(infoText, 0, wx.ALL, 5)
		mainSizer.Add(infoBox, 0, wx.EXPAND|wx.ALL, 10)
		
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)

	def UpdateEditorList(self):
		"""Update the list of installed editors"""
		self.editorList.DeleteAllItems()
		
		for idx, (editor_key, editor_info) in enumerate(EditorPanel.EDITORS.items()):
			is_installed = importlib.util.find_spec(editor_key) is not None
			
			self.editorList.InsertItem(idx, editor_info['name'])
			self.editorList.SetItem(idx, 1, 
								   _('Installed') if is_installed else _('Not installed'))
			self.editorList.SetItem(idx, 2, editor_info['description'])
			
			# Color code the status
			if is_installed:
				self.editorList.SetItemTextColour(idx, wx.Colour(0, 128, 0))
			else:
				self.editorList.SetItemTextColour(idx, wx.Colour(128, 128, 128))

	def OnEditorInfo(self, event):
		"""Show information about selected editor"""
		selection = self.choice.GetSelection()
		
		if selection == wx.NOT_FOUND:
			wx.MessageBox(_("No editor selected"), _("Info"), 
						 wx.OK | wx.ICON_INFORMATION)
			return
		
		editor_name = self.choice.GetString(selection)
		
		# Find editor info
		for key, info in EditorPanel.EDITORS.items():
			if info['name'] == editor_name:
				msg = f"{_('Editor')}: {info['name']}\n\n"
				msg += f"{_('Description')}: {info['description']}\n\n"
				msg += f"{_('Website')}: {info['url']}\n\n"
				msg += f"{_('Status')}: "
				msg += _("Installed") if self.editor_status.get(key, False) else _("Not installed")
				
				dlg = wx.MessageDialog(self, msg, _('Editor Information'),
									  wx.OK | wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
				break

	def OnRefreshEditors(self, event):
		"""Refresh the list of available editors"""
		old_count = self.choice.GetCount()
		
		# Re-scan for installed editors
		choices = []
		self.editor_status = {}
		
		for editor_key, editor_info in EditorPanel.EDITORS.items():
			is_installed = importlib.util.find_spec(editor_key) is not None
			self.editor_status[editor_key] = is_installed
			
			if is_installed:
				choices.append(editor_info['name'])
		
		# Update choice control
		current_selection = self.choice.GetStringSelection()
		self.choice.Clear()
		self.choice.AppendItems(choices)
		
		# Restore selection if possible
		if current_selection:
			idx = self.choice.FindString(current_selection)
			if idx != wx.NOT_FOUND:
				self.choice.SetSelection(idx)
			else:
				self.choice.SetSelection(0 if choices else wx.NOT_FOUND)
		
		# Update list
		self.UpdateEditorList()
		
		new_count = self.choice.GetCount()
		
		if new_count > old_count:
			msg = _("Found {} new editor(s)!").format(new_count - old_count)
			icon = wx.ICON_INFORMATION
		elif new_count == old_count:
			msg = _("No new editors found.")
			icon = wx.ICON_INFORMATION
		else:
			msg = _("Editor list updated.")
			icon = wx.ICON_INFORMATION
		
		wx.MessageBox(msg, _("Refresh Complete"), wx.OK | icon)

	def OnInstallEditor(self, event):
		"""Show dialog to install editors"""
		# Get list of non-installed editors
		not_installed = []
		for key, info in EditorPanel.EDITORS.items():
			if not self.editor_status.get(key, False):
				not_installed.append(info['name'])
		
		if not not_installed:
			wx.MessageBox(_("All supported editors are already installed!"),
						 _("Info"), wx.OK | wx.ICON_INFORMATION)
			return
		
		dlg = wx.SingleChoiceDialog(
			self,
			_("Select an editor to install:"),
			_("Install Editor"),
			not_installed
		)
		
		if dlg.ShowModal() == wx.ID_OK:
			selected = dlg.GetStringSelection()
			
			# Find the key for this editor
			editor_key = None
			for key, info in EditorPanel.EDITORS.items():
				if info['name'] == selected:
					editor_key = key
					break
			
			if editor_key:
				# Show progress
				wx.BeginBusyCursor()
				
				try:
					success = BuzyCursorNotification(install(editor_key))
					wx.EndBusyCursor()
					
					if success:
						msg = _("Installation successful!\n\n"
							   "Please restart DEVSimPy to use {}.").format(selected)
						icon = wx.ICON_INFORMATION
					else:
						msg = _("Installation failed.\n\n"
							   "Please install {} manually using pip.").format(selected)
						icon = wx.ICON_ERROR
					
				except Exception as e:
					wx.EndBusyCursor()
					msg = _("Error during installation:\n{}").format(str(e))
					icon = wx.ICON_ERROR
				
				wx.MessageBox(msg, _("Installation"), wx.OK | icon)
				
				# Refresh the list
				self.OnRefreshEditors(None)
		
		dlg.Destroy()

	def OnCheck(self, event):
		"""Handle local editor checkbox"""
		self.choice.Enable(not self.cb.IsChecked())
		
	def OnApply(self, evt):
		"""Apply changes"""
		old_local = getattr(builtins, 'LOCAL_EDITOR')
		old_external = getattr(builtins, 'EXTERNAL_EDITOR_NAME')
		
		new_local = self.cb.IsChecked()
		
		# Get external editor key (not display name)
		new_external = ""
		if self.choice.IsEnabled() and self.choice.GetSelection() != wx.NOT_FOUND:
			selected_name = self.choice.GetString(self.choice.GetSelection())
			# Find the key for this name
			for key, info in EditorPanel.EDITORS.items():
				if info['name'] == selected_name:
					new_external = key
					break
		
		# Apply changes
		setattr(builtins, 'LOCAL_EDITOR', new_local)
		setattr(builtins, 'EXTERNAL_EDITOR_NAME', new_external)
		
		# Show summary
		changes = []
		if old_local != new_local:
			changes.append(_("Editor mode: {}").format(
				_("Built-in") if new_local else _("External")))
		
		if old_external != new_external and not new_local:
			editor_name = EditorPanel.EDITORS.get(new_external, {}).get('name', new_external)
			changes.append(_("External editor: {}").format(editor_name))
		
		if changes:
			msg = _("The following editor settings have been updated:\n\n")
			msg += "\n".join(f"• {c}" for c in changes)
			
			dlg = wx.MessageDialog(self, msg, _('Settings Updated'),
								  wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()


class AIPanel(wx.Panel):
	""" AI Integration Panel with modern UI
	"""

	AI_PROVIDERS = {
		'': {
			'name': _('None'),
			'description': _('No AI assistant selected'),
			'url': '',
			'icon': wx.ART_MISSING_IMAGE
		},
		'ChatGPT': {
			'name': 'ChatGPT',
			'description': _('OpenAI GPT-4 powered code generation'),
			'url': 'https://openai.com/research/chatgpt',
			'icon': wx.ART_TIP,
			'requires': ['API Key']
		},
		'Ollama': {
			'name': 'Ollama',
			'description': _('Local LLM running on your machine'),
			'url': 'https://ollama.com/',
			'icon': wx.ART_HARDDISK,
			'requires': ['Server Port']
		}
	}

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		# Load saved settings
		self.load_settings()
		self.InitUI()

	def InitUI(self):
		""" Initialize interface with modern layout
		"""
		
		# Main sizer
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# ============================================================
		# Section 1: AI Provider Selection
		# ============================================================
		providerBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('AI Provider'))
		
		# Provider selection grid
		providerGrid = wx.FlexGridSizer(1, 3, 10, 10)
		providerGrid.AddGrowableCol(1, 1)
		
		providerLabel = wx.StaticText(self, label=_("Select AI:"))
		
		self.choice_ia = wx.ComboBox(
			self, wx.NewIdRef(),
			value=getattr(builtins, 'SELECTED_IA', ''),
			choices=[info['name'] for info in AIPanel.AI_PROVIDERS.values()],
			style=wx.CB_READONLY
		)
		self.choice_ia.SetToolTip(_("Select an AI provider for code generation"))
		self.choice_ia.Bind(wx.EVT_COMBOBOX, self.OnAISelection)
		
		# Info button
		self.ai_info_button = wx.Button(self, wx.NewIdRef(), _("Info"))
		self.ai_info_button.SetBitmap(
			wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_BUTTON))
		self.ai_info_button.SetToolTip(_("More about the selected AI provider"))
		self.ai_info_button.Bind(wx.EVT_BUTTON, self.OnInfoButtonClick)
		
		providerGrid.Add(providerLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		providerGrid.Add(self.choice_ia, 1, wx.EXPAND)
		providerGrid.Add(self.ai_info_button, 0, wx.ALIGN_CENTER_VERTICAL)
		
		providerBox.Add(providerGrid, 0, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(providerBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 2: Provider Configuration
		# ============================================================
		self.configBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Configuration'))
		
		# ChatGPT Configuration
		self.chatgpt_panel = wx.Panel(self)
		chatgpt_sizer = wx.BoxSizer(wx.VERTICAL)
		
		# API Key
		apiGrid = wx.FlexGridSizer(1, 2, 10, 10)
		apiGrid.AddGrowableCol(1, 1)
		
		apiLabel = wx.StaticText(self.chatgpt_panel, label=_("API Key:"))
		self.api_key_ctrl = wx.TextCtrl(self.chatgpt_panel, style=wx.TE_PASSWORD)
		self.api_key_ctrl.SetValue(
			getattr(builtins, 'PARAMS_IA', {}).get('CHATGPT_API_KEY', ''))
		self.api_key_ctrl.SetToolTip(_("Your OpenAI API key"))
		
		apiGrid.Add(apiLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		apiGrid.Add(self.api_key_ctrl, 1, wx.EXPAND)
		
		chatgpt_sizer.Add(apiGrid, 0, wx.EXPAND|wx.ALL, 5)
		
		# Get API Key button
		getKeyBtn = wx.Button(self.chatgpt_panel, wx.NewIdRef(), _("Get API Key"))
		getKeyBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_BUTTON))
		getKeyBtn.SetToolTip(_("Open OpenAI website to get your API key"))
		getKeyBtn.Bind(wx.EVT_BUTTON, 
					  lambda e: wx.LaunchDefaultBrowser('https://platform.openai.com/api-keys'))
		chatgpt_sizer.Add(getKeyBtn, 0, wx.ALL, 5)
		
		self.chatgpt_panel.SetSizer(chatgpt_sizer)
		self.configBox.Add(self.chatgpt_panel, 0, wx.EXPAND|wx.ALL, 5)
		
		# Ollama Configuration
		self.ollama_panel = wx.Panel(self)
		ollama_sizer = wx.BoxSizer(wx.VERTICAL)
		
		# Server Port
		portGrid = wx.FlexGridSizer(2, 2, 10, 10)
		portGrid.AddGrowableCol(1, 1)
		
		portLabel = wx.StaticText(self.ollama_panel, label=_("Server Port:"))
		self.port_ctrl = wx.SpinCtrl(self.ollama_panel, 
									 value='11434',
									 min=1024, max=65535)
		self.port_ctrl.SetValue(
			int(getattr(builtins, 'PARAMS_IA', {}).get('OLLAMA_PORT', '11434')))
		self.port_ctrl.SetToolTip(_("Port where Ollama server is running"))
		
		portGrid.Add(portLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		portGrid.Add(self.port_ctrl, 1, wx.EXPAND)
		
		# Server Host
		hostLabel = wx.StaticText(self.ollama_panel, label=_("Server Host:"))
		self.host_ctrl = wx.TextCtrl(self.ollama_panel)
		self.host_ctrl.SetValue(
			getattr(builtins, 'PARAMS_IA', {}).get('OLLAMA_HOST', 'localhost'))
		self.host_ctrl.SetToolTip(_("Host where Ollama server is running"))
		
		portGrid.Add(hostLabel, 0, wx.ALIGN_CENTER_VERTICAL)
		portGrid.Add(self.host_ctrl, 1, wx.EXPAND)
		
		ollama_sizer.Add(portGrid, 0, wx.EXPAND|wx.ALL, 5)
		
		# Install Ollama button
		installBtn = wx.Button(self.ollama_panel, wx.NewIdRef(), _("Install Ollama"))
		installBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_BUTTON))
		installBtn.SetToolTip(_("Download and install Ollama"))
		installBtn.Bind(wx.EVT_BUTTON, 
					   lambda e: wx.LaunchDefaultBrowser('https://ollama.com/download'))
		ollama_sizer.Add(installBtn, 0, wx.ALL, 5)
		
		self.ollama_panel.SetSizer(ollama_sizer)
		self.configBox.Add(self.ollama_panel, 0, wx.EXPAND|wx.ALL, 5)
		
		mainSizer.Add(self.configBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 3: Status and Testing
		# ============================================================
		statusBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Status'))
		
		# Status indicator
		statusGrid = wx.FlexGridSizer(2, 2, 10, 10)
		statusGrid.AddGrowableCol(1, 1)
		
		statusLabelText = wx.StaticText(self, label=_("Connection:"))
		self.status_indicator = wx.StaticText(self, label=_("Not tested"))
		self.status_indicator.SetForegroundColour(wx.Colour(128, 128, 128))
		
		statusGrid.Add(statusLabelText, 0, wx.ALIGN_CENTER_VERTICAL)
		statusGrid.Add(self.status_indicator, 0, wx.ALIGN_CENTER_VERTICAL)
		
		# Test button
		self.ai_check_button = wx.Button(self, wx.NewIdRef(), _("Test Connection"))
		self.ai_check_button.SetBitmap(
			wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_BUTTON))
		self.ai_check_button.SetToolTip(_("Test if the AI provider is ready"))
		self.ai_check_button.Bind(wx.EVT_BUTTON, self.OnAICheck)
		
		statusGrid.Add(wx.StaticText(self, label=""), 0)
		statusGrid.Add(self.ai_check_button, 0, wx.ALIGN_LEFT)
		
		statusBox.Add(statusGrid, 0, wx.EXPAND|wx.ALL, 5)
		mainSizer.Add(statusBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# ============================================================
		# Section 4: Information
		# ============================================================
		infoBox = wx.StaticBoxSizer(wx.VERTICAL, self, _('Information'))
		
		self.info_text = wx.StaticText(self, label="")
		self.info_text.Wrap(500)
		infoBox.Add(self.info_text, 0, wx.ALL, 5)
		
		mainSizer.Add(infoBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# Add stretch spacer
		mainSizer.AddStretchSpacer(1)
		
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)
		
		# Initialize visibility and info
		self.selected_ia = self.choice_ia.GetValue()
		self.UpdateFieldsVisibility()
		self.UpdateInfoText()

	def UpdateFieldsVisibility(self):
		""" Update UI based on selected AI provider
		"""
		selected_name = self.choice_ia.GetValue()
		
		# Find the key for selected provider
		selected_key = ''
		for key, info in AIPanel.AI_PROVIDERS.items():
			if info['name'] == selected_name:
				selected_key = key
				break
		
		# Show/hide configuration panels
		self.chatgpt_panel.Show(selected_key == 'ChatGPT')
		self.ollama_panel.Show(selected_key == 'Ollama')
		
		# Show/hide buttons
		has_selection = bool(selected_key)
		self.ai_info_button.Show(has_selection and selected_key != '')
		self.ai_check_button.Show(has_selection and selected_key != '')
		
		# Show/hide config box
		self.configBox.GetStaticBox().Show(has_selection and selected_key != '')
		
		self.Layout()

	def UpdateInfoText(self):
		""" Update the information text based on selected AI
		"""
		selected_name = self.choice_ia.GetValue()
		
		for key, info in AIPanel.AI_PROVIDERS.items():
			if info['name'] == selected_name:
				if key:
					text = f"{info['description']}\n\n"
					if 'requires' in info:
						text += _("Required: ") + ", ".join(info['requires'])
					self.info_text.SetLabel(text)
				else:
					self.info_text.SetLabel(
						_("Select an AI provider to enable code generation assistance."))
				break
		
		self.info_text.Wrap(500)

	def OnAICheck(self, event):
		""" Test the AI connection
		"""
		self.SaveAISettings()
		
		self.status_indicator.SetLabel(_("Testing..."))
		self.status_indicator.SetForegroundColour(wx.Colour(255, 165, 0))
		self.Layout()
		wx.SafeYield()
		
		try:
			# Test connection via adapter
			adapter = AdapterFactory.get_adapter_instance(None, params=PARAMS_IA)
			
			if adapter:
				self.status_indicator.SetLabel(_("Connected"))
				self.status_indicator.SetForegroundColour(wx.Colour(0, 128, 0))
				
				wx.MessageBox(
					_(f"{self.selected_ia} is ready for code generation!"),
					_("Connection Successful"),
					wx.OK | wx.ICON_INFORMATION
				)
			else:
				raise Exception(_("Failed to create adapter"))
				
		except Exception as e:
			self.status_indicator.SetLabel(_("Failed"))
			self.status_indicator.SetForegroundColour(wx.Colour(255, 0, 0))
			
			wx.MessageBox(
				_(f"Connection failed:\n{str(e)}"),
				_("Connection Error"),
				wx.OK | wx.ICON_ERROR
			)
		
		self.Layout()

	def OnInfoButtonClick(self, event):
		""" Open information about selected AI provider
		"""
		selected_name = self.choice_ia.GetValue()
		
		for key, info in AIPanel.AI_PROVIDERS.items():
			if info['name'] == selected_name and info['url']:
				wx.LaunchDefaultBrowser(info['url'])
				break

	def OnAISelection(self, event):
		""" Handle AI provider selection change
		"""
		selected_name = self.choice_ia.GetValue()
		
		# Find the key
		for key, info in AIPanel.AI_PROVIDERS.items():
			if info['name'] == selected_name:
				self.selected_ia = key
				setattr(builtins, 'SELECTED_IA', key)
				break
		
		# Reset status
		self.status_indicator.SetLabel(_("Not tested"))
		self.status_indicator.SetForegroundColour(wx.Colour(128, 128, 128))
		
		self.UpdateFieldsVisibility()
		self.UpdateInfoText()

	def load_settings(self):
		""" Load AI settings from builtins
		"""
		# Initialize builtins with AI info
		setattr(builtins, "SELECTED_IA", getattr(builtins, "SELECTED_IA", ""))
		setattr(builtins, "PARAMS_IA", getattr(builtins, "PARAMS_IA", {}))
		
		# Default parameters
		builtins.PARAMS_IA.setdefault('CHATGPT_API_KEY', '')
		builtins.PARAMS_IA.setdefault('OLLAMA_PORT', '11434')
		builtins.PARAMS_IA.setdefault('OLLAMA_HOST', 'localhost')

	def OnApply(self, evt):
		""" Apply and save current AI settings
		"""
		old_ia = getattr(builtins, "SELECTED_IA", "")
		self.SaveAISettings()
		new_ia = getattr(builtins, "SELECTED_IA", "")
		
		changes = []
		
		if old_ia != new_ia:
			provider_name = AIPanel.AI_PROVIDERS.get(new_ia, {}).get('name', _('None'))
			changes.append(_("AI Provider: {}").format(provider_name))
		
		# Check configuration changes
		if new_ia == "ChatGPT":
			changes.append(_("ChatGPT API Key updated"))
		elif new_ia == "Ollama":
			changes.append(_("Ollama configuration updated"))
		
		if changes:
			msg = _("The following AI settings have been updated:\n\n")
			msg += "\n".join(f"• {c}" for c in changes)
			
			dlg = wx.MessageDialog(self, msg, _('Settings Updated'),
								  wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()

	def SaveAISettings(self):
		""" Save AI settings to builtins
		"""
		selected_name = self.choice_ia.GetValue()
		
		# Find key from name
		selected_key = ''
		for key, info in AIPanel.AI_PROVIDERS.items():
			if info['name'] == selected_name:
				selected_key = key
				break
		
		# Update selected AI
		if getattr(builtins, "SELECTED_IA", "") != selected_key:
			setattr(builtins, "SELECTED_IA", selected_key)
		
		# Update provider-specific settings
		if selected_key == "ChatGPT":
			new_api_key = self.api_key_ctrl.GetValue()
			if getattr(builtins, 'PARAMS_IA').get('CHATGPT_API_KEY') != new_api_key:
				builtins.PARAMS_IA['CHATGPT_API_KEY'] = new_api_key
				
		elif selected_key == "Ollama":
			new_port = str(self.port_ctrl.GetValue())
			new_host = self.host_ctrl.GetValue()
			
			if getattr(builtins, 'PARAMS_IA').get('OLLAMA_PORT') != new_port:
				builtins.PARAMS_IA['OLLAMA_PORT'] = new_port
			
			if getattr(builtins, 'PARAMS_IA').get('OLLAMA_HOST') != new_host:
				builtins.PARAMS_IA['OLLAMA_HOST'] = new_host


########################################################################
class Preferences(wx.Toolbook):
	""" Based Toolbook Preference class with auto-sizing
	"""

	def __init__(self, parent):
		"""Constructor."""
		wx.Toolbook.__init__(self, parent, wx.NewIdRef(), style=wx.BK_DEFAULT)
		self.InitUI()
	
	def InitUI(self):
		""" Init the UI.
		"""
		### don't try to translate this labels with _() because there are used to find png
		L = [('General',"(self)"),('Simulation',"(self)"), ('Editor',"(self)"), ('AI',"(self)"), ('Plugins',"(self)")]

		# make an image list using the LBXX images
		il = wx.ImageList(25, 25)
		for img in [load_and_resize_image("%s_pref.png"%a[0], 25, 25) for a in L]:
			il.Add(img)
		self.AssignImageList(il)

		imageIdGenerator = iter(range(il.GetImageCount()))

		for p, label in [("%sPanel%s"%(s,str(args)), _(s)) for s,args in L]:
			page = eval(p)
			self.AddPage(page, label, imageId=next(imageIdGenerator))

		### Plug-in page setting (populate is done when page is changed)
		self.pluginPanel = self.GetPage(self.GetPageCount()-1)

		self.CheckList = GeneralPluginsList(self.pluginPanel.GetRightPanel(), 
										   style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SORT_ASCENDING)
		### populate checklist with file in plug-ins directory
		wx.CallAfter(self.CheckList.Populate, (list(os.walk(PLUGINS_PATH))))

		self.pluginPanel.SetPluginsList(self.CheckList)

		lpanel = self.pluginPanel.GetLeftPanel()

		### Buttons for insert or delete plug-ins
		self.addBtn = wx.Button(lpanel, wx.ID_ADD, size=(140, -1))
		self.delBtn = wx.Button(lpanel, wx.ID_DELETE, size=(140, -1))
		self.refBtn = wx.Button(lpanel, wx.ID_REFRESH, size=(140, -1))
	
		self.addBtn.SetToolTip(_("Add new plug-ins"))
		self.delBtn.SetToolTip(_("Delete all existing plug-ins"))
		self.refBtn.SetToolTip(_("Refresh plug-ins list"))

		### add widget to plug-in panel
		self.pluginPanel.AddWidget(3, self.addBtn)
		self.pluginPanel.AddWidget(4, self.delBtn)
		self.pluginPanel.AddWidget(5, self.refBtn)

		### Binding
		self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGING, self.OnPageChanging)
		self.Bind(wx.EVT_BUTTON, self.OnAdd, id=self.addBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDelete, id=self.delBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnRefresh, id=self.refBtn.GetId())

	def OnPageChanged(self, event):
		""" Page has been changed - auto resize window
		"""
		# Let the event propagate first
		event.Skip()
		
		# Use CallAfter to ensure the page is fully displayed before calculating size
		wx.CallAfter(self.ResizeForTab)

	def ResizeForTab(self):
		""" Resize window to fit current tab
		"""
		try:
			parent = self.GetTopLevelParent()
			if not parent:
				return
			
			current_idx = self.GetSelection()
			if current_idx == wx.NOT_FOUND:
				return
			
			tab_sizes = {
				0: (750, 680),  # General
				1: (750, 700),  # Simulation
				2: (750, 680),  # Editor
				3: (750, 650),  # AI
				4: (800, 600),  # Plugins
			}
			
			optimal_width, optimal_height = tab_sizes.get(current_idx, (750, 600))
			
			# Always update minimum size
			parent.SetMinSize((optimal_width, optimal_height))
			
			# Resize to optimal size
			parent.SetSize((optimal_width, optimal_height))
			
			parent.Layout()
			parent.Refresh()
			
		except:
			pass  # Silent fail


	def OnPageChanging(self, event):
		""" Page is changing.
		"""
		new = event.GetSelection()
		### plug-in page
		if new == 4:  # Plugins tab (index 4)
			### list of plug-ins file in plug-in directory
			l = list(os.walk(PLUGINS_PATH))
			### populate checklist with file in plug-ins directory
			wx.CallAfter(self.CheckList.Populate, (l))
		event.Skip()

	def OnAdd(self, event):
		""" Add plug-in.
		"""
		wcd = 'All files (*)|*|Editor files (*.py)|*.py'
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=DEVSIMPY_PACKAGE_PATH, defaultFile='', wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
		if open_dlg.ShowModal() == wx.ID_OK:
			filename = open_dlg.GetPath()
			### sure is python file
			if filename.endswith(('.py','pyc')):
				### Insert item in list
				basename,ext = os.path.splitext(os.path.basename(filename))
				root = os.path.dirname(filename)
				self.CheckList.Importing(root, basename)
				
				### trying to copy file in plug-in directory in order to find it again when the plugins list is populate (depending on the __init__.py file)
				try:
					shutil.copy2(filename, PLUGINS_PATH)
				except Exception as info:
					sys.stderr.write(_('ERROR: %s copy failed!\n%s')%(os.path.basename(filename), str(info)))
				else:
					### rewrite the new __init__.py file that contain the new imported plugin (basename) in order to populate the future generale plugins list
					AddToInitFile(PLUGINS_PATH, [basename])

			else:
				sys.stderr.write(_('ERROR: %s is not a python file.\nOnly python file can be added as plugin.')%(os.path.basename(filename)))

		open_dlg.Destroy()

	def OnDelete(self, event):
		""" Delete plugins item and python source file.
		"""

		for i in range(self.CheckList.GetItemCount()):
			if self.CheckList.IsSelected(i):
				### Delete query
				dial = wx.MessageDialog(self, _('Do you want to delete the selected %s plugins?'%self.CheckList.GetItemText(i)), _('Plugin MAnager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				if dial.ShowModal() == wx.ID_YES:
					### for selected plug-ins
				
					module = self.CheckList.GetPyData(i)[0]
					basename,ext = os.path.splitext(os.path.basename(module.__file__))

					### delete item
					self.CheckList.DeleteItem(i)

					### TODO: remove also into __init__.py
					### delete the selected plugin from__init__.py
					DelToInitFile(PLUGINS_PATH, [basename])

					try:
						#name, ext = os.path.splitext(module.__file__)
						dlg = wx.MessageDialog(self, _('Do you want to remove the corresponding file %s?')%basename, _('Preference Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
						if dlg.ShowModal() == wx.ID_YES:
							os.remove(module.__file__)			
					except Exception:
						sys.stderr.write(_('ERROR: plugin file not deleted!'))
					else:
						dlg.Destroy()	
				else:
					sys.stderr.write(_('Select plugins to delete'))

				dial.Destroy()

	def OnRefresh(self, event):
		""" Refresh list of plugins.
		"""
		self.CheckList.Clear()
		l = list(os.walk(PLUGINS_PATH))
		### populate checklist with file in plug-ins directory
		wx.CallAfter(self.CheckList.Populate, (l))

	def OnApply(self,evt):
		""" Apply button has been pressed and we must take into account all changes for each panel
		"""
		for page in [self.GetPage(i) for i in range(self.GetPageCount())]:
			page.OnApply(evt)

########################################################################
class PreferencesGUI(wx.Frame):
	""" DEVSimPy Preferences General User Interface class
	"""

	def __init__(self, parent, title):
		"""
			Constructor.
		"""
		wx.Frame.__init__(self, parent, wx.NewIdRef(), title, style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN)

		self.InitUI()
		
		self.Center()

	def InitUI(self):
		""" Init the UI.
		"""
		icon = wx.Icon()
		icon.CopyFromBitmap(load_and_resize_image("preferences.png"))
		self.SetIcon(icon)
		
		self.SetSize((400,680))
		
		panel = wx.Panel(self, wx.NewIdRef())
		self.pref = Preferences(panel)
		
		# Boutons Apply et Cancel
		self.cancel = wx.Button(panel, wx.ID_CANCEL)
		self.apply = wx.Button(panel, wx.ID_OK)
		
		# Bouton d'aide générale (NOUVEAU)
		self.help_btn = wx.Button(panel, wx.ID_HELP, "?")
		self.help_btn.SetToolTip(_("Show help about preferences"))
		
		self.apply.SetToolTipString = self.apply.SetToolTip
		self.cancel.SetToolTipString = self.cancel.SetToolTip
		
		self.apply.SetToolTipString(_("Apply all changing"))
		self.cancel.SetToolTipString(_("Cancel without changing"))
		
		self.apply.SetDefault()
		
		# Layout
		vbox = wx.BoxSizer(wx.VERTICAL)
		hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
		
		hbox_buttons.Add(self.help_btn, 0, wx.ALL, 5)
		hbox_buttons.AddStretchSpacer()
		hbox_buttons.Add(self.cancel, 0, wx.ALL, 5)
		hbox_buttons.Add(self.apply, 0, wx.ALL, 5)
		
		vbox.Add(self.pref, 1, wx.EXPAND | wx.ALL, 10)
		vbox.Add(hbox_buttons, 0, wx.EXPAND | wx.ALL, 5)
		
		panel.SetSizer(vbox)
		
		# Binding
		self.Bind(wx.EVT_BUTTON, self.OnShowPreferencesHelp, id=wx.ID_HELP)
		self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)


	def OnShowPreferencesHelp(self, event):
		"""Show help about preferences dialog"""
		
		help_msg = _(
			"DEVSimPy PREFERENCES\n\n"
			"═══════════════════════════════════════\n\n"
			"This dialog allows you to configure DEVSimPy settings.\n"
			"Navigate through tabs to access different preference categories.\n\n"
			"═══════════════════════════════════════\n\n"
			"GENERAL TAB:\n\n"
			"• Plug-ins Directory: Location of DEVSimPy plugins\n"
			"  Change to use custom plugin collections\n\n"
			"• Library Directory: Location of DEVS model libraries\n"
			"  Main directory containing all model libraries\n\n"
			"• Output Directory: Where simulation outputs are saved\n"
			"  Results, logs, and generated files location\n\n"
			"• Number of Recent Files: Length of recent files list\n"
			"  Range: 2-20 files\n\n"
			"• Font Size: Size of text in block diagrams\n"
			"  Range: 2-20 points\n\n"
			"• Deep of History: Number of undo/redo levels\n"
			"  Range: 2-100 operations\n\n"
			"• wxPython Version: Select wxPython version to use\n"
			"  Requires restart to take effect\n\n"
			"• Transparency: Enable transparency for detached frames\n"
			"  Makes windows semi-transparent when moving\n\n"
			"• Notifications: Enable notification messages\n"
			"  Show pop-up notifications for events\n\n"
			"═══════════════════════════════════════\n\n"
			"SIMULATION TAB:\n\n"
			"• DEVS Kernel: Choose between PyDEVS and PyPDEVS\n"
			"  PyDEVS: Classic DEVS simulator\n"
			"  PyPDEVS: Parallel DEVS simulator (recommended)\n\n"
			"• Default Strategy: Simulation algorithm to use\n"
			"  - original: Standard DEVS algorithm\n"
			"  - bag: Optimized message handling\n"
			"  - direct: Direct coupling (fastest)\n\n"
			"• Sound on Success: Play sound when simulation completes\n"
			"  Select custom MP3/WAV file\n\n"
			"• Sound on Error: Play sound when simulation fails\n"
			"  Helps detect problems quickly\n\n"
			"• No Time Limit: Default state for NTL checkbox\n"
			"  Run simulations until all models inactive\n\n"
			"• Plot Dynamic Frequency: How often to update plots\n"
			"  Higher = more frequent updates (slower)\n"
			"  Lower = less frequent updates (faster)\n\n"
			"═══════════════════════════════════════\n\n"
			"EDITOR TAB:\n\n"
			"• Use DEVSimPy Local Editor: Use built-in code editor\n"
			"  When checked: Use internal editor\n"
			"  When unchecked: Use external editor\n\n"
			"• Select External Editor: Choose external code editor\n"
			"  Available: Spyder, Pyzo, or others\n"
			"  Click Refresh to detect newly installed editors\n\n"
			"Note: External editor must be installed separately\n"
			"Use 'Update' button to install missing editors\n\n"
			"═══════════════════════════════════════\n\n"
			"AI TAB:\n\n"
			"• Select an AI: Choose AI code generation service\n"
			"  - ChatGPT: OpenAI's language model\n"
			"  - Ollama: Local AI models\n\n"
			"• API Key (ChatGPT): Your OpenAI API key\n"
			"  Get from: https://platform.openai.com/api-keys\n"
			"  Stored securely, never shared\n\n"
			"• Port (Ollama): Local Ollama server port\n"
			"  Default: 11434\n"
			"  Ollama must be running locally\n\n"
			"• Check Button: Verify AI configuration\n"
			"  Tests connection and validates settings\n\n"
			"• Info Button: Open AI documentation\n"
			"  Learn more about selected AI service\n\n"
			"═══════════════════════════════════════\n\n"
			"PLUGINS TAB:\n\n"
			"• Plugin List: All available DEVSimPy plugins\n"
			"  Checkbox = enabled/disabled state\n\n"
			"• Add (+): Install new plugins\n"
			"  Browse for plugin files to add\n\n"
			"• Delete (-): Remove all plugins\n"
			"  Warning: Deletes all plugin files!\n\n"
			"• Refresh (⟳): Update plugin list\n"
			"  Detects newly added plugins\n\n"
			"Double-click plugin name to enable/disable\n"
			"Changes take effect after restart\n\n"
			"═══════════════════════════════════════\n\n"
			"APPLYING CHANGES:\n\n"
			"• Apply: Save all changes and close dialog\n"
			"  Settings are written to .devsimpy config file\n\n"
			"• Cancel: Discard changes and close\n"
			"  All modifications are lost\n\n"
			"Some changes require DEVSimPy restart:\n"
			"- wxPython version change\n"
			"- DEVS kernel change (PyDEVS ↔ PyPDEVS)\n"
			"- Plugin enable/disable\n"
			"- Library directory change\n\n"
			"═══════════════════════════════════════\n\n"
			"TIPS:\n\n"
			"- Save preferences before closing DEVSimPy\n"
			"- Test AI configuration before using code generation\n"
			"- Increase undo history for complex modeling\n"
			"- Use PyPDEVS for better performance\n"
			"- External editors provide better code assistance\n"
			"- Plugins extend DEVSimPy functionality\n"
			"- Check 'Output Directory' has write permissions"
		)
		
		try:
			import wx.lib.dialogs
			dlg = wx.lib.dialogs.ScrolledMessageDialog(
				self, 
				help_msg, 
				_("Preferences Help"),
				size=(700, 650)
			)
			dlg.ShowModal()
			dlg.Destroy()
		except Exception as e:
			# Fallback
			wx.MessageBox(
				help_msg,
				_("Preferences Help"),
				wx.OK | wx.ICON_INFORMATION
			)

	def OnApply(self, evt):
		""" Apply button has been clicked.
		"""
		self.pref.OnApply(evt)
		self.Close()

	def OnCancel(self, evt):
		""" Cancel button has been invoked.
		"""
		self.Close()
		evt.Skip()

	def OnClose(self, evt):
		""" Close button has been invoked.
		"""
		self.Close()
		evt.Skip()
