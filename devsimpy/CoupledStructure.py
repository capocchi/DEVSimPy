# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# CoupledStructure.py --- Build a coupled model from an AI description.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  12/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
# A DEVSimPy coupled model (a .cmd archive) stores its structure in the
# diagram (.dat): submodels, ports and couplings. This module validates the
# JSON structure proposed by the AI assistant and turns it into real diagram
# shapes (Block and ConnectionShape) so the generated model is usable.
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import ast
import builtins
import difflib
import json
import os
import pickle
import re
import sys
import zipfile

### Names accepted for the coupled model external ports in a connection
INPUT_REFERENCES = frozenset(("__input__", "$input", "input", "__in__", "in"))

OUTPUT_REFERENCES = frozenset(("__output__", "$output", "output", "__out__", "out"))

### Directories never scanned when building the model catalog
SKIP_DIRECTORIES = frozenset(
	(
		"__pycache__",
		".git",
		".hg",
		".svn",
		"node_modules",
	)
)

### Python files that never contain a DEVSimPy model class
SKIP_PYTHON_FILES = frozenset(
	(
		"__init__",
		"plugins",
		"steps",
		"environment",
		"strategies",
		"configuration",
		"sample",
		"Atomic",
		"Coupled",
	)
)

### Maximum number of models exposed to the AI
MAX_CATALOG_SIZE = 200

### How a submodel is obtained:
### - "existing": bind an existing catalog model (default);
### - "behavior": generate the atomic model from a behavior description;
### - "stub": generate an empty atomic model with the declared ports.
GENERATE_MODES = frozenset(("existing", "behavior", "stub"))

GENERATE_ALIASES = {
	"": "existing",
	"existing": "existing",
	"catalog": "existing",
	"generate": "behavior",
	"generated": "behavior",
	"ai": "behavior",
	"empty": "stub",
	"placeholder": "stub",
}

### Layout used when the AI does not provide coordinates
DEFAULT_X = 160
DEFAULT_Y = 80
DEFAULT_COLUMN_WIDTH = 180
DEFAULT_ROW_HEIGHT = 130
DEFAULT_COLUMNS = 3


class CoupledStructureError(ValueError):
	"""Raised when a coupled model structure is invalid."""


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# JSON helpers
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def parse_json_object(raw):
	"""Return the first JSON object found in an AI response.

	Providers often wrap JSON in markdown fences or add a short sentence
	around it, so the outermost braces are used when a direct parse fails.
	"""
	if not isinstance(raw, str) or not raw.strip():
		raise CoupledStructureError("The AI response is empty.")

	text = raw.strip()

	if text.startswith("```"):
		lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
		text = "\n".join(lines).strip()

	try:
		data = json.loads(text)
	except json.JSONDecodeError:
		start = text.find("{")
		end = text.rfind("}")
		if start < 0 or end <= start:
			raise CoupledStructureError(
				"The AI response does not contain a JSON object."
			) from None
		try:
			data = json.loads(text[start : end + 1])
		except json.JSONDecodeError as error:
			raise CoupledStructureError(
				f"The AI response is not valid JSON: {error}"
			) from error

	if not isinstance(data, dict):
		raise CoupledStructureError("The AI response must be a JSON object.")

	return data


def _first_value(mapping, keys, default=None):
	"""Return the first non-empty value among ``keys``."""
	for key in keys:
		if key in mapping:
			value = mapping[key]
			if value is not None and value != "":
				return value
	return default


def _as_int(value, default=0, minimum=0):
	"""Convert ``value`` to an int, clamped to ``minimum``."""
	try:
		value = int(value)
	except (TypeError, ValueError):
		return default

	return max(minimum, value)


def _as_float(value, default=None):
	"""Convert ``value`` to a float, or return ``default``."""
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _is_input_reference(reference):
	"""Return True when ``reference`` denotes the coupled model inputs."""
	return str(reference or "").strip().lower() in INPUT_REFERENCES


def _is_output_reference(reference):
	"""Return True when ``reference`` denotes the coupled model outputs."""
	return str(reference or "").strip().lower() in OUTPUT_REFERENCES


def _sanitize_identifier(value, fallback="GeneratedModel"):
	"""Return a valid Python identifier built from ``value``."""
	text = "".join(
		character if (character.isalnum() or character == "_") else "_"
		for character in str(value or "")
	)

	text = text.strip("_")

	if not text:
		text = fallback

	if text[0].isdigit():
		text = f"_{text}"

	return text


def generated_submodel_name(coupled_name, label):
	"""Return the class/archive stem used for a generated submodel."""
	return _sanitize_identifier(f"{coupled_name}_{label}", "GeneratedModel")


