# -*- coding: utf-8 -*-  # noqa: UP009

"""
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AIPrompterDialog.py ---
#                     --------------------------------
#                            Copyright (c) 2024
#                    A. Dominci (dominici_a@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 10/28/2024
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
"""

import json
import threading
import wx
import os
import sys
import builtins

import gettext

_ = gettext.gettext

from Utilities import load_and_resize_image

import AICoupledSession

from CoupledStructurePreview import StructurePreviewPanel

from AIFileContext import (
	AIFileError,
	compose_prompt,
	load_attachment,
	summarize_attachments,
)


# Définition du dialogue personnalisé
class AIPrompterDialog(wx.Dialog):
	def __init__(
		self,
		parent,
		title=_("AI Code Editor"),  # noqa: B008
		code_to_replace="",
		adapter=None,
		model_kind="atomic",
		model_name=None,
		inputs=None,
		outputs=None,
		catalog=None,
		archive_path=None,
		session=None,
	):
		super().__init__(parent, id=wx.ID_ANY, title=title)

		_icon = wx.Icon()
		_icon.CopyFromBitmap(load_and_resize_image("puce_ai.png"))
		self.SetIcon(_icon)

		### local copy
		self.adapter = adapter
		self.parent = parent

		### "atomic" generates a model class, "coupled" generates a structure
		self.model_kind = model_kind or "atomic"
		self.model_name = model_name
		self.inputs = inputs
		self.outputs = outputs
		self.catalog = catalog

		### archive that stores the session of a coupled model (.cmd/.amd)
		self.archive_path = archive_path
		self.session = dict(session or {})
		self.session_data = None
		self._session_id = self.session.get("session_id")

		### conversation of the coupled-model assistant, restored from the
		### archive so a reopened session keeps its context
		self.coupled_messages = self._clean_session_messages(
			self.session.get("messages")
		)

		### generate the structure only (no atomic model code)
		self.structure_only = bool(self.session.get("structure_only", False))

		### reopen the previous structure (editable) instead of an empty box
		if (
			self.model_kind == "coupled"
			and not code_to_replace
			and isinstance(self.session.get("structure"), dict)
		):
			code_to_replace = json.dumps(
				self.session["structure"], indent=2, ensure_ascii=False
			)

		self.code_to_replace = code_to_replace

		### editor instance
		if parent and self.model_kind != "coupled":
			nb = parent.GetNoteBook()
			self.editor = nb.GetCurrentPage()
		else:
			self.editor = None

		### Code generated inside the self.code_text field
		self.generated_code = ""

		# generated JSON representing a newly created model
		self.model_json = None
		# validated structure of a newly created coupled model
		self.coupled_model = None
		# local documents whose text is added to the prompt
		self.attachments = []
		self._generation_active = False
		self._stop_event = threading.Event()
		# prompt of the request being processed (stored in the conversation)
		self._pending_prompt = ""

		self.__init_ui()
		self.Bind(wx.EVT_CLOSE, self.on_close)
		self.Center()

		### draw the graphical preview of a restored structure
		self._refresh_structure_preview()

		### tell the user that the previous conversation was reopened
		if self.model_kind == "coupled" and self.coupled_messages:
			self._append_trace(
				_("\nSession restored ({count} message(s)).\n").format(
					count=len(self.coupled_messages)
				)
			)

	def __init_ui(self):
		"""Initialize the user interface"""

		# Taille optimale
		self.SetSize((760, 820))
		self.SetMinSize((680, 640))

		panel = wx.Panel(self)
		panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
		self._main_panel = panel

		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Section Generated Code ---
		if self.model_kind == "coupled":
			code_label = _("Coupled Model Structure")
		else:
			code_label = _("Generated Code")

		code_static = wx.StaticBox(panel, label=code_label)
		code_box = wx.StaticBoxSizer(code_static, wx.VERTICAL)

		# Police monospace pour le code
		font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		### Coupled structures are shown either as JSON or as a diagram.
		self.structure_notebook = None
		self.structure_preview = None
		self.structure_preview_message = None
		self.preview_refresh_button = None

		if self.model_kind == "coupled":
			self.structure_notebook = wx.Notebook(code_static)

			json_page = wx.Panel(self.structure_notebook)
			self.code_text = wx.TextCtrl(
				json_page,
				value=self.code_to_replace,
				style=wx.TE_MULTILINE | wx.TE_RICH2,
			)
			self.code_text.SetFont(font)

			json_sizer = wx.BoxSizer(wx.VERTICAL)
			json_sizer.Add(
				self.code_text, proportion=1, flag=wx.ALL | wx.EXPAND, border=5
			)
			json_page.SetSizer(json_sizer)

			preview_page = wx.Panel(self.structure_notebook)
			preview_sizer = wx.BoxSizer(wx.VERTICAL)

			preview_toolbar = wx.BoxSizer(wx.HORIZONTAL)
			self.preview_refresh_button = wx.Button(
				preview_page, label=_("Refresh preview"), size=(140, 28)
			)
			self.preview_refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_preview)
			self.preview_refresh_button.SetToolTip(
				_("Redraw the graphical view from the current JSON structure")
			)
			preview_toolbar.Add(self.preview_refresh_button, flag=wx.RIGHT, border=8)

			self.structure_preview_message = wx.StaticText(
				preview_page, label=_("Preview of the structure before validation.")
			)
			self.structure_preview_message.SetForegroundColour(wx.Colour(100, 100, 100))
			preview_toolbar.Add(
				self.structure_preview_message,
				proportion=1,
				flag=wx.ALIGN_CENTER_VERTICAL,
			)

			preview_sizer.Add(
				preview_toolbar, flag=wx.EXPAND | wx.ALL, border=5
			)

			self.structure_preview = StructurePreviewPanel(preview_page)
			preview_sizer.Add(
				self.structure_preview,
				proportion=1,
				flag=wx.EXPAND | wx.ALL,
				border=5,
			)
			preview_page.SetSizer(preview_sizer)

			self.structure_notebook.AddPage(json_page, _("JSON"))
			self.structure_notebook.AddPage(preview_page, _("Graphical view"))

			code_box.Add(
				self.structure_notebook,
				proportion=1,
				flag=wx.ALL | wx.EXPAND,
				border=5,
			)

			self.code_text.Bind(wx.EVT_TEXT, self.on_structure_text_change)
			self.structure_notebook.Bind(
				wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_structure_page_changed
			)
		else:
			self.code_text = wx.TextCtrl(
				code_static, value=self.code_to_replace, style=wx.TE_MULTILINE | wx.TE_RICH2
			)
			self.code_text.SetFont(font)

			code_box.Add(self.code_text, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

		main_sizer.Add(code_box, proportion=2, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, border=15)

		# --- Section Live AI Output ---
		trace_static = wx.StaticBox(panel, label=_("Live AI Output"))
		trace_box = wx.StaticBoxSizer(trace_static, wx.VERTICAL)
		self.trace_text = wx.TextCtrl(
			trace_static,
			value="",
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
		)
		self.trace_text.SetFont(font)
		trace_box.Add(self.trace_text, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
		main_sizer.Add(
			trace_box,
			proportion=1,
			flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
			border=15,
		)

		# --- Section Prompt ---
		prompt_static = wx.StaticBox(panel, label=_("AI Prompt"))
		prompt_box = wx.StaticBoxSizer(prompt_static, wx.VERTICAL)

		# Info text
		if self.model_kind == "coupled":
			info_label = _(
				"Describe the coupled model you want to build. The AI returns a JSON "
				"structure (submodels and couplings) that you can edit before applying:"
			)
			hint_label = _(
				"Example: Build a queue model fed by a generator and observed by a collector..."
			)
		else:
			info_label = _("Describe what you want the AI to do with the code above:")
			hint_label = _("Example: Add error handling to this function...")

		info_text = wx.StaticText(prompt_static, label=info_label)
		info_text.SetForegroundColour(wx.Colour(100, 100, 100))
		prompt_box.Add(info_text, flag=wx.ALL, border=5)

		### structure-only mode: no atomic model code is generated
		self.structure_only_check = None

		if self.model_kind == "coupled":
			self.structure_only_check = wx.CheckBox(
				prompt_static,
				label=_("Structure only: do not generate the code of the atomic models"),
			)
			self.structure_only_check.SetValue(self.structure_only)
			self.structure_only_check.SetToolTip(
				_(
					"Only build the coupled model structure (submodels and "
					"couplings). Submodels that are not in the library are "
					"created as empty atomic models; no atomic model code is "
					"generated."
				)
			)
			prompt_box.Add(
				self.structure_only_check,
				flag=wx.LEFT | wx.RIGHT | wx.BOTTOM,
				border=5,
			)

		self.prompt_input = wx.TextCtrl(
			prompt_static, value="", style=wx.TE_MULTILINE | wx.TE_RICH2
		)
		self.prompt_input.SetFont(font)
		self.prompt_input.SetHint(hint_label)
		prompt_box.Add(self.prompt_input, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

		# Set the focus to the prompt_input field
		self.prompt_input.SetFocus()

		# Bind text event
		self.prompt_input.Bind(wx.EVT_TEXT, self.on_prompt_input_change)

		main_sizer.Add(
			prompt_box, proportion=1, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=15
		)

		# --- Section Attached Files ---
		attach_static = wx.StaticBox(panel, label=_("Attached Files (optional)"))
		attach_box = wx.StaticBoxSizer(attach_static, wx.VERTICAL)

		attach_buttons = wx.BoxSizer(wx.HORIZONTAL)

		self.attach_button = wx.Button(
			attach_static, label=_("Attach files..."), size=(130, 30)
		)
		self.attach_button.Bind(wx.EVT_BUTTON, self.on_attach_files)
		self.attach_button.SetToolTip(
			_(
				"Attach TXT or PDF files. Their text is extracted locally and "
				"added to the prompt; scanned PDFs require OCR."
			)
		)
		attach_buttons.Add(self.attach_button, flag=wx.RIGHT, border=5)

		self.remove_attachment_button = wx.Button(
			attach_static, label=_("Remove"), size=(90, 30)
		)
		self.remove_attachment_button.Bind(wx.EVT_BUTTON, self.on_remove_attachment)
		self.remove_attachment_button.Enable(False)
		attach_buttons.Add(self.remove_attachment_button, flag=wx.RIGHT, border=5)

		self.clear_attachments_button = wx.Button(
			attach_static, label=_("Clear"), size=(90, 30)
		)
		self.clear_attachments_button.Bind(wx.EVT_BUTTON, self.on_clear_attachments)
		self.clear_attachments_button.Enable(False)
		attach_buttons.Add(self.clear_attachments_button, flag=wx.RIGHT, border=10)

		self.attachments_summary = wx.StaticText(
			attach_static, label=_("No file attached.")
		)
		self.attachments_summary.SetForegroundColour(wx.Colour(100, 100, 100))
		attach_buttons.Add(
			self.attachments_summary, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL
		)

		attach_box.Add(attach_buttons, flag=wx.ALL | wx.EXPAND, border=5)

		### The list is always laid out (empty when nothing is attached):
		### showing it after the first layout would leave it at position (0, 0).
		self.attachments_list = wx.ListBox(
			attach_static, style=wx.LB_SINGLE, size=(-1, 60)
		)
		self.attachments_list.Bind(wx.EVT_LISTBOX, self.on_attachment_selected)
		attach_box.Add(
			self.attachments_list,
			flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
			border=5,
		)

		main_sizer.Add(
			attach_box, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=15
		)

		if not self._attachments_supported():
			self.attach_button.Disable()
			self.attach_button.SetToolTip(
				_("The selected AI provider does not accept attached files.")
			)

		# --- Buttons Section ---
		button_panel = wx.Panel(panel)
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)

		# Bouton Help/Info à gauche
		self.help_button = wx.Button(button_panel, label=_("Help"), size=(100, 32))
		self.help_button.SetBitmap(load_and_resize_image("info.png"))
		self.help_button.Bind(wx.EVT_BUTTON, self.on_help)
		self.help_button.SetToolTip(_("Show help on how to use this dialog"))
		button_sizer.Add(self.help_button, flag=wx.RIGHT, border=10)

		# Spacer pour pousser les autres boutons à droite
		button_sizer.AddStretchSpacer()

		# Bouton Send to AI
		self.send_button = wx.Button(button_panel, label=_("Send to AI"), size=(120, 32))
		self.send_button.Bind(wx.EVT_BUTTON, self.on_send_ai)
		self.send_button.SetToolTip(_("Send the prompt to AI for processing"))
		self.send_button.Enable(False)
		button_sizer.Add(self.send_button, flag=wx.RIGHT, border=5)

		self.stop_button = wx.Button(button_panel, label=_("Stop"), size=(80, 32))
		self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_ai)
		self.stop_button.SetToolTip(_("Stop the current generation"))
		self.stop_button.Enable(False)
		button_sizer.Add(self.stop_button, flag=wx.RIGHT, border=5)

		# Bouton Insert/Replace ou Apply
		if self.editor:
			self.insert_button = wx.Button(button_panel, label=_("Insert/Replace"), size=(120, 32))
			self.insert_button.Bind(wx.EVT_BUTTON, self.on_insert)
			self.insert_button.SetToolTip(_("Insert or replace the generated code in the editor"))
			self.insert_button.Enable(False)
			button_sizer.Add(self.insert_button, flag=wx.RIGHT, border=5)
		else:
			self.insert_button = wx.Button(
				button_panel, id=wx.ID_OK, label=_("Apply"), size=(120, 32)
			)
			self.insert_button.Bind(wx.EVT_BUTTON, self.on_ok)
			self.insert_button.SetToolTip(_("Apply the generated code"))
			self.insert_button.Enable(False)
			button_sizer.Add(self.insert_button, flag=wx.RIGHT, border=5)

			self.download_json_button = wx.Button(
				button_panel, label=_("Download JSON"), size=(130, 32)
			)
			self.download_json_button.Bind(wx.EVT_BUTTON, self.on_download_json)
			self.download_json_button.SetToolTip(
				_("Download the JSON corresponding to the coupled model structure")
				if self.model_kind == "coupled"
				else _("Download the JSON corresponding to the atomic model")
			)
			self.download_json_button.Enable(False)
			button_sizer.Add(self.download_json_button, flag=wx.RIGHT, border=5)

		# Bouton Cancel
		self.cancel_button = wx.Button(button_panel, wx.ID_CANCEL, _("Cancel"), size=(100, 32))
		button_sizer.Add(self.cancel_button)

		button_panel.SetSizer(button_sizer)
		main_sizer.Add(button_panel, flag=wx.ALL | wx.EXPAND, border=15)

		panel.SetSizer(main_sizer)
		panel.Layout()

	def on_help(self, event):
		"""Display help information"""

		if self.editor:
			help_text = _(
				"AI Code Editor - Help\n\n"
				"This tool helps you modify code using AI assistance.\n\n"
				"How to use:\n\n"
				"1. Generated Code Section:\n"
				"   • Shows the initial code or AI-generated modifications\n"
				"   • You can manually edit this code if needed\n\n"
				"2. AI Prompt Section:\n"
				"   • Describe what you want the AI to do\n"
				"   • Examples:\n"
				"     - 'Add error handling'\n"
				"     - 'Optimize this function'\n"
				"     - 'Add documentation comments'\n"
				"     - 'Refactor to use list comprehension'\n\n"
				"3. Buttons:\n"
				"   • Send to AI: Process your prompt and generate code\n"
				"   • Insert/Replace: Put the code into your editor\n"
				"   • Cancel: Close without changes\n\n"
				"4. Attached Files:\n"
				"   • Use 'Attach files...' to add TXT or PDF documents\n"
				"   • Their text is extracted locally and added to the prompt\n"
				"   • Scanned PDFs need OCR before they can be attached\n\n"
				"Tips:\n"
				"• Be specific in your prompts for better results\n"
				"• You can send multiple prompts to refine the code\n"
				"• Review the generated code before inserting"
			)
		elif self.model_kind == "coupled":
			help_text = _(
				"AI Coupled Model Generator - Help\n\n"
				"This tool builds a coupled model from a natural language description.\n\n"
				"How to use:\n\n"
				"1. Coupled Model Structure Section:\n"
				"   • JSON tab: shows the structure proposed by the AI\n"
				"   • Graphical view tab: draws the submodels, their ports and\n"
				"     the couplings, before the structure is validated\n"
				"   • It lists the submodels, their ports and the couplings\n"
				"   • You can edit the JSON before applying it\n\n"
				"2. AI Prompt Section:\n"
				"   • Describe the structure you want to build\n"
				"   • Examples:\n"
				"     - 'A generator feeding a queue observed by a collector'\n"
				"     - 'Two processors in parallel with a shared input'\n\n"
				"3. Structure Only:\n"
				"   • Check 'Structure only' to build the submodels and couplings\n"
				"     without generating the code of the atomic models\n"
				"   • Submodels that are not in the library are then created as\n"
				"     empty atomic models, ready to be implemented later\n\n"
				"4. Buttons:\n"
				"   • Send to AI: Generate the coupled model structure\n"
				"   • Apply: Validate the JSON and build the model\n"
				"   • Download JSON: Save the structure as a JSON file\n"
				"   • Cancel: Close without saving\n\n"
				"5. Attached Files:\n"
				"   • Use 'Attach files...' to add TXT or PDF documents\n"
				"   • Their text is extracted locally and added to the prompt\n"
				"   • Scanned PDFs need OCR before they can be attached\n\n"
				"Notes:\n"
				"• Use \"generate\": \"existing\" to reuse a library model\n"
				"• Use \"generate\": \"behavior\" when no library model matches: "
				"the AI writes the atomic model from its \"behavior\" description "
				"and it is saved next to the coupled model\n"
				"• The generated class is named like its submodel label, so it "
				"matches the name of its code block\n"
				"• Use \"generate\": \"stub\" to create an empty atomic model with "
				"the declared ports\n"
				"• In structure-only mode the AI returns \"stub\" submodels "
				"instead of \"behavior\" ones\n"
				"• Port indices start at 0\n"
				"• The special names __input__ and __output__ reference the "
				"coupled model's own ports\n"
				"• A submodel that declares 0 input ports cannot receive a "
				"connection, and a submodel with 0 output ports cannot send one"
			)
		else:
			help_text = _(
				"AI Model Generator - Help\n\n"
				"This tool helps you generate model code using AI.\n\n"
				"How to use:\n\n"
				"1. Generated Code Section:\n"
				"   • Shows the AI-generated model code\n"
				"   • You can manually edit this code if needed\n\n"
				"2. AI Prompt Section:\n"
				"   • Describe the model you want to create\n"
				"   • Examples:\n"
				"     - 'Create a queue model with FIFO behavior'\n"
				"     - 'Generate a sensor model that samples data'\n"
				"     - 'Build a controller with PID algorithm'\n\n"
				"3. Buttons:\n"
				"   • Send to AI: Generate the model from your prompt\n"
				"   • Apply: Accept the generated code\n"
				"   • Download JSON: Save the model as JSON file\n"
				"   • Cancel: Close without saving\n\n"
				"4. Attached Files:\n"
				"   • Use 'Attach files...' to add TXT or PDF documents\n"
				"   • Their text is extracted locally and added to the prompt\n"
				"   • Scanned PDFs need OCR before they can be attached\n\n"
				"Tips:\n"
				"• Describe the model behavior clearly\n"
				"• Specify inputs, outputs, and state variables\n"
				"• Review and test the generated model"
			)

		dlg = wx.MessageDialog(
			self, help_text, _("Help - AI Code Editor"), wx.OK | wx.ICON_INFORMATION
		)
		dlg.ShowModal()
		dlg.Destroy()

	def on_prompt_input_change(self, event):
		"""Fonction de rappel qui s'active lorsque l'utilisateur tape dans le champ de prompt."""

		if self._generation_active:
			self.send_button.Enable(False)
			return

		input_text = self.prompt_input.GetValue().strip()

		# Activer/désactiver les boutons selon le texte d'entrée
		if input_text:
			self.send_button.Enable(True)
		else:
			self.send_button.Enable(False)

	def _attachments_supported(self):
		"""Return True when the selected adapter accepts attached files."""
		check = getattr(self.adapter, "supports_file_attachments", None)

		if callable(check):
			try:
				return bool(check())
			except Exception:
				return False

		### Adapters without the capability method are assumed to accept text
		return self.adapter is not None

	def on_attach_files(self, event):
		"""Select TXT or PDF files whose text is added to the prompt."""
		if self._generation_active or not self._attachments_supported():
			return

		wildcard = _(
			"Text and PDF files (*.txt;*.md;*.pdf)|*.txt;*.md;*.pdf|"
			"All files (*.*)|*.*"
		)

		dlg = wx.FileDialog(
			self,
			message=_("Attach files to the prompt"),
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
		)

		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return

		paths = dlg.GetPaths()
		dlg.Destroy()
		self._add_attachments(paths)

	def _add_attachments(self, paths):
		"""Load ``paths`` and add the successfully read files to the prompt."""
		errors = []
		known = {attachment.path for attachment in self.attachments}

		with wx.BusyCursor():
			for path in paths:
				if os.path.abspath(path) in known:
					continue

				try:
					attachment = load_attachment(path)
				except AIFileError as error:
					errors.append(str(error))
					continue

				self.attachments.append(attachment)
				known.add(attachment.path)

		self._refresh_attachments()

		if errors:
			wx.MessageBox(
				"\n".join(errors),
				_("Cannot attach file"),
				wx.OK | wx.ICON_WARNING,
			)

	def on_remove_attachment(self, event):
		"""Remove the file selected in the attachment list."""
		selection = self.attachments_list.GetSelection()

		if selection == wx.NOT_FOUND or selection >= len(self.attachments):
			return

		del self.attachments[selection]
		self._refresh_attachments()

	def on_clear_attachments(self, event):
		"""Remove every attached file."""
		self.attachments = []
		self._refresh_attachments()

	def on_attachment_selected(self, event):
		"""Enable the Remove button when a file is selected."""
		self.remove_attachment_button.Enable(
			not self._generation_active
			and self.attachments_list.GetSelection() != wx.NOT_FOUND
		)

	def _refresh_attachments(self):
		"""Update the attachment list, summary and button states."""
		self.attachments_list.Clear()

		for attachment in self.attachments:
			suffix = _(" (truncated)") if attachment.truncated else ""
			self.attachments_list.Append(
				f"{attachment.name} - {attachment.chars:,} chars{suffix}"
			)

		has_files = bool(self.attachments)

		self.remove_attachment_button.Enable(False)
		self.clear_attachments_button.Enable(
			has_files and not self._generation_active
		)
		self.attachments_summary.SetLabel(
			summarize_attachments(self.attachments)
		)
		self._main_panel.Layout()

	# ================================================================
	# Coupled-model session
	# ================================================================
	@staticmethod
	def _clean_session_messages(messages):
		"""Return a bounded conversation usable as AI history."""
		cleaned = []

		for message in messages or []:
			if not isinstance(message, dict):
				continue

			role = message.get("role")
			content = message.get("content")

			if role not in ("user", "assistant") or not isinstance(content, str):
				continue

			if content.strip():
				cleaned.append({"role": role, "content": content})

		return cleaned

	def on_structure_text_change(self, event):
		"""Refresh the graphical preview while the JSON is edited."""
		if event is not None:
			event.Skip()
		self._refresh_structure_preview()

	def on_structure_page_changed(self, event):
		"""Refresh the preview when its tab is selected."""
		if event is not None:
			event.Skip()
		self._refresh_structure_preview()

	def on_refresh_preview(self, event):
		"""Redraw the preview on demand."""
		self._refresh_structure_preview()

	def _set_preview_status(self, message):
		"""Update the text shown next to the preview refresh button."""
		if self.structure_preview_message is not None:
			self.structure_preview_message.SetLabel(message)
			self.structure_preview_message.GetParent().Layout()

	def _refresh_structure_preview(self):
		"""Rebuild the graphical view from the JSON currently displayed.

		The structure is normalized with the same rules as the validation
		performed by the Apply button, so the preview shows what will be
		built.  When the JSON is incomplete or invalid, the preview panel
		shows the validation error instead of a diagram.
		"""
		if self.structure_preview is None:
			return

		from CoupledStructure import (
			CoupledStructureError,
			normalize_coupled_structure,
		)

		text = self.code_text.GetValue()

		if not text.strip():
			self.structure_preview.SetMessage(_("No structure to display yet."))
			self._set_preview_status(
				_("Preview of the structure before validation.")
			)
			return

		try:
			data = self._parse_structure(text)

			if data is None:
				raise CoupledStructureError(_("The structure is not valid JSON."))

			structure = normalize_coupled_structure(
				data,
				catalog=self.catalog,
				name=self.model_name,
				inputs=self.inputs,
				outputs=self.outputs,
			)
		except Exception as error:  # noqa: BLE001
			self.structure_preview.SetMessage(
				_("Preview unavailable:\n{}").format(str(error))
			)
			self._set_preview_status(_("The structure is not valid yet."))
			return

		self.structure_preview.SetStructure(structure)
		self._set_preview_status(
			_("{submodels} submodel(s), {connections} connection(s).").format(
				submodels=len(structure.get("submodels") or []),
				connections=len(structure.get("connections") or []),
			)
		)

	@staticmethod
	def _parse_structure(code):
		"""Return the JSON structure written in ``code``, or None."""
		if not str(code or "").strip():
			return None

		from CoupledStructure import parse_json_object

		try:
			data = parse_json_object(code)
		except Exception:
			return None

		return data if isinstance(data, dict) and data else None

	def _build_session_data(self):
		"""Return the session payload of the coupled assistant."""
		prompt = ""

		for message in reversed(self.coupled_messages):
			if message.get("role") == "user":
				prompt = message.get("content", "")
				break

		structure = (
			self._parse_structure(self.code_text.GetValue())
			or self.coupled_model
			or self.session.get("structure")
		)

		attachment_names = [
			attachment.name for attachment in self.attachments
		]

		return AICoupledSession.build_session(
			self.session,
			session_id=self._session_id,
			model_name=self.model_name or self.session.get("model_name"),
			provider=getattr(builtins, "SELECTED_IA", "") or None,
			ai_model=getattr(self.adapter, "model_name", "") or None,
			structure=structure,
			messages=self.coupled_messages,
			prompt=prompt,
			title=self.session.get("title"),
			attachments=attachment_names or None,
			structure_only=self._structure_only_enabled(),
		)

	def session_payload(self):
		"""Return the session payload of the coupled assistant, or None."""
		if self.model_kind != "coupled":
			return None

		return self._build_session_data()

	def _store_session(self):
		"""Persist the coupled session in the model archive, if any."""
		if self.model_kind != "coupled" or not self.archive_path:
			return None

		session = self._build_session_data()

		if not session.get("messages") and not session.get("structure"):
			return None

		session_id = AICoupledSession.save_session(
			self.archive_path,
			session,
			session_id=self._session_id,
		)

		if not session_id:
			return None

		self._session_id = session_id
		session["session_id"] = session_id
		self.session = session
		self.session_data = session

		return session_id

	def _record_coupled_turn(self, answer):
		"""Append the request/answer pair to the coupled conversation.

		The prompt is stored as typed by the user (without the text of the
		attached documents) so the reopened session stays readable.
		"""
		if self.model_kind != "coupled":
			return

		prompt = (self._pending_prompt or "").strip()

		if prompt and not (
			self.coupled_messages
			and self.coupled_messages[-1].get("role") == "user"
			and self.coupled_messages[-1].get("content") == prompt
		):
			self.coupled_messages.append({"role": "user", "content": prompt})

		if str(answer or "").strip():
			self.coupled_messages.append(
				{"role": "assistant", "content": str(answer)}
			)

		self._store_session()

	def on_ok(self, event):
		if self.model_kind == "coupled":
			from CoupledStructure import (
				CoupledStructureError,
				normalize_coupled_structure,
				parse_json_object,
			)

			try:
				data = parse_json_object(self.code_text.GetValue())
				structure = normalize_coupled_structure(
					data,
					catalog=self.catalog,
					name=self.model_name,
					inputs=self.inputs,
					outputs=self.outputs,
				)
			except CoupledStructureError as error:
				wx.MessageBox(
					_("The coupled model structure is invalid:\n{}").format(str(error)),
					_("Invalid structure"),
					wx.OK | wx.ICON_ERROR,
				)
				return

			### The wizard builds the python shell itself with coupledCode()
			self.generated_code = ""
			self.coupled_model = structure
			self.model_json = structure
			self._store_session()
			self.EndModal(wx.ID_OK)
			return

		self.generated_code = self.code_text.GetValue().strip()

		if self.generated_code:  # Only close if there's non-empty input
			self.EndModal(wx.ID_OK)

	def on_insert(self, event):

		if not self.editor:
			return

		generated_code = self.code_text.GetValue()

		selection = self.editor.GetSelection()
		textstring = self.editor.GetRange(selection[0], selection[1])

		# Remplacement du texte dans l'éditeur si le texte a été modifié
		if generated_code and generated_code != textstring:
			### si text selectionné dans le code à remplacer
			self.editor.ReplaceSelection(generated_code)
		### sinon on insère en place
		else:
			self.editor.AddText(generated_code)

		self.parent.Notification(
			True,
			_(f"{os.path.basename(self.editor.GetFilename())} modified"),  # noqa: INT001
			"",
			"",
		)

		self.Close()

	def on_send_ai(self, event):
		if self._generation_active:
			return

		prompt = self.prompt_input.GetValue()
		code = self.code_text.GetValue()
		self._pending_prompt = prompt
		self._generation_active = True
		self._stop_event.clear()
		self.send_button.Enable(False)
		self.send_button.SetLabel(_("Processing..."))
		self.stop_button.Enable(True)
		self.insert_button.Enable(False)
		self.cancel_button.Enable(False)
		self.attach_button.Enable(False)
		self.remove_attachment_button.Enable(False)
		self.clear_attachments_button.Enable(False)
		if self.structure_only_check is not None:
			self.structure_only_check.Enable(False)
		if hasattr(self, "download_json_button"):
			self.download_json_button.Enable(False)
		self.trace_text.SetValue(_("Starting request...\n"))

		self._generation_thread = threading.Thread(
			target=self._generate_in_background,
			args=(prompt, code),
			daemon=True,
		)
		self._generation_thread.start()

	def on_stop_ai(self, event):
		if not self._generation_active or self._stop_event.is_set():
			return
		self._stop_event.set()
		self.stop_button.Enable(False)
		self.trace_text.AppendText(_("\nStop requested; waiting for the current response chunk...\n"))

	def _generate_in_background(self, prompt, code):
		model_json = None
		stop_event = self._stop_event
		try:
			on_token = lambda token: wx.CallAfter(self._append_trace, token)

			if self.adapter is None:
				raise RuntimeError(_("No AI provider is selected."))

			# Provider preflight (LM Studio server up, model loaded, ...)
			ensure_ready = getattr(self.adapter, "ensure_ready", None)

			if callable(ensure_ready):
				ensure_ready()

			### Add the text of attached documents to the user prompt
			if self.attachments:
				wx.CallAfter(
					self._append_trace,
					_("\nUsing {count} attached file(s): {names}\n").format(
						count=len(self.attachments),
						names=", ".join(
							attachment.name for attachment in self.attachments
						),
					),
				)
				prompt = compose_prompt(prompt, self.attachments)

			if self.model_kind == "coupled":
				wx.CallAfter(
					self._append_trace,
					_("\nGenerating coupled model structure...\n"),
				)
				### structure-only mode: no atomic model code is generated
				structure_only = self._structure_only_enabled()

				if structure_only:
					wx.CallAfter(
						self._append_trace,
						_(
							"Structure only: the code of the atomic models is "
							"not generated.\n"
						),
					)

				### when the box already holds a structure (reopened session or
				### a previous answer), the assistant updates it instead of
				### creating a new one
				previous_structure = self._parse_structure(code)
				raw_structure = self.adapter.generate_coupled_model_json(
					prompt,
					catalog=self.catalog,
					model_name=self.model_name,
					inputs=self.inputs,
					outputs=self.outputs,
					previous_structure=previous_structure,
					history=list(self.coupled_messages),
					generate_atomic_code=not structure_only,
					on_token=on_token,
					stop_event=stop_event,
				)
				if stop_event.is_set():
					wx.CallAfter(self._finish_generation, None, None, None, True)
					return
				from CoupledStructure import (
					CoupledStructureError,
					normalize_coupled_structure,
					parse_json_object,
				)

				structure = parse_json_object(raw_structure)

				if structure_only:
					### keep the structure only: submodels that would need
					### generated code become empty stubs
					structure = self._skip_coupled_submodel_code(structure)
				else:
					### Generate the atomic code of submodels that ask for it.
					### This is what turns a described behavior into a real
					### model instead of binding it to an unrelated catalog
					### model.
					structure = self._generate_coupled_submodel_code(
						structure,
						on_token,
						stop_event,
					)

				if stop_event.is_set():
					wx.CallAfter(self._finish_generation, None, None, None, True)
					return

				modified_code = json.dumps(structure, indent=2)
				model_json = structure

				### Check the structure right away so inconsistencies are visible
				### in the trace panel instead of only after clicking Apply.
				try:
					normalize_coupled_structure(
						structure,
						catalog=self.catalog,
						name=self.model_name,
						inputs=self.inputs,
						outputs=self.outputs,
					)
				except CoupledStructureError as error:
					wx.CallAfter(
						self._append_trace,
						_("\nStructure check failed:\n{}\n").format(str(error)),
					)
				else:
					wx.CallAfter(
						self._append_trace,
						_("\nStructure check passed.\n"),
					)
			elif not self.editor:
				wx.CallAfter(self._append_trace, _("\nGenerating model specification...\n"))
				model_json = self.adapter.generate_model_json(
					prompt, on_token=on_token, stop_event=stop_event
				)
				if stop_event.is_set():
					wx.CallAfter(self._finish_generation, None, None, None, True)
					return
				if not isinstance(model_json, dict):
					raise RuntimeError(str(model_json))
				wx.CallAfter(self._append_trace, _("\nGenerating model code...\n"))
				modified_code = self.adapter.generate_model_code(
					model_json, on_token=on_token, stop_event=stop_event
				)
			else:
				full_prompt = self.adapter.modify_model_part_prompt(code, prompt)
				wx.CallAfter(self._append_trace, _("\nGenerating code...\n"))

				get_system_prompt = getattr(
					self.adapter, "system_prompt", None
				)
				system_prompt = (
					get_system_prompt() if callable(get_system_prompt) else ""
				)

				modified_code = self.adapter.generate_output(
					full_prompt,
					system_prompt=system_prompt,
					on_token=on_token,
					stop_event=stop_event,
				)
			if stop_event.is_set():
				wx.CallAfter(self._finish_generation, None, None, None, True)
			else:
				wx.CallAfter(self._finish_generation, modified_code, model_json, None)
		except Exception as error:
			if stop_event.is_set():
				wx.CallAfter(self._finish_generation, None, None, None, True)
			else:
				wx.CallAfter(self._finish_generation, None, model_json, error)

	def _structure_only_enabled(self):
		"""Return True when the user asked for the structure only."""
		if self.model_kind != "coupled" or self.structure_only_check is None:
			return False

		return bool(self.structure_only_check.GetValue())

	def _skip_coupled_submodel_code(self, structure):
		"""Keep the structure only: no atomic model code is generated.

		Submodels that ask for a generated behavior and do not carry code yet
		become ``stub`` submodels, so the wizard creates an empty atomic model
		with the declared ports instead of writing one from the behavior
		description.
		"""
		from CoupledStructure import GENERATE_ALIASES

		raw_submodels = (
			structure.get("submodels")
			or structure.get("models")
			or structure.get("components")
			or []
		)

		if not isinstance(raw_submodels, list):
			return structure

		for position, submodel in enumerate(raw_submodels):
			if not isinstance(submodel, dict):
				continue

			mode = str(
				submodel.get("generate", "existing") or "existing"
			).strip().lower()
			mode = GENERATE_ALIASES.get(mode, mode)

			if mode != "behavior":
				continue

			### submodels that already carry code keep it: only the generation
			### of new atomic models is disabled
			if str(submodel.get("code") or "").strip():
				continue

			label = str(submodel.get("label") or f"Model{position + 1}").strip()
			submodel["generate"] = "stub"

			wx.CallAfter(
				self._append_trace,
				_(
					"\nAtomic model code generation is disabled: '{label}' "
					"is created as an empty atomic model.\n"
				).format(label=label),
			)

		return structure

	def _generate_coupled_submodel_code(self, structure, on_token, stop_event):
		"""Generate the atomic code of coupled submodels that request it.

		Only submodels with ``"generate": "behavior"`` and no code yet are
		processed. The generated source is stored in ``submodel["code"]`` so
		the wizard can materialise a real ``.amd`` next to the coupled model.
		"""
		from CoupledStructure import (
			GENERATE_ALIASES,
			generate_submodel_code,
		)

		raw_submodels = (
			structure.get("submodels")
			or structure.get("models")
			or structure.get("components")
			or []
		)

		if not isinstance(raw_submodels, list):
			return structure

		coupled_name = str(
			structure.get("name")
			or structure.get("label")
			or self.model_name
			or "CoupledModel"
		).strip()

		for position, submodel in enumerate(raw_submodels):
			if not isinstance(submodel, dict):
				continue

			mode = str(
				submodel.get("generate", "existing") or "existing"
			).strip().lower()
			mode = GENERATE_ALIASES.get(mode, mode)

			if mode != "behavior":
				continue

			### a submodel that already carries code needs no generation
			if str(submodel.get("code") or "").strip():
				continue

			label = str(submodel.get("label") or f"Model{position + 1}").strip()
			behavior = str(
				submodel.get("behavior")
				or submodel.get("behaviour")
				or submodel.get("specification")
				or submodel.get("description")
				or ""
			).strip()

			### without a description there is nothing to generate; the
			### structure validation will report it to the user
			if not behavior:
				continue

			wx.CallAfter(
				self._append_trace,
				_("\nGenerating atomic model '{label}'...\n").format(label=label),
			)

			code = generate_submodel_code(
				submodel,
				coupled_name,
				self.adapter,
				on_token=on_token,
				stop_event=stop_event,
			)

			if stop_event.is_set():
				return structure

			submodel["code"] = code

			wx.CallAfter(
				self._append_trace,
				_("\nAtomic model '{label}' generated.\n").format(label=label),
			)

		return structure

	def _append_trace(self, text):
		### the dialog may be closed while a queued trace update is pending
		try:
			self.trace_text.AppendText(text)
			self.trace_text.ShowPosition(self.trace_text.GetLastPosition())
		except RuntimeError:
			pass

	def _finish_generation(self, modified_code, model_json, error, cancelled=False):
		self._generation_active = False
		self.send_button.SetLabel(_("Send to AI"))
		self.send_button.Enable(bool(self.prompt_input.GetValue().strip()))
		self.stop_button.Enable(False)
		self.cancel_button.Enable(True)
		self.attach_button.Enable(self._attachments_supported())
		self.remove_attachment_button.Enable(False)
		self.clear_attachments_button.Enable(bool(self.attachments))
		if self.structure_only_check is not None:
			self.structure_only_check.Enable(True)

		if cancelled:
			self.trace_text.AppendText(_("\nGeneration stopped. Partial output was not applied.\n"))
		elif error is not None:
			self.trace_text.AppendText(_("\nGeneration failed.\n"))
			wx.MessageBox(
				_("An error occurred while processing your request:\n{}").format(str(error)),
				_("Error"),
				wx.OK | wx.ICON_ERROR,
			)
		elif modified_code:
			self.code_text.SetValue(modified_code)
			self.insert_button.Enable(True)
			if model_json is not None:
				self.model_json = model_json
				if hasattr(self, "download_json_button"):
					self.download_json_button.Enable(True)
			if self.model_kind == "coupled":
				self._refresh_structure_preview()
				self._record_coupled_turn(modified_code)
			self.trace_text.AppendText(_("\nGeneration complete.\n"))
		else:
			self.trace_text.AppendText(_("\nNo code was generated.\n"))
			wx.MessageBox(
				_("No code was generated. Please try again with a different prompt."),
				_("No Result"),
				wx.OK | wx.ICON_WARNING,
			)

	def on_close(self, event):
		if self._generation_active and event.CanVeto():
			event.Veto()
			return
		event.Skip()

	def on_download_json(self, event):
		default_name = (
			"coupled_model.json"
			if self.model_kind == "coupled"
			else "atomic_model.json"
		)
		dlg = wx.FileDialog(
			self,
			message=_("Save file as..."),
			defaultFile=default_name,
			wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
		)

		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			try:
				with open(path, "w") as file:
					file.write(json.dumps(self.model_json, indent=2))

				wx.MessageBox(
					_("JSON file saved successfully!"), _("Success"), wx.OK | wx.ICON_INFORMATION
				)
			except Exception as e:
				wx.MessageBox(
					_("Error saving file:\n{}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR
				)

		dlg.Destroy()


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Coupled-model assistant reopening
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def edit_coupled_model_with_ai(block, parent=None):
	"""Reopen the coupled-model AI assistant stored in a model archive.

	The session saved in the ``.cmd`` archive of ``block`` is loaded, the
	coupled-model dialog is reopened with its conversation and structure, and
	the updated structure is applied to ``block`` when the user validates it.

	Args:
		block (ContainerBlock): Coupled model to modify.
		parent (wx.Window, optional): Parent window of the dialog.

	Returns:
		bool: True when a new structure was applied and saved.
	"""
	archive = str(getattr(block, "model_path", "") or "")

	if not AICoupledSession.is_archive(archive):
		wx.MessageBox(
			_("This coupled model is not a saved model archive:\n{}").format(
				archive or "-"
			),
			_("AI Coupled Model"),
			wx.OK | wx.ICON_INFORMATION,
		)
		return False

	session = AICoupledSession.load_latest_session(archive)

	if not session:
		wx.MessageBox(
			_("No AI session is stored in this model:\n{}").format(archive),
			_("AI Coupled Model"),
			wx.OK | wx.ICON_INFORMATION,
		)
		return False

	### generative AI must be selected in the Preferences
	if not getattr(builtins, "SELECTED_IA", ""):
		wx.MessageBox(
			_("Generative AI must be selected in the Preferences."),
			_("AI Coupled Model"),
			wx.OK | wx.ICON_INFORMATION,
		)
		return False

	### models available to compose the coupled model
	try:
		from CoupledStructure import build_model_catalog

		catalog = build_model_catalog()
	except Exception as error:
		catalog = []
		sys.stderr.write(f"Unable to build the model catalog: {error}\n")

	from AIAdapter import AdapterFactory

	adapter = AdapterFactory.get_adapter_instance(
		parent=None,
		params=getattr(builtins, "PARAMS_IA", {}),
	)

	model_name = session.get("model_name") or getattr(block, "label", "")

	dialog = AIPrompterDialog(
		parent,
		_("AI Coupled Model Assistant"),
		"",
		adapter,
		model_kind="coupled",
		model_name=model_name,
		inputs=getattr(block, "input", None),
		outputs=getattr(block, "output", None),
		catalog=catalog,
		archive_path=archive,
		session=session,
	)

	result = dialog.ShowModal()
	structure = dialog.coupled_model
	### the dialog stored the updated conversation in the archive
	session = dialog.session_data or session
	dialog.Destroy()

	if result != wx.ID_OK or not structure:
		return False

	from CoupledStructure import CoupledStructureError, apply_coupled_structure

	try:
		apply_coupled_structure(block, structure)
	except CoupledStructureError as error:
		message = _("The coupled model structure could not be applied:\n%s") % error
		sys.stderr.write(message + "\n")
		wx.MessageBox(message, _("Coupled model"), wx.OK | wx.ICON_ERROR)
		return False
	except Exception as error:
		message = _("Unexpected error while building the coupled model:\n%s") % error
		sys.stderr.write(message + "\n")
		wx.MessageBox(message, _("Coupled model"), wx.OK | wx.ICON_ERROR)
		return False

	### save the diagram (the AI session entries are preserved)
	if not block.SaveFile(archive):
		message = _("Error saving file %s") % os.path.basename(archive)
		sys.stderr.write(message + "\n")
		wx.MessageBox(message, _("Coupled model"), wx.OK | wx.ICON_ERROR)
		return False

	### store the applied structure (with the generated submodel code)
	session["structure"] = structure
	AICoupledSession.save_session(
		archive,
		session,
		session_id=session.get("session_id"),
	)

	canvas = getattr(block, "parent", None)

	if canvas is not None and hasattr(canvas, "Refresh"):
		canvas.Refresh()

	return True