def _class_name_from_code(code):
	"""Return the first top-level class declared in ``code``."""
	try:
		tree = ast.parse(code)
	except (SyntaxError, ValueError):
		return None

	for node in tree.body:
		if isinstance(node, ast.ClassDef):
			return node.name

	return None


def _rename_class(code, old_name, new_name):
	"""Rename the class ``old_name`` to ``new_name`` in ``code``."""
	if not old_name or old_name == new_name:
		return code

	return re.sub(
		rf"\bclass\s+{re.escape(old_name)}\b",
		f"class {new_name}",
		code,
		count=1,
	)


def _normalize_generate_mode(raw_submodel):
	"""Return the validated ``generate`` mode of a raw submodel."""
	mode = str(raw_submodel.get("generate", "existing") or "existing").strip().lower()
	mode = GENERATE_ALIASES.get(mode, mode)

	if mode not in GENERATE_MODES:
		raise CoupledStructureError(
			f"Unknown generate mode '{mode}'. Use one of: "
			f"{', '.join(sorted(GENERATE_MODES))}."
		)

	return mode


def stub_atomic_code(class_name, inputs=1, outputs=1):
	"""Return a complete, empty atomic DEVSimPy model.

	The generated stub only declares the DEVS functions; its ports are
	created by DEVSimPy from the diagram metadata, as for any CodeBlock.
	"""
	class_name = _sanitize_identifier(class_name, "GeneratedModel")

	return f'''# -*- coding: utf-8 -*-

"""
 Name:                  {class_name}.py
 Model description:     Generated stub ({inputs} input(s), {outputs} output(s))
 Organization:          DEVSimPy
 License:               GPL v3.0
"""

### Specific import ------------------------------------------------------------
from DomainInterface import DomainBehavior
from DomainInterface.Object import Message

### Model class ----------------------------------------------------------------
class {class_name}(DomainBehavior):
	"""Empty atomic model generated for a coupled model submodel."""

	def __init__(self):
		"""Constructor."""
		DomainBehavior.__init__(self)

		self.initPhase("IDLE", INFINITY)

	@transition("external")
	def extTransition(self, *args):
		"""DEVS external transition function."""
		return self.getState()

	@handler("output")
	def outputFnc(self):
		"""DEVS output function."""
		if len(self.OPorts) > 0:
			self.poke(self.OPorts[0], Message(1, self.timeNext))
		return {{}}

	@transition("internal")
	def intTransition(self):
		"""DEVS internal transition function."""
		return self.getState()

	@handler("time_advance")
	def timeAdvance(self):
		"""DEVS time advance function."""
		return self.getSigma()

	def finish(self, msg):
		"""Function called just before the end of the simulation."""
		pass
'''


def atomic_submodel_prompt(submodel, coupled_name):
	"""Return the atomic-model prompt used to generate a submodel behavior."""
	label = str(submodel.get("label") or "Submodel").strip()
	class_name = generated_submodel_name(coupled_name, label)
	inputs = _as_int(submodel.get("inputs"), 1)
	outputs = _as_int(submodel.get("outputs"), 1)
	behavior = str(
		_first_value(
			submodel,
			("behavior", "behaviour", "specification", "description"),
			"",
		)
		or ""
	).strip()

	lines = [
		f"Create an atomic DEVSimPy model named '{class_name}'.",
		f"It has {inputs} input port(s) and {outputs} output port(s).",
	]

	if behavior:
		lines.append("")
		lines.append("Behavior to implement:")
		lines.append(behavior)

	lines.append("")
	lines.append(
		"The model is a submodel of the coupled model "
		f"'{coupled_name}'. Implement the behavior described above; do not "
		"create ports in the constructor because DEVSimPy creates them from "
		"the diagram metadata."
	)

	return "\n".join(lines)


def generate_submodel_code(
	submodel,
	coupled_name,
	adapter,
	on_token=None,
	stop_event=None,
):
	"""Generate the atomic source of a ``behavior`` submodel.

	The adapter is used twice, exactly like the atomic-model wizard: once to
	obtain the model specification (JSON) and once to generate the code.
	"""
	model_json = adapter.generate_model_json(
		atomic_submodel_prompt(submodel, coupled_name),
		on_token=on_token,
		stop_event=stop_event,
	)

	if stop_event is not None and stop_event.is_set():
		return ""

	if not isinstance(model_json, dict):
		raise TypeError(str(model_json))

	code = adapter.generate_model_code(
		model_json,
		on_token=on_token,
		stop_event=stop_event,
	)

	if stop_event is not None and stop_event.is_set():
		return ""

	return code



## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Model catalog
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _classify_python_model(path):
	"""Return ``(class_name, kind)`` for a DEVSimPy model file.

	The file is parsed (not imported) so scanning the library has no side
	effect on the running application.
	"""
	try:
		with open(path, "r", encoding="utf-8", errors="ignore") as stream:
			tree = ast.parse(stream.read(), filename=path)
	except (OSError, SyntaxError, ValueError):
		return None

	for node in ast.walk(tree):
		if not isinstance(node, ast.ClassDef):
			continue

		for base in node.bases:
			if isinstance(base, ast.Name):
				base_name = base.id
			elif isinstance(base, ast.Attribute):
				base_name = base.attr
			else:
				continue

			if base_name == "DomainBehavior":
				return node.name, "atomic"
			if base_name == "DomainStructure":
				return node.name, "coupled"

	return None


def _catalog_roots():
	"""Return the directories scanned to build the model catalog."""
	roots = []

	domain_path = getattr(builtins, "DOMAIN_PATH", None)
	if domain_path:
		roots.append(domain_path)

	try:
		from Utilities import getTopLevelWindow

		main_window = getTopLevelWindow()
		export_paths = getattr(main_window, "exportPathsList", None) or []
		for path in export_paths:
			if path and path not in roots:
				roots.append(path)
	except Exception:  # noqa: S110
		pass

	return [root for root in roots if root and os.path.isdir(root)]


def build_model_catalog(roots=None, limit=MAX_CATALOG_SIZE):
	"""Return the DEVSimPy models available to compose a coupled model.

	Each entry is a dict with ``name``, ``kind``, ``python_path``, ``archive``,
	``inputs`` and ``outputs``. Archives (.amd/.cmd) are resolved to the python
	entry they embed; plain .py files are classified by parsing their base
	class, so no model is imported.
	"""
	import ZipManager

	search_roots = roots if roots is not None else _catalog_roots()

	catalog = []
	seen_names = set()

	for root in search_roots:
		for dirpath, dirnames, filenames in os.walk(root):
			dirnames[:] = sorted(
				name for name in dirnames if name not in SKIP_DIRECTORIES
			)

			for filename in sorted(filenames):
				lower_name = filename.lower()
				stem = os.path.splitext(filename)[0]
				key = stem.lower()

				if key in seen_names:
					continue

				if lower_name.endswith((".amd", ".cmd")):
					archive = os.path.join(dirpath, filename)

					try:
						python_entry = ZipManager.getPythonModelFileName(archive)
					except Exception:  # noqa: S112
						continue

					if not python_entry:
						continue

					catalog.append(
						{
							"name": stem,
							"kind": "coupled"
							if lower_name.endswith(".cmd")
							else "atomic",
							"python_path": os.path.join(archive, python_entry),
							"archive": archive,
							"inputs": 1,
							"outputs": 1,
						}
					)
					seen_names.add(key)

				elif lower_name.endswith(".py") and stem not in SKIP_PYTHON_FILES:
					path = os.path.join(dirpath, filename)
					info = _classify_python_model(path)

					if info is None:
						continue

					class_name, kind = info
					catalog.append(
						{
							"name": stem,
							"model": class_name,
							"kind": kind,
							"python_path": path,
							"archive": "",
							"inputs": 1,
							"outputs": 1,
						}
					)
					seen_names.add(key)

				if len(catalog) >= limit:
					return catalog

	return catalog


def catalog_for_prompt(catalog):
	"""Return a compact, JSON-friendly view of the catalog for the AI."""
	return [
		{
			"name": entry.get("name"),
			"kind": entry.get("kind", "atomic"),
			"inputs": entry.get("inputs", 1),
			"outputs": entry.get("outputs", 1),
		}
		for entry in catalog or []
	]


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Prompt
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def coupled_system_prompt(catalog=None):
	"""Return the system prompt used to generate a coupled model structure."""
	available = json.dumps(
		catalog_for_prompt(catalog),
		indent=2,
		ensure_ascii=False,
	)

	return f"""You are an expert in DEVS coupled models built with DEVSimPy.

A DEVSimPy coupled model is a structure (DomainStructure) made of:
- submodels, each being either an existing DEVSimPy model from the catalog
  or an atomic model generated from a behavior description;
- the coupled model own input and output ports (0-based indices);
- internal couplings (submodel output -> submodel input);
- external input couplings (coupled model input -> submodel input);
- external output couplings (submodel output -> coupled model output).

Use the special names "__input__" and "__output__" as source/target to
reference the coupled model own ports. Port indices are 0-based.

Available models (JSON):
{available}

Rules:
1. Answer with a single JSON object and nothing else: no markdown, no
   explanation, no code fences.
2. Every submodel must declare how it is obtained with "generate":
   - "existing" (default): "model" must be one of the catalog names above.
     Use it when a catalog model already implements the requested behavior.
   - "behavior": the submodel does not exist in the catalog but its behavior
     is described in the request. Provide a precise "behavior" description
     (inputs, outputs, state, timing, message content). Do not provide a
     "model" name: the wizard generates the atomic model code from
     "behavior".
   - "stub": the submodel does not exist and no behavior is described.
     The wizard creates an empty atomic model with the declared ports.
3. Never bind a described behavior to an unrelated catalog model. When the
   request describes what a submodel does and no catalog model does exactly
   that, use "generate": "behavior" instead of the closest catalog model.
   Only use "stub" when the request gives no behavior at all.
4. A submodel label must be unique and should describe its role
   (for example "Generator1", "Queue1").
5. Port indices must stay inside the declared port counts.
6. Never connect a submodel output to one of its own inputs.
7. The coupled model "inputs" and "outputs" values must match the request.
8. Keep the model reasonable: at most 12 submodels.
9. "connections" may be empty when no coupling is needed.
10. The "inputs" and "outputs" values of a submodel are authoritative: they
    define its ports. A connection may only use a port that exists.
    - A submodel with "inputs": 0 must never be the target of a connection.
    - A submodel with "outputs": 0 must never be the source of a connection.
11. Several connections may target the same input port: DEVSimPy merges them
    in the port bag. Do not invent extra ports for that reason.
12. Re-read every connection before answering and check it against the
    "inputs"/"outputs" of its two endpoints.

Common mistake to avoid:
  {{"label": "Gen", "inputs": 0, "outputs": 1, ...}}
  {{"source": "__input__", "source_port": 0, "target": "Gen", "target_port": 0}}
This is invalid: Gen declares no input port, so nothing can be connected to it.

Another mistake to avoid: the request describes a "Formatter" that converts
tokens, but the catalog only contains an unrelated "Converter". Do not use
"Converter"; answer with:
  {{"label": "Formatter", "generate": "behavior", "behavior": "converts ...",
    "inputs": 1, "outputs": 1}}

Expected JSON shape:
{{
  "name": "CoupledModelName",
  "description": "short description",
  "inputs": 1,
  "outputs": 1,
  "submodels": [
    {{
      "label": "Generator1",
      "generate": "existing",
      "model": "Generator",
      "inputs": 0,
      "outputs": 1,
      "x": 160,
      "y": 80
    }},
    {{
      "label": "Formatter1",
      "generate": "behavior",
      "behavior": "receives a token and changes its shape according to its color",
      "inputs": 1,
      "outputs": 1,
      "x": 340,
      "y": 80
    }}
  ],
  "connections": [
    {{"source": "Generator1", "source_port": 0, "target": "Formatter1", "target_port": 0}},
    {{"source": "Formatter1", "source_port": 0, "target": "__output__", "target_port": 0}}
  ]
}}
"""


def coupled_user_prompt(
	prompt,
	model_name=None,
	inputs=None,
	outputs=None,
	previous_structure=None,
):
	"""Return the user prompt asking for a coupled model structure.

	When ``previous_structure`` is given, the assistant is asked to *update*
	the existing structure instead of creating a new one. The complete
	structure is still expected in the answer, so the result can be applied
	directly without merging a diff.
	"""
	revision = isinstance(previous_structure, dict) and bool(previous_structure)

	lines = [
		"Update the DEVSimPy coupled model structure below."
		if revision
		else "Create a DEVSimPy coupled model."
	]

	if model_name:
		lines.append(f"The model class name is '{model_name}'.")

	if inputs is not None:
		lines.append(f"It has {inputs} input port(s).")

	if outputs is not None:
		lines.append(f"It has {outputs} output port(s).")

	if revision:
		lines.append("")
		lines.append("Current coupled model structure (JSON):")
		lines.append(json.dumps(previous_structure, indent=2, ensure_ascii=False))

	lines.append("")
	lines.append("User request:")
	lines.append(str(prompt or "").strip() or "Build a simple coupled model.")

	if revision:
		lines.append("")
		lines.append(
			"Apply the request to the current structure and return the "
			"complete updated JSON object. Keep every submodel and connection "
			"that the request does not change, including their labels, ports, "
			"positions and generated code."
		)

	lines.append("")
	lines.append("Return only the JSON object described in the system message.")

	return "\n".join(lines)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Validation
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _catalog_index(catalog):
	"""Return a lookup table keyed by model name and class name."""
	index = {}

	for entry in catalog or []:
		for key in (entry.get("name"), entry.get("model")):
			if key:
				index.setdefault(str(key).strip().lower(), entry)

	return index


def _resolve_model_reference(reference, catalog_index):
	"""Return a catalog entry for ``reference`` or raise."""
	text = str(reference or "").strip()

	if not text:
		raise CoupledStructureError("A submodel has no model reference.")

	entry = catalog_index.get(text.lower())

	if entry is not None:
		return entry

	### The AI may return a direct path instead of a catalog name
	if os.path.exists(text):
		if text.lower().endswith((".amd", ".cmd")):
			import ZipManager

			python_entry = ZipManager.getPythonModelFileName(text)
			return {
				"name": os.path.splitext(os.path.basename(text))[0],
				"kind": "coupled" if text.lower().endswith(".cmd") else "atomic",
				"python_path": os.path.join(text, python_entry),
				"archive": text,
				"inputs": 1,
				"outputs": 1,
			}

		if text.lower().endswith((".py", ".pyc")):
			return {
				"name": os.path.splitext(os.path.basename(text))[0],
				"kind": "atomic",
				"python_path": text,
				"archive": "",
				"inputs": 1,
				"outputs": 1,
			}

	raise CoupledStructureError(
		f"Unknown model '{text}'. Use one of the catalog models: "
		f"{_suggestions(text, catalog_index)}."
	)


def _suggestions(reference, catalog_index):
	"""Return a short list of catalog names close to ``reference``."""
	names = sorted({entry.get("name", "") for entry in catalog_index.values()})
	matches = difflib.get_close_matches(reference, names, n=5, cutoff=0.4)

	if matches:
		return ", ".join(matches)

	return ", ".join(names[:5]) or "none"


def _check_connection(
	position,
	source,
	source_port,
	target,
	target_port,
	labels,
	structure_inputs,
	structure_outputs,
):
	"""Validate one connection.

	Returns:
		str | None: An error message when the connection is invalid, otherwise
		``None``. The message explains which port is missing and how to fix it.
	"""
	number = position + 1

	if _is_input_reference(source):
		if source_port >= structure_inputs:
			return (
				f"Connection #{number} uses coupled model input port {source_port} "
				f"but the structure declares {structure_inputs} input port(s). "
				f'Set "inputs" to at least {source_port + 1} or remove this connection.'
			)
	else:
		submodel = labels.get(str(source).strip().lower())

		if submodel is None:
			return f"Connection #{number} references unknown submodel '{source}'."

		if source_port >= submodel["outputs"]:
			return (
				f"Connection #{number} uses output port {source_port} of "
				f"'{submodel['label']}' but it declares {submodel['outputs']} "
				f'output port(s). Add the port to the submodel declaration '
				f'(e.g. "outputs": {source_port + 1}) or remove this connection.'
			)

	if _is_output_reference(target):
		if target_port >= structure_outputs:
			return (
				f"Connection #{number} uses coupled model output port {target_port} "
				f"but the structure declares {structure_outputs} output port(s). "
				f'Set "outputs" to at least {target_port + 1} or remove this connection.'
			)
	else:
		submodel = labels.get(str(target).strip().lower())

		if submodel is None:
			return f"Connection #{number} references unknown submodel '{target}'."

		if target_port >= submodel["inputs"]:
			return (
				f"Connection #{number} targets input port {target_port} of "
				f"'{submodel['label']}' but it declares {submodel['inputs']} "
				f'input port(s). Add the port to the submodel declaration '
				f'(e.g. "inputs": {target_port + 1}) or remove this connection.'
			)

	if (
		not _is_input_reference(source)
		and not _is_output_reference(target)
		and str(source).strip().lower() == str(target).strip().lower()
	):
		return (
			f"Connection #{number} creates a direct feedback on '{source}', "
			f"which DEVSimPy does not allow."
		)

	return None


def _connection_error_message(errors):
	"""Return one readable message for a list of invalid connections."""
	lines = ["The coupled model structure is invalid:"]
	lines.extend(f"  - {error}" for error in errors)
	lines.append(
		'Every connection must reference an existing port: a submodel with '
		'"inputs": 0 cannot receive a connection and a submodel with '
		'"outputs": 0 cannot send one.'
	)

	return "\n".join(lines)


def normalize_coupled_structure(
	data,
	catalog=None,
	name=None,
	inputs=None,
	outputs=None,
):
	"""Validate and normalize a coupled model structure.

	Args:
		data (dict): Structure returned by the AI.
		catalog (list): Models available for composition.
		name (str): Default coupled model name.
		inputs (int): Default number of input ports.
		outputs (int): Default number of output ports.

	Returns:
		dict: A normalized, JSON-serializable structure.

	Raises:
		CoupledStructureError: When the structure cannot be used.
	"""
	if not isinstance(data, dict):
		raise CoupledStructureError("The coupled model structure must be a dict.")

	catalog_index = _catalog_index(catalog)

	structure_name = str(
		_first_value(data, ("name", "label"), name or "CoupledModel")
	).strip()

	structure_inputs = _as_int(
		_first_value(data, ("inputs", "input_ports", "nb_inputs"), inputs),
		default=_as_int(inputs, 0),
	)
	structure_outputs = _as_int(
		_first_value(data, ("outputs", "output_ports", "nb_outputs"), outputs),
		default=_as_int(outputs, 0),
	)

	raw_submodels = _first_value(data, ("submodels", "models", "components"), [])

	if not isinstance(raw_submodels, list) or not raw_submodels:
		raise CoupledStructureError("The structure must declare at least one submodel.")

	submodels = []
	labels = {}

	for position, raw_submodel in enumerate(raw_submodels):
		if not isinstance(raw_submodel, dict):
			raise CoupledStructureError(
				f"Submodel #{position + 1} must be a JSON object."
			)

		label = str(
			_first_value(
				raw_submodel,
				("label", "name", "id"),
				f"Model{position + 1}",
			)
		).strip()

		if not label:
			raise CoupledStructureError(
				f"Submodel #{position + 1} has an empty label."
			)

		if label.lower() in labels:
			raise CoupledStructureError(f"Duplicate submodel label '{label}'.")

		reference = _first_value(
			raw_submodel,
			("model", "class", "python_file", "model_name", "type"),
		)
		generate_mode = _normalize_generate_mode(raw_submodel)
		behavior = str(
			_first_value(
				raw_submodel,
				("behavior", "behaviour", "specification", "description"),
				"",
			)
			or ""
		).strip()
		code = str(
			_first_value(
				raw_submodel,
				("code", "source", "python_code", "implementation"),
				"",
			)
			or ""
		).strip()

		if generate_mode == "existing":
			entry = _resolve_model_reference(reference, catalog_index)
		else:
			### A generated submodel must not be bound to a catalog model:
			### the wizard materialises it as a real atomic archive.
			entry = {
				"model": _sanitize_identifier(label),
				"python_path": None,
				"archive": "",
				"kind": "atomic",
				"inputs": 1,
				"outputs": 1,
			}

			if generate_mode == "behavior" and not behavior and not code:
				raise CoupledStructureError(
					f"Submodel '{label}' uses generate 'behavior' but has no "
					'"behavior" description or "code".'
				)

		if code:
			try:
				compile(code, f"{label}.py", "exec")
			except SyntaxError as error:
				raise CoupledStructureError(
					f"Submodel '{label}' has invalid generated code: {error}"
				) from error

			if _class_name_from_code(code) is None:
				raise CoupledStructureError(
					f"Submodel '{label}' generated code does not declare a class."
				)

		x = _as_float(raw_submodel.get("x"))
		y = _as_float(raw_submodel.get("y"))

		if x is None:
			x = DEFAULT_X + (position % DEFAULT_COLUMNS) * DEFAULT_COLUMN_WIDTH

		if y is None:
			y = DEFAULT_Y + (position // DEFAULT_COLUMNS) * DEFAULT_ROW_HEIGHT

		submodel = {
			"label": label,
			"model": entry.get("model") or entry.get("name"),
			"python_path": entry.get("python_path"),
			"archive": entry.get("archive", ""),
			"kind": entry.get("kind", "atomic"),
			"generate": generate_mode,
			"behavior": behavior,
			"code": code,
			"inputs": _as_int(
				_first_value(
					raw_submodel,
					("inputs", "input_ports", "nb_inputs"),
					entry.get("inputs", 1),
				),
				default=1,
			),
			"outputs": _as_int(
				_first_value(
					raw_submodel,
					("outputs", "output_ports", "nb_outputs"),
					entry.get("outputs", 1),
				),
				default=1,
			),
			"x": x,
			"y": y,
		}

		submodels.append(submodel)
		labels[label.lower()] = submodel

	raw_connections = _first_value(
		data,
		("connections", "couplings", "links"),
		[],
	)

	if not isinstance(raw_connections, list):
		raise CoupledStructureError("'connections' must be a JSON list.")

	connections = []
	connection_errors = []

	for position, raw_connection in enumerate(raw_connections):
		if not isinstance(raw_connection, dict):
			raise CoupledStructureError(
				f"Connection #{position + 1} must be a JSON object."
			)

		source = _first_value(
			raw_connection,
			("source", "from", "src", "output"),
		)
		target = _first_value(
			raw_connection,
			("target", "to", "dst", "input"),
		)

		if source is None or target is None:
			connection_errors.append(
				f"Connection #{position + 1} needs a source and a target."
			)
			continue

		source_port = _as_int(
			_first_value(
				raw_connection,
				("source_port", "from_port", "out_port", "port"),
				0,
			)
		)
		target_port = _as_int(
			_first_value(
				raw_connection,
				("target_port", "to_port", "in_port", "port"),
				0,
			)
		)

		error = _check_connection(
			position,
			source,
			source_port,
			target,
			target_port,
			labels,
			structure_inputs,
			structure_outputs,
		)

		if error:
			connection_errors.append(error)
			continue

		connections.append(
			{
				"source": str(source).strip(),
				"source_port": source_port,
				"target": str(target).strip(),
				"target_port": target_port,
			}
		)

	### Report every invalid connection at once instead of stopping at the first
	### one: AI answers often contain several inconsistencies.
	if connection_errors:
		raise CoupledStructureError(_connection_error_message(connection_errors))

	return {
		"name": structure_name,
		"description": str(data.get("description") or "").strip(),
		"inputs": structure_inputs,
		"outputs": structure_outputs,
		"submodels": submodels,
		"connections": connections,
	}


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Diagram construction
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _write_generated_archive(archive, python_entry, code, block=None):
	"""Write a generated atomic archive.

	When ``block`` is given, its diagram attributes are pickled into
	``DEVSimPyModel.dat`` so the generated ``.amd`` can be loaded later as a
	normal library model. Otherwise a placeholder is written.
	"""
	directory = os.path.dirname(archive)

	if directory:
		os.makedirs(directory, exist_ok=True)

	if block is None:
		payload = b"Call SaveFile method first!"
	else:
		from Mixins.Savable import PickledCollection

		payload = pickle.dumps(
			PickledCollection(block),
			protocol=pickle.HIGHEST_PROTOCOL,
		)

	with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
		zf.writestr(python_entry, code)
		zf.writestr("DEVSimPyModel.dat", payload)


def _prepare_generated_submodel(submodel, base_dir, coupled_stem):
	"""Materialise a generated submodel as ``<Coupled>_<Label>.amd``.

	The archive is written next to the coupled model, with a python entry
	named after the archive (as required by ``DumpZipFile.Load``).

	Returns:
		tuple: ``(archive, python_entry, code)``.
	"""
	label = submodel["label"]
	class_name = generated_submodel_name(coupled_stem, label)
	python_entry = f"{class_name}.py"
	archive = os.path.join(base_dir, f"{class_name}.amd")

	code = str(submodel.get("code") or "").strip()

	if code:
		### the AI class name is replaced by the deterministic archive name
		code = _rename_class(code, _class_name_from_code(code), class_name)
	else:
		### no code was generated (or the user removed it): use a stub
		code = stub_atomic_code(
			class_name,
			submodel.get("inputs", 1),
			submodel.get("outputs", 1),
		)

	try:
		compile(code, python_entry, "exec")
	except SyntaxError as error:
		raise CoupledStructureError(
			f"Submodel '{label}' generated code is not valid Python: {error}"
		) from error

	_write_generated_archive(archive, python_entry, code)

	submodel["python_path"] = os.path.join(archive, python_entry)
	submodel["archive"] = archive
	submodel["model"] = class_name

	return archive, python_entry, code


def _create_submodel(submodel):
	"""Create the graphical block of a submodel."""
	import Components

	label = submodel["label"]
	python_path = submodel.get("python_path")
	archive = submodel.get("archive") or ""

	if not python_path:
		raise CoupledStructureError(f"Submodel '{label}' has no python file.")

	### A coupled submodel must load its own .dat structure
	if archive.lower().endswith(".cmd") and os.path.exists(archive):
		block = Components.CMDComponent.Load(archive, label)

		if block is None:
			raise CoupledStructureError(
				f"Could not load coupled submodel '{label}' from {archive}."
			)

		return block

	block = Components.BlockFactory.CreateBlock(
		canvas=None,
		x=None,
		y=None,
		label=label,
		id=0,
		inputs=submodel.get("inputs", 1),
		outputs=submodel.get("outputs", 1),
		python_file=python_path,
		model_file=archive,
	)

	if not block:
		raise CoupledStructureError(
			f"Could not create submodel '{label}' from {python_path}."
		)

	return block


def apply_coupled_structure(container_block, structure):
	"""Populate ``container_block`` with the submodels and couplings.

	Args:
		container_block (ContainerBlock): Coupled model block to fill.
		structure (dict): Normalized structure (see
			:func:`normalize_coupled_structure`).

	Returns:
		tuple: ``(submodel_count, connection_count)``.

	Raises:
		CoupledStructureError: When the structure cannot be applied.
	"""
	if not isinstance(structure, dict):
		raise CoupledStructureError("No coupled model structure to apply.")

	from Container import Block, ConnectionShape, iPort, oPort

	input_ports = [
		shape for shape in container_block.GetShapeList() if isinstance(shape, iPort)
	]
	output_ports = [
		shape for shape in container_block.GetShapeList() if isinstance(shape, oPort)
	]

	### the port shapes are stored in diagram order; use their id for indexing
	input_ports.sort(key=lambda shape: getattr(shape, "id", 0))
	output_ports.sort(key=lambda shape: getattr(shape, "id", 0))

	structure_inputs = _as_int(structure.get("inputs"), 0)
	structure_outputs = _as_int(structure.get("outputs"), 0)

	if len(input_ports) < structure_inputs:
		raise CoupledStructureError(
			f"The coupled model has {len(input_ports)} input port shape(s) but "
			f"the structure needs {structure_inputs}."
		)

	if len(output_ports) < structure_outputs:
		raise CoupledStructureError(
			f"The coupled model has {len(output_ports)} output port shape(s) but "
			f"the structure needs {structure_outputs}."
		)

	### Make the operation idempotent: drop previous submodels and couplings
	remaining_shapes = []
	for shape in container_block.GetShapeList():
		if isinstance(shape, (Block, ConnectionShape)):
			continue
		remaining_shapes.append(shape)

	container_block.shapes = remaining_shapes
	container_block.nbCodeBlock = 0
	container_block.nbContainerBlock = 0
	container_block.deletedCodeBlockId = []
	container_block.deletedContainerBlockId = []

	blocks = {}

	### Generated submodels are stored next to the coupled model
	model_path = str(getattr(container_block, "model_path", "") or "")

	if model_path:
		base_dir = os.path.dirname(os.path.abspath(model_path))
		coupled_stem = os.path.splitext(os.path.basename(model_path))[0]
	else:
		base_dir = os.getcwd()
		coupled_stem = str(structure.get("name") or "Coupled")

	for submodel in structure.get("submodels") or []:
		generated = None

		if submodel.get("generate") in ("behavior", "stub"):
			generated = _prepare_generated_submodel(
				submodel,
				base_dir,
				coupled_stem,
			)

		block = _create_submodel(submodel)

		### replace the placeholder .dat by the real pickled diagram data
		if generated:
			archive, python_entry, code = generated
			_write_generated_archive(archive, python_entry, code, block)

		if hasattr(block, "move"):
			block.move(float(submodel.get("x", DEFAULT_X)), float(submodel.get("y", DEFAULT_Y)))

		container_block.AddShape(block)
		blocks[str(submodel["label"]).strip().lower()] = block

	for connection in structure.get("connections") or []:
		source_reference = str(connection.get("source", "")).strip()
		target_reference = str(connection.get("target", "")).strip()

		source_port = _as_int(connection.get("source_port"), 0)
		target_port = _as_int(connection.get("target_port"), 0)

		if _is_input_reference(source_reference):
			source_shape = input_ports[source_port]
		else:
			source_shape = blocks.get(source_reference.lower())

		if _is_output_reference(target_reference):
			target_shape = output_ports[target_port]
		else:
			target_shape = blocks.get(target_reference.lower())

		if source_shape is None or target_shape is None:
			raise CoupledStructureError(
				f"Cannot connect '{source_reference}' to '{target_reference}'."
			)

		### the real block may declare fewer ports than the AI structure
		if not _is_input_reference(source_reference) and source_port >= getattr(
			source_shape, "output", 1
		):
			raise CoupledStructureError(
				f"'{source_reference}' has no output port {source_port}."
			)

		if not _is_output_reference(target_reference) and target_port >= getattr(
			target_shape, "input", 1
		):
			raise CoupledStructureError(
				f"'{target_reference}' has no input port {target_port}."
			)

		connection_shape = ConnectionShape()
		connection_shape.setInput(source_shape, source_port)
		connection_shape.setOutput(target_shape, target_port)

		### initial endpoints, as done by ShapeCanvas.makeConnectionShape
		connection_shape.x[0], connection_shape.y[0] = source_shape.getPortXY(
			"output", source_port
		)
		connection_shape.x[1], connection_shape.y[1] = target_shape.getPortXY(
			"input", target_port
		)

		### Connections are drawn below the blocks (same order as the canvas)
		container_block.shapes.insert(0, connection_shape)

	container_block.modify = True

	sys.stdout.write(
		f"Coupled structure applied: {len(blocks)} submodel(s), "
		f"{len(structure.get('connections') or [])} connection(s).\n"
	)

	return len(blocks), len(structure.get("connections") or [])
