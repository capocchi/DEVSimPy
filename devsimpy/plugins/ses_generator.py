# -*- coding: utf-8 -*-  # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ses_generator.py --- Generate a System Entity Structure (SES) and a coupled
#                      DEVS model from a prompt and an optional ontology.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.1                                      last modified:  11/18/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
# The plug-in adds one entry ("Generate SES / AI model...") to the contextual
# menu of a coupled model block, to the contextual menu of the diagram of that
# block and to the contextual menu of a model diagram. The dialog asks for a
# natural-language request and, optionally, an ontology, generates a System
# Entity Structure (SES) that follows the SES toolbox of the CEA (Wismar
# University of Applied Sciences), then asks the AI to prune that SES into a
# coupled DEVS model. The SES tree uses the toolbox elements: entity nodes,
# aspect nodes (Dec), multiple-aspect nodes (MultiAspect) and specialization
# nodes (Spec), and enforces the SES axioms (alternating mode, strict
# hierarchy, uniformity, valid siblings, assigned variables).
# The result either fills the block the menu was opened on, or creates a new
# coupled model block in the diagram (its ports, submodels, couplings and
# archive are generated).
#
# The SES is stored in the model archive (ses.json) next to the diagram and
# the code, so moving the model also carries its SES: it is read back when the
# assistant is opened again on that model and re-embedded after every save.
# The final coupled model is displayed in a graphical view (the preview of the
# coupled-model AI assistant) and the steps of its generation are logged in a
# dedicated tab. The folder where the archive and the atomic models are
# written can be chosen in the assistant.
# The plug-in only uses the public helpers of the DEVSimPy modules; no other
# project file is modified (except the plug-in registry that lists this
# module).
#
# The AI model is chosen in the SES assistant and in the coupled-model AI
# assistant with the same chooser as the atomic-model AI assistant (the AI
# panel of the editor): the selection is stored in builtins.PARAMS_IA.
#
# Self-test (no graphical display needed):
#     python devsimpy/plugins/ses_generator.py
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import builtins
import gettext
import html
import json
import os
import re
import sys
import threading
import zipfile
from datetime import datetime
from xml.etree import ElementTree

### Allow running this file directly for the self-test: the plug-in is
### normally imported with the DEVSimPy package directory already on sys.path.
if __name__ == "__main__":
	_PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

	if _PACKAGE_DIR not in sys.path:
		sys.path.insert(0, _PACKAGE_DIR)

	### the self-test imports DEVSimPy modules that rely on the builtins set
	### by config.UpdateBuiltins (GUI_FLAG, DOMAIN_PATH...)
	from config import UpdateBuiltins

	UpdateBuiltins()

import wx

from CoupledStructurePreview import StructurePreviewPanel
from Utilities import load_and_resize_image

from PluginManager import PluginManager

_ = gettext.gettext

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Constants
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### Contextual menu label of the plug-in
MENU_LABEL = "Generate SES / AI model..."

### Entry of the chooser that creates a new coupled model block
NEW_MODEL_LABEL = "New coupled model..."

### Name used by the plug-in manager to enable/disable this plug-in
PLUGIN_NAME = __name__.rsplit(".", 1)[-1]

### ZIP entry holding the diagram of a model archive
MODEL_ENTRY = "DEVSimPyModel.dat"

### ZIP entry holding the SES of a model archive
SES_ENTRY = "ses.json"

### Position of a coupled model block created in a diagram
NEW_BLOCK_X = 160
NEW_BLOCK_Y = 80

### Version of the payload stored in SES_ENTRY
### 2: adds the PES and the answers of the interactive pruning
### 3: adds the output folder of the generated coupled model
SES_PAYLOAD_VERSION = 3

### State of a step of the generation log
STEP_PENDING = "pending"
STEP_RUNNING = "running"
STEP_DONE = "done"
STEP_FAILED = "failed"
STEP_SKIPPED = "skipped"

### Label and colour of each state of the generation log
STEP_APPEARANCE = {
	STEP_PENDING: ("Pending", (110, 110, 110)),
	STEP_RUNNING: ("Running...", (30, 90, 180)),
	STEP_DONE: ("Done", (30, 130, 70)),
	STEP_FAILED: ("Failed", (170, 40, 40)),
	STEP_SKIPPED: ("Skipped", (110, 110, 110)),
}

### Archives that can hold an SES
ARCHIVE_EXTENSIONS = (".amd", ".cmd")

### Folder chosen in the assistant, remembered for the next new model
_last_output_dir = ""

### Canonical marker of a multi-aspect (variable number of instances)
MULTI_ASPECT = "1..*"

MULTI_ASPECT_ALIASES = frozenset(
	("*", "1..*", "0..*", "n", "many", "multi", "multi-aspect", "1..n")
)

### Node kinds of the SES toolbox
### (https://www.cea-wismar.de/tbx/SES_Tbx/SES_Elements_Axioms.html)
ENTITY = "entity"
ASPECT = "aspect"
MULTI_ASPECT_KIND = "multi_aspect"
SPECIALIZATION = "specialization"

NODE_KINDS = (ENTITY, ASPECT, MULTI_ASPECT_KIND, SPECIALIZATION)

### Suffix that the SES toolbox appends to the descriptive nodes
NODE_SUFFIX = {
	ASPECT: "Dec",
	MULTI_ASPECT_KIND: "MultiAspect",
	SPECIALIZATION: "Spec",
}

### Icon of each node kind: letter and colour
NODE_ICON = {
	ENTITY: ("E", (47, 109, 181)),
	ASPECT: ("A", (46, 139, 87)),
	MULTI_ASPECT_KIND: ("M", (123, 79, 168)),
	SPECIALIZATION: ("S", (181, 101, 29)),
}

### Position of the icon of each node kind in the image list of the tree
NODE_IMAGE_INDEX = {kind: position for position, kind in enumerate(NODE_KINDS)}

### Meaning of each node kind, shown in the legend of the tree
NODE_TOOLTIP = {
	ENTITY: _("Entity: an object of the real or imagined world."),
	ASPECT: _("Aspect (Dec): decomposition of an entity into parts (AND)."),
	MULTI_ASPECT_KIND: _(
		"Multiple-aspect (MultiAspect): replication of one entity, with the "
		"variable and the range of the number of copies."
	),
	SPECIALIZATION: _("Specialization (Spec): taxonomy of an entity (XOR)."),
}

### Guards of the SES normalization
MAX_SES_ENTITIES = 200
MAX_SES_DEPTH = 12

### Variants above this count are reported as "many"
MAX_SES_VARIANTS = 1000000000

### Kinds of decision asked while the SES is pruned interactively
PRUNING_SPECIALIZATION = "specialization"
PRUNING_ASPECT = "aspect"
PRUNING_MULTIPLICITY = "multiplicity"

### Practical bound of a multiple-aspect whose SES range is unbounded
MAX_PES_INSTANCES = 100

### Number of instances proposed for an unbounded multiple-aspect
DEFAULT_PES_INSTANCES = 3

### Maximum number of atomic submodels described by one PES
MAX_PES_SUBMODELS = 200

### Number of ontology characters sent to the AI
MAX_ONTOLOGY_CHARS = 20000

### Keys accepted by the coupled model structure of the AI for the submodels,
### the port counts and the connections (same aliases as CoupledStructure)
SUB_MODEL_CONTAINER_KEYS = ("submodels", "models", "components")
SUB_MODEL_LABEL_KEYS = ("label", "name", "id")
PORT_INPUT_KEYS = ("inputs", "input_ports", "nb_inputs")
PORT_OUTPUT_KEYS = ("outputs", "output_ports", "nb_outputs")
CONNECTION_CONTAINER_KEYS = ("connections", "couplings", "links")
CONNECTION_SOURCE_KEYS = ("source", "from", "src", "output")
CONNECTION_TARGET_KEYS = ("target", "to", "dst", "input")
CONNECTION_SOURCE_PORT_KEYS = ("source_port", "from_port", "out_port", "port")
CONNECTION_TARGET_PORT_KEYS = ("target_port", "to_port", "in_port", "port")

### ``PARAMS_IA`` entry holding the model of each AI provider (same keys as
### the Preferences and as the model chooser of the atomic-model assistant)
MODEL_SETTING_KEYS = {
	"ChatGPT": "CHATGPT_MODEL",
	"Ollama": "OLLAMA_MODEL",
	"LM Studio": "LMSTUDIO_MODEL",
}

### Model used when the Preferences do not define one
MODEL_DEFAULT_NAMES = {
	"ChatGPT": "gpt-4.1-nano",
	"Ollama": "mistral",
	"LM Studio": "",
}

### Text files accepted as an ontology
ONTOLOGY_EXTENSIONS = (
	".json",
	".xml",
	".owl",
	".rdf",
	".xsd",
	".ttl",
	".nt",
	".n3",
	".txt",
	".md",
	".yaml",
	".yml",
	".csv",
)


class SESError(ValueError):
	"""Raised when a System Entity Structure is invalid."""


def _log(message):
	"""Write a plug-in message on the console."""
	sys.stdout.write(f"[SES] {message}\n")


def _head(text, limit=4000):
	"""Return at most ``limit`` characters of ``text``."""
	text = str(text or "")

	if len(text) <= limit:
		return text

	return text[:limit].rstrip() + "\n..."


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# SES normalization
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# SES normalization
#
# The model follows the System Entity Structure of the SES toolbox of the
# CEA, Wismar University of Applied Sciences:
#     https://www.cea-wismar.de/tbx/SES_Tbx/SES_Elements_Axioms.html
#
# An SES is a tree of *entity* nodes (real nodes) and *descriptive* nodes:
# aspect (Dec), multiple-aspect (MultiAspect) and specialization (Spec).
# Descriptive nodes only occur between entities (alternating mode), they
# carry entity children, and the tree obeys the SES axioms (strict
# hierarchy, uniformity, valid siblings, assigned variables).
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _as_text(value, default=""):
	"""Return ``value`` as a stripped string."""
	return str(value or "").strip() or default


def _strip_node_suffix(name):
	"""Return ``name`` without a trailing SES toolbox suffix.

	The toolbox writes descriptive nodes as ``physicalDec``, ``pageMultiAspect``
	or ``genreSpec``. The suffix is added by the viewer, so it is removed from
	the stored name to keep it unique and to avoid ``DecDec`` labels.
	"""
	text = str(name or "")

	for suffix in ("MultiAspect", "Dec", "Spec"):
		if len(text) > len(suffix) and text.lower().endswith(suffix.lower()):
			return text[: -len(suffix)]

	return text


def node_label(kind, name):
	"""Return the SES toolbox label of a descriptive node (``name`` + suffix)."""
	suffix = NODE_SUFFIX.get(kind, "")

	if not suffix or str(name).lower().endswith(suffix.lower()):
		return str(name)

	return f"{name}{suffix}"


def kind_label(kind):
	"""Return the human name of a node kind (used by the tree legend)."""
	return {
		ENTITY: _("Entity"),
		ASPECT: _("Aspect (Dec)"),
		MULTI_ASPECT_KIND: _("Multiple-aspect (MultiAspect)"),
		SPECIALIZATION: _("Specialization (Spec)"),
	}.get(kind, str(kind))


def _parse_multiplicity(value):
	"""Return the ``(minimum, maximum)`` of a multiplicity.

	``maximum`` is None when the multiplicity is unbounded. The accepted
	forms are ``1``, ``3``, ``"2..5"``, ``"1..*"``, ``"0..*"``, ``"*"``,
	``"n"`` and ``{"min": 1, "max": 5}``.
	"""
	if isinstance(value, bool):
		return 1, 1

	if isinstance(value, dict):
		minimum = _parse_multiplicity(value.get("min", value.get("minimum", 1)))[0]
		maximum = value.get("max", value.get("maximum"))

		if maximum is None or str(maximum).strip().lower() in ("*", "n", ""):
			return minimum, None

		return minimum, max(minimum, _parse_multiplicity(maximum)[0])

	if isinstance(value, int):
		number = max(0, value)
		return number, number

	text = str(1 if value is None else value).strip().lower().replace(" ", "")

	if not text:
		return 1, 1

	if text in MULTI_ASPECT_ALIASES:
		return (0 if text.startswith("0") else 1), None

	try:
		if ".." in text:
			low, _, high = text.partition("..")
			minimum = max(0, int(low)) if low else 0

			if high in ("", "*", "n"):
				return minimum, None

			return minimum, max(minimum, int(high))

		number = max(0, int(text))
	except ValueError as error:
		raise SESError(
			f"Invalid multiplicity '{value}': use 1, an integer greater than 1, "
			'a range like "2..5", or "1..*".'
		) from error

	return number, number


def _normalize_multiplicity(value):
	"""Return the multiplicity of a legacy aspect as an int or ``"1..*"``.

	Older SES payloads put a multiplicity on an aspect. The SES toolbox
	expresses a replication with a multiple-aspect node instead, so such an
	aspect is converted (see :func:`_normalize_aspect`).
	"""
	_, maximum = _parse_multiplicity(value)

	return MULTI_ASPECT if maximum is None else maximum


def _node_name(raw, fallback):
	"""Return the name of a descriptive node, without its toolbox suffix."""
	name = _as_text(
		raw.get("name") or raw.get("label") or raw.get("aspect") or raw.get("specialization")
	)

	return _strip_node_suffix(name) or fallback


def _child_entities(raw, path, depth, counter, names, ancestors):
	"""Normalize the entity children declared by a descriptive node."""
	entities = raw.get("entities")

	if entities is None:
		entities = raw.get("children") or raw.get("subentities") or []

	### the AI sometimes writes the single entity of an aspect with a
	### singular key, as it does for a multiple-aspect
	if not entities:
		for key in ("entity", "subentity", "child", "node"):
			value = raw.get(key)

			if isinstance(value, dict):
				entities = [value]
				break

	if not isinstance(entities, list) or not entities:
		raise SESError(f"{path} must declare at least one entity.")

	return [
		_normalize_entity(
			child,
			f"{path} > entity #{position + 1}",
			depth,
			counter,
			names,
			ancestors,
		)
		for position, child in enumerate(entities)
	]


def _normalize_entity(raw, path, depth, counter, names, ancestors=()):
	"""Validate and normalize one SES entity (recursive).

	``names`` holds the entity names already used in the SES (axiom of
	uniformity) and ``ancestors`` the names of the entities of the current
	path (axiom of strict hierarchy).
	"""
	if depth > MAX_SES_DEPTH:
		raise SESError(f"{path} is nested too deeply (maximum depth is {MAX_SES_DEPTH}).")

	if not isinstance(raw, dict):
		raise SESError(f"{path} must be a JSON object.")

	name = _as_text(raw.get("name") or raw.get("entity") or raw.get("label"))

	if not name:
		if path != "SES":
			raise SESError(f"{path} has no name.")
		name = "SES"

	key = name.lower()

	if key in ancestors:
		raise SESError(
			f"{path}: the entity '{name}' appears twice on the same path "
			"(axiom of strict hierarchy)."
		)

	if key in names:
		raise SESError(
			f"{path}: the entity '{name}' already appears in the SES "
			"(axiom of uniformity: an entity is declared only once)."
		)

	names[key] = name
	counter[0] += 1

	if counter[0] > MAX_SES_ENTITIES:
		raise SESError(f"The SES declares more than {MAX_SES_ENTITIES} entities.")

	entity = {
		"name": name,
		"description": _as_text(raw.get("description") or raw.get("desc")),
		"aspects": [],
		"multi_aspects": [],
		"specializations": [],
	}

	path_names = (*ancestors, key)

	### Aspect nodes (Dec): decomposition into parts (AND) -----------------
	raw_aspects = raw.get("aspects")

	if raw_aspects is None:
		raw_aspects = raw.get("aspect") or []

	if not isinstance(raw_aspects, list):
		raise SESError(f"{path}: 'aspects' must be a list.")

	seen = set()

	for position, raw_aspect in enumerate(raw_aspects):
		if not isinstance(raw_aspect, dict):
			raise SESError(f"{path} > aspect #{position + 1} must be a JSON object.")

		aspect = _normalize_aspect(
			raw_aspect,
			f"{path} > aspect #{position + 1}",
			depth + 1,
			counter,
			names,
			path_names,
			name if position == 0 else f"{name}{position + 1}",
		)
		node_key = (aspect["kind"], aspect["node"]["name"].lower())

		if node_key in seen:
			raise SESError(
				f"{path} has two {aspect['kind'].replace('_', '-')} nodes "
				f"named '{aspect['node']['name']}'."
			)

		seen.add(node_key)

		if aspect["kind"] == MULTI_ASPECT_KIND:
			entity["multi_aspects"].append(aspect["node"])
		else:
			entity["aspects"].append(aspect["node"])

	### Multiple-aspect nodes (MultiAspect): replication -------------------
	raw_multi = raw.get("multi_aspects")

	if raw_multi is None:
		raw_multi = (
			raw.get("multiAspects") or raw.get("multi-aspects") or raw.get("multiple_aspects") or []
		)

	if not isinstance(raw_multi, list):
		raise SESError(f"{path}: 'multi_aspects' must be a list.")

	for position, raw_node in enumerate(raw_multi):
		node = _normalize_multi_aspect(
			raw_node,
			f"{path} > multi-aspect #{position + 1}",
			depth + 1,
			counter,
			names,
			path_names,
			name if position == 0 else f"{name}{position + 1}",
		)
		node_key = (MULTI_ASPECT_KIND, node["name"].lower())

		if node_key in seen:
			raise SESError(f"{path} has two multiple-aspect nodes named '{node['name']}'.")

		seen.add(node_key)
		entity["multi_aspects"].append(node)

	### Specialization nodes (Spec): taxonomy (XOR) ------------------------
	raw_specializations = raw.get("specializations")

	if raw_specializations is None:
		raw_specializations = raw.get("specialization") or []

	if not isinstance(raw_specializations, list):
		raise SESError(f"{path}: 'specializations' must be a list.")

	### two accepted forms: a list of alternatives (one specialization
	### node) or a list of named specialization nodes
	nodes = raw_specializations

	if nodes and all(
		isinstance(item, dict) and "entities" not in item and "alternatives" not in item
		for item in nodes
	):
		nodes = [{"entities": raw_specializations}]

	for position, raw_node in enumerate(nodes):
		node = _normalize_specialization(
			raw_node,
			f"{path} > specialization #{position + 1}",
			depth + 1,
			counter,
			names,
			path_names,
			name if position == 0 else f"{name}{position + 1}",
		)
		node_key = (SPECIALIZATION, node["name"].lower())

		if node_key in seen:
			raise SESError(f"{path} has two specialization nodes named '{node['name']}'.")

		seen.add(node_key)
		entity["specializations"].append(node)

	return entity


def _normalize_aspect(raw, path, depth, counter, names, ancestors, default_name):
	"""Normalize an aspect node, or a legacy aspect carrying a multiplicity.

	Returns:
		dict: ``{"kind": ASPECT | MULTI_ASPECT_KIND, "node": {...}}``.
	"""
	name = _node_name(raw, default_name)
	entities = _child_entities(raw, f"{path} '{name}'", depth, counter, names, ancestors)
	minimum, maximum = _parse_multiplicity(raw.get("multiplicity", raw.get("cardinality", 1)))

	### a multiplicity on an aspect is a multiple-aspect in the SES toolbox:
	### the same entity is replicated instead of decomposed
	if (minimum, maximum) != (1, 1):
		if len(entities) != 1:
			raise SESError(
				f"{path} '{name}': a multiple-aspect replicates a single entity, "
				f"but {len(entities)} entities are declared with multiplicity "
				f"{raw.get('multiplicity')!r}. Use a plain aspect to decompose."
			)

		return {
			"kind": MULTI_ASPECT_KIND,
			"node": {
				"name": name,
				"variable": _as_text(
					raw.get("variable") or raw.get("numRep"),
					f"numRep_{name}",
				),
				"min": minimum,
				"max": maximum,
				"entity": entities[0],
			},
		}

	return {"kind": ASPECT, "node": {"name": name, "entities": entities}}


def _normalize_multi_aspect(raw, path, depth, counter, names, ancestors, default_name):
	"""Normalize a multiple-aspect node (replication of one entity)."""
	if not isinstance(raw, dict):
		raise SESError(f"{path} must be a JSON object.")

	name = _node_name(raw, default_name)
	raw_entity = raw.get("entity")

	if raw_entity is None:
		entities = raw.get("entities") or raw.get("children") or []

		if not isinstance(entities, list) or len(entities) != 1:
			raise SESError(f"{path} '{name}': a multiple-aspect replicates exactly one entity.")

		raw_entity = entities[0]

	if not isinstance(raw_entity, dict):
		raise SESError(f"{path} '{name}' must declare an entity.")

	child = _normalize_entity(
		raw_entity,
		f"{path} '{name}' > entity",
		depth,
		counter,
		names,
		ancestors,
	)

	if "min" in raw or "max" in raw:
		minimum = _parse_multiplicity(raw.get("min", 1))[0]
		maximum = raw.get("max")

		if maximum is None or str(maximum).strip().lower() in ("*", "n", ""):
			maximum = None
		else:
			maximum = max(minimum, _parse_multiplicity(maximum)[0])
	else:
		minimum, maximum = _parse_multiplicity(
			raw.get("multiplicity", raw.get("cardinality", MULTI_ASPECT))
		)

	return {
		"name": name,
		"variable": _as_text(raw.get("variable") or raw.get("numRep"), f"numRep_{name}"),
		"min": minimum,
		"max": maximum,
		"entity": child,
	}


def _normalize_specialization(raw, path, depth, counter, names, ancestors, default_name):
	"""Normalize a specialization node (XOR between the alternatives)."""
	if not isinstance(raw, dict):
		raise SESError(f"{path} must be a JSON object.")

	name = _node_name(raw, default_name)
	raw_entities = raw.get("entities")

	if raw_entities is None:
		raw_entities = raw.get("alternatives")

	if raw_entities is None:
		raise SESError(f"{path} '{name}' must declare its alternatives in 'entities'.")

	entities = _child_entities(
		{"entities": raw_entities},
		f"{path} '{name}'",
		depth,
		counter,
		names,
		ancestors,
	)

	if len(entities) < 2:
		raise SESError(f"{path} '{name}': a specialization must declare at least two alternatives.")

	return {"name": name, "entities": entities}


def normalize_ses(data):
	"""Validate and normalize a System Entity Structure.

	The normalized SES is a tree of entity nodes; each entity holds the three
	kinds of descriptive nodes of the SES toolbox:

	- ``aspects``: ``[{"name", "entities": [entity, ...]}]`` (``Dec``,
	  decomposition, AND);
	- ``multi_aspects``: ``[{"name", "variable", "min", "max", "entity"}]``
	  (``MultiAspect``, replication of one entity);
	- ``specializations``: ``[{"name", "entities": [entity, ...]}]``
	  (``Spec``, taxonomy, XOR).

	Args:
		data (dict): SES returned by the AI. A ``{"ses": {...}}`` wrapper is
			accepted, as well as the older aspect ``multiplicity`` form.

	Returns:
		dict: The normalized root entity.

	Raises:
		SESError: When the SES cannot be used (including when it breaks the
			SES axioms of uniformity or strict hierarchy).
	"""
	if not isinstance(data, dict):
		raise SESError("The System Entity Structure must be a JSON object.")

	raw = data["ses"] if isinstance(data.get("ses"), dict) else data

	return _normalize_entity(raw, "SES", 0, [0], {})


def _range_text(node):
	"""Return the value range of a multiple-aspect as ``min..max``."""
	minimum = node.get("min", 1)
	maximum = node.get("max")

	return f"{minimum}..*" if maximum is None else f"{minimum}..{maximum}"


def _entity_variants(entity, cap=MAX_SES_VARIANTS):
	"""Return the number of variants described by ``entity`` (capped)."""
	total = 1

	### several aspects under one entity are a decision node: the pruned
	### structure keeps exactly one of them
	aspects = entity.get("aspects") or []

	if aspects:
		subtotals = [_aspect_variants(aspect, cap) for aspect in aspects]
		total *= sum(subtotals) if len(subtotals) > 1 else subtotals[0]

	for node in entity.get("multi_aspects") or []:
		base = _entity_variants(node.get("entity") or {}, cap)
		minimum = int(node.get("min", 1))
		maximum = node.get("max")

		if maximum is None:
			return cap

		replicated = 0

		for count in range(minimum, int(maximum) + 1):
			replicated += base**count

			if replicated >= cap:
				return cap

		total *= replicated

	for node in entity.get("specializations") or []:
		alternatives = sum(_entity_variants(child, cap) for child in node.get("entities") or [])
		total *= alternatives

	return min(total, cap)


def _aspect_variants(aspect, cap=MAX_SES_VARIANTS):
	"""Return the number of variants of one aspect (product of its parts)."""
	total = 1

	for child in aspect.get("entities") or []:
		total *= _entity_variants(child, cap)

		if total >= cap:
			return cap

	return total


def ses_statistics(ses):
	"""Return the counts, the depth and the variants described by ``ses``.

	The counts follow the SES toolbox: entities are real nodes, aspects
	(``Dec``), multiple-aspects (``MultiAspect``) and specializations
	(``Spec``) are descriptive nodes. ``variants`` is the number of pruned
	entity structures (PES) the SES describes, or None when it exceeds
	``MAX_SES_VARIANTS`` or is unbounded.
	"""
	counts = {
		"entities": 0,
		"aspects": 0,
		"multi_aspects": 0,
		"specializations": 0,
		"alternatives": 0,
		"descriptive": 0,
		"decision_nodes": 0,
		"depth": 0,
		"variants": 1,
		"unbounded": False,
	}

	def walk(entity, depth):
		counts["entities"] += 1
		counts["depth"] = max(counts["depth"], depth)

		aspects = entity.get("aspects") or []
		multi_aspects = entity.get("multi_aspects") or []
		specializations = entity.get("specializations") or []

		counts["aspects"] += len(aspects)
		counts["multi_aspects"] += len(multi_aspects)
		counts["specializations"] += len(specializations)
		counts["descriptive"] += len(aspects) + len(multi_aspects) + len(specializations)
		counts["decision_nodes"] += max(0, len(aspects) - 1) + len(multi_aspects)

		for node in specializations:
			alternatives = len(node.get("entities") or [])
			counts["alternatives"] += alternatives

			if alternatives > 1:
				counts["decision_nodes"] += 1

		### the depth counts the descriptive nodes too, like the displayed tree
		for aspect in aspects:
			for child in aspect.get("entities") or []:
				walk(child, depth + 2)

		for node in multi_aspects:
			if node.get("max") is None:
				counts["unbounded"] = True

			walk(node.get("entity") or {}, depth + 2)

		for node in specializations:
			for child in node.get("entities") or []:
				walk(child, depth + 2)

	if isinstance(ses, dict):
		walk(ses, 0)
		variants = _entity_variants(ses)

		if counts["unbounded"] or variants >= MAX_SES_VARIANTS:
			counts["variants"] = None
		else:
			counts["variants"] = variants

	return counts


def ses_tree_nodes(ses):
	"""Return the nodes of the SES tree as nested dicts.

	Each node has ``kind`` (``entity``, ``aspect``, ``multi_aspect`` or
	``specialization``), ``name``, ``label``, ``detail``, ``badge`` and
	``children``. The labels follow the SES toolbox notation: the descriptive
	nodes carry the ``Dec``, ``MultiAspect`` and ``Spec`` suffixes.
	"""
	if not isinstance(ses, dict):
		return []

	def entity_node(entity):
		aspects = entity.get("aspects") or []
		multi_aspects = entity.get("multi_aspects") or []
		specializations = entity.get("specializations") or []

		badges = []

		if len(aspects) > 1:
			badges.append(f"decision: {len(aspects)} aspects")

		for node in specializations:
			alternatives = len(node.get("entities") or [])

			if alternatives > 1:
				badges.append(f"decision: {alternatives} alternatives")

		for node in multi_aspects:
			badges.append(f"decision: {node.get('variable')}")

		children = []

		for aspect in aspects:
			children.append(
				{
					"kind": ASPECT,
					"name": aspect["name"],
					"label": node_label(ASPECT, aspect["name"]),
					"detail": _(
						"Aspect (Dec): decomposition of '{parent}'. All its entities "
						"are parts of the parent; several aspects are a decision "
						"node (one is chosen when the SES is pruned)."
					).format(parent=entity["name"]),
					"badge": _("{count} part(s)").format(count=len(aspect.get("entities") or [])),
					"children": [entity_node(child) for child in aspect.get("entities") or []],
				}
			)

		for node in multi_aspects:
			child = node.get("entity") or {}
			children.append(
				{
					"kind": MULTI_ASPECT_KIND,
					"name": node["name"],
					"label": node_label(MULTI_ASPECT_KIND, node["name"]),
					"detail": _(
						"Multiple-aspect (MultiAspect): replication of '{child}' "
						"under '{parent}'. The replication variable '{variable}' "
						"takes a value in {value_range}; the number of instances is "
						"chosen when the SES is pruned."
					).format(
						child=child.get("name", "?"),
						parent=entity["name"],
						variable=node.get("variable"),
						value_range=_range_text(node),
					),
					"badge": "{variable} = {value_range}".format(
						variable=node.get("variable"),
						value_range=_range_text(node),
					),
					"children": [entity_node(child)],
				}
			)

		for node in specializations:
			alternatives = node.get("entities") or []
			children.append(
				{
					"kind": SPECIALIZATION,
					"name": node["name"],
					"label": node_label(SPECIALIZATION, node["name"]),
					"detail": _(
						"Specialization (Spec): taxonomy of '{parent}'. Exactly one "
						"of the alternatives is chosen when the SES is pruned:\n"
						"{alternatives}"
					).format(
						parent=entity["name"],
						alternatives="\n".join(
							f"  - {child.get('name', '?')}" for child in alternatives
						),
					),
					"badge": _("{count} alternative(s)").format(count=len(alternatives)),
					"children": [entity_node(child) for child in alternatives],
				}
			)

		return {
			"kind": ENTITY,
			"name": entity["name"],
			"label": entity["name"],
			"detail": entity.get("description", ""),
			"badge": ", ".join(badges),
			"children": children,
		}

	return [entity_node(ses)]


def ses_to_tree_rows(ses):
	"""Return the rows of the SES tree (pre-order, with their depth).

	Each row is a dict with ``depth``, ``kind``, ``label``, ``detail`` and
	``badge`` (see :func:`ses_tree_nodes`).
	"""
	rows = []

	def walk(node, depth):
		rows.append(
			{
				"depth": depth,
				"kind": node["kind"],
				"label": node["label"],
				"detail": node["detail"],
				"badge": node["badge"],
			}
		)

		for child in node["children"]:
			walk(child, depth + 1)

	for node in ses_tree_nodes(ses):
		walk(node, 0)

	return rows


def _tree_item_label(node):
	"""Return the label of a node of the SES tree (name followed by its badge)."""
	label = str(node.get("label") or node.get("name") or "")

	if node.get("badge"):
		return f"{label}  \u2014  {node['badge']}"

	return label


def tree_image_list():
	"""Return the image list shared by the SES and PES trees."""
	images = wx.ImageList(16, 16, True, len(NODE_KINDS))

	for kind in NODE_KINDS:
		images.Add(_node_bitmap(kind))

	return images


def fill_tree_ctrl(tree, nodes):
	"""Fill ``tree`` with the nodes of a SES/PES tree and return its root item."""
	tree.DeleteAllItems()

	if not nodes:
		return None

	def add(parent, node):
		image = NODE_IMAGE_INDEX.get(node["kind"], -1)
		label = _tree_item_label(node)

		if parent is None:
			item = tree.AddRoot(label, image, -1, node)
		else:
			item = tree.AppendItem(parent, label, image, -1, node)

		if node["kind"] == ENTITY:
			tree.SetItemBold(item, True)
		else:
			tree.SetItemTextColour(item, wx.Colour(*NODE_ICON[node["kind"]][1]))

		for child in node.get("children") or []:
			add(item, child)

		return item

	root = add(None, nodes[0])
	tree.ExpandAll()

	return root


def _node_bitmap(kind):
	"""Return the 16x16 icon drawn in the SES tree for ``kind``.

	The icon is a coloured square carrying the initial letter of the node
	kind (``E`` entity, ``A`` aspect, ``M`` multiple-aspect, ``S``
	specialization), which keeps the tree readable without an external
	image file.
	"""
	letter, colour = NODE_ICON.get(kind, ("?", (110, 110, 110)))
	bitmap = wx.Bitmap(16, 16)
	dc = wx.MemoryDC(bitmap)

	try:
		dc.SetBackground(wx.Brush(wx.Colour(*colour)))
		dc.Clear()
		dc.SetPen(wx.Pen(wx.Colour(*colour)))
		dc.SetBrush(wx.Brush(wx.Colour(*colour)))
		dc.DrawRectangle(0, 0, 16, 16)
		dc.SetTextForeground(wx.Colour(255, 255, 255))
		dc.SetFont(
			wx.Font(
				9,
				wx.FONTFAMILY_SWISS,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)
		width, height = dc.GetTextExtent(letter)
		dc.DrawText(letter, (16 - width) // 2, (16 - height) // 2)
	finally:
		dc.SelectObject(wx.NullBitmap)

	return bitmap


def _describe_node(node):
	"""Return the text shown when a node of the SES tree is selected."""
	if not isinstance(node, dict):
		return ""

	kind = node.get("kind", "")
	titles = {
		ENTITY: _("Entity"),
		ASPECT: _("Aspect node (Dec)"),
		MULTI_ASPECT_KIND: _("Multiple-aspect node (MultiAspect)"),
		SPECIALIZATION: _("Specialization node (Spec)"),
	}

	lines = [f"{titles.get(kind, kind)}: {node.get('label') or node.get('name')}"]

	if node.get("badge"):
		lines.append(str(node["badge"]))

	if node.get("detail"):
		lines.append("")
		lines.append(str(node["detail"]))

	if node.get("children"):
		lines.append("")
		lines.append(_("{count} child node(s).").format(count=len(node["children"])))

	return "\n".join(lines)


def ses_entity_names(ses):
	"""Return the names of the entities of ``ses`` in pre-order."""
	return [row["label"] for row in ses_to_tree_rows(ses) if row["kind"] == ENTITY]


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Interactive pruning (PES)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _clamp_instances(value, minimum, maximum):
	"""Return a valid number of instances for a multiple-aspect."""
	try:
		count = int(value)
	except (TypeError, ValueError):
		count = int(minimum)

	count = max(int(minimum), count)

	if maximum is None:
		return min(count, max(int(minimum), MAX_PES_INSTANCES))

	return min(count, max(int(minimum), int(maximum)))


def _decision_options(node):
	"""Return the alternatives declared by an aspect or specialization node."""
	return [
		{
			"name": str(entity.get("name") or ""),
			"description": str(entity.get("description") or ""),
		}
		for entity in node.get("entities") or []
		if isinstance(entity, dict)
	]


def _entity_decisions(entity, path, trail, answers, decisions):
	"""Collect the decisions of ``entity`` in pruning order.

	``path`` identifies the branch that leads to the entity (it is the key of
	its decisions), ``trail`` holds the names of the ancestors. A decision is
	always appended, even when it is answered: the session uses the plan to
	validate the answers and to count the progress. Recursion stops under an
	unanswered decision because the following questions depend on it.
	"""
	name = str(entity.get("name") or "")

	### Specializations: exactly one alternative per specialization node
	for index, node in enumerate(entity.get("specializations") or []):
		key = path + (("decision", PRUNING_SPECIALIZATION, index),)
		alternatives = node.get("entities") or []

		decisions.append(
			{
				"kind": PRUNING_SPECIALIZATION,
				"key": key,
				"path": path,
				"trail": tuple(trail) + (name,),
				"entity": name,
				"node": str(node.get("name") or ""),
				"options": _decision_options(node),
				"default": 0,
				"min": None,
				"max": None,
				"variable": "",
				"child": "",
			}
		)

		choice = answers.get(key)

		if choice is None:
			return

		try:
			choice = int(choice)
		except (TypeError, ValueError):
			choice = 0

		if not 0 <= choice < len(alternatives):
			choice = 0

		if alternatives:
			_entity_decisions(
				alternatives[choice],
				path + ((PRUNING_SPECIALIZATION, index, choice),),
				list(trail) + [name],
				answers,
				decisions,
			)

	### Aspects: one decomposition, chosen when several aspects are declared
	aspects = entity.get("aspects") or []

	if len(aspects) > 1:
		key = path + (("decision", PRUNING_ASPECT),)

		decisions.append(
			{
				"kind": PRUNING_ASPECT,
				"key": key,
				"path": path,
				"trail": tuple(trail) + (name,),
				"entity": name,
				"node": "",
				"options": [
					{
						"name": str(aspect.get("name") or ""),
						"description": _("{count} part(s)").format(
							count=len(aspect.get("entities") or [])
						),
					}
					for aspect in aspects
				],
				"default": 0,
				"min": None,
				"max": None,
				"variable": "",
				"child": "",
			}
		)

		choice = answers.get(key)

		if choice is None:
			return
	else:
		choice = 0 if aspects else None

	if aspects:
		try:
			choice = int(choice)
		except (TypeError, ValueError):
			choice = 0

		if not 0 <= choice < len(aspects):
			choice = 0

		for index, child in enumerate(aspects[choice].get("entities") or []):
			_entity_decisions(
				child,
				path + ((PRUNING_ASPECT, choice, index),),
				list(trail) + [name],
				answers,
				decisions,
			)

	### Multiple-aspects: one number of instances per node
	for index, node in enumerate(entity.get("multi_aspects") or []):
		key = path + (("decision", PRUNING_MULTIPLICITY, index),)
		minimum = int(node.get("min") or 0)
		maximum = node.get("max")
		child = node.get("entity") or {}

		decisions.append(
			{
				"kind": PRUNING_MULTIPLICITY,
				"key": key,
				"path": path,
				"trail": tuple(trail) + (name,),
				"entity": name,
				"node": str(node.get("name") or ""),
				"options": [],
				"default": minimum,
				"min": minimum,
				"max": maximum,
				"variable": str(node.get("variable") or ""),
				"child": str(child.get("name") or ""),
			}
		)

		count = answers.get(key)

		if count is None:
			continue

		### the structure of the copies is shared: its questions are asked once
		if _clamp_instances(count, minimum, maximum) > 0:
			_entity_decisions(
				child,
				path + ((PRUNING_MULTIPLICITY, index, 0),),
				list(trail) + [name],
				answers,
				decisions,
			)


def pruning_kind_label(kind):
	"""Return the readable name of a pruning decision kind."""
	return {
		PRUNING_SPECIALIZATION: _("specialization (choose one alternative)"),
		PRUNING_ASPECT: _("aspect (choose one decomposition)"),
		PRUNING_MULTIPLICITY: _("number of instances"),
	}.get(kind, str(kind))


class PruningSession:
	"""Track the answers that prune an SES into one PES.

	The session is independent of wxPython: it is used by the assistant
	dialog and by the self-test.
	"""

	def __init__(self, ses):
		self.ses = normalize_ses(ses)
		self.answers = {}
		self.history = []
		self._decisions = []
		self._plan()

	def _plan(self):
		"""Recompute the decisions reachable from the current answers."""
		self._decisions = []
		_entity_decisions(self.ses, (), (), self.answers, self._decisions)

	def decisions(self):
		"""Return every decision of the current plan (answered or not)."""
		return list(self._decisions)

	def decision(self, key):
		"""Return the decision identified by ``key``, or None."""
		for decision in self._decisions:
			if decision["key"] == key:
				return decision

		return None

	def pending(self):
		"""Return the decisions that are not answered yet."""
		return [decision for decision in self._decisions if decision["key"] not in self.answers]

	def next_decision(self):
		"""Return the first decision to ask, or None when the PES is ready."""
		pending = self.pending()

		return pending[0] if pending else None

	def is_complete(self):
		"""Return True when every reachable decision has been answered."""
		return not self.pending()

	def progress(self):
		"""Return ``(answered, known)`` decision counts."""
		answered = sum(1 for decision in self._decisions if decision["key"] in self.answers)

		return answered, len(self._decisions)

	def default_answer(self, decision):
		"""Return the default answer of ``decision`` (first option, min count)."""
		if decision["kind"] == PRUNING_MULTIPLICITY:
			return int(decision["min"] or 0)

		return 0

	def validate(self, decision, value):
		"""Return ``value`` validated for ``decision``.

		Raises:
			SESError: When the answer is outside the choices or the range.
		"""
		if decision["kind"] in (PRUNING_SPECIALIZATION, PRUNING_ASPECT):
			try:
				index = int(value)
			except (TypeError, ValueError) as error:
				raise SESError(_("Choose one of the proposed options.")) from error

			if not 0 <= index < len(decision["options"]):
				raise SESError(_("Choose one of the proposed options."))

			return index

		minimum = int(decision["min"] or 0)
		maximum = decision["max"]

		try:
			count = int(value)
		except (TypeError, ValueError) as error:
			raise SESError(_("The number of instances must be an integer.")) from error

		if count < minimum:
			raise SESError(_("At least {min} instance(s) are required.").format(min=minimum))

		if maximum is not None and count > int(maximum):
			raise SESError(
				_("At most {max} instance(s) are allowed by the SES.").format(max=int(maximum))
			)

		if count > MAX_PES_INSTANCES:
			raise SESError(
				_("At most {max} instances can be created.").format(max=MAX_PES_INSTANCES)
			)

		return count

	def answer(self, key, value):
		"""Store the answer of ``key`` and invalidate the answers it changes.

		Returns:
			bool: True when the plan changed.
		"""
		decision = self.decision(key)

		if decision is None:
			raise SESError(_("This decision is not part of the current pruning."))

		value = self.validate(decision, value)

		if key in self.answers and self.answers[key] == value:
			return False

		### a different answer changes the following branches: forget them
		if key in self.history:
			position = self.history.index(key)

			for later in self.history[position + 1 :]:
				self.answers.pop(later, None)

			del self.history[position + 1 :]

		self.answers[key] = value

		if key not in self.history:
			self.history.append(key)

		self._plan()

		return True

	def undo(self):
		"""Forget the last answer and return its key, or None."""
		if not self.history:
			return None

		key = self.history.pop()
		self.answers.pop(key, None)
		self._plan()

		return key

	def partial_pes(self):
		"""Return the PES of the answered decisions (unanswered ones omitted)."""
		return _build_pes(self.ses, (), self.answers, partial=True)

	def pes(self):
		"""Return the PES described by every answer.

		Raises:
			SESError: When a decision is still unanswered.
		"""
		if not self.is_complete():
			raise SESError(_("Every decision must be answered before the PES is built."))

		return _build_pes(self.ses, (), self.answers, partial=False)


def pruning_answers(session):
	"""Return the answers of ``session`` as a JSON-serializable list.

	The decisions are stored in the order they were answered, because an
	answer can reveal (or hide) the decisions that follow it.
	"""
	if session is None:
		return []

	return [
		{
			"key": [list(part) if isinstance(part, tuple) else part for part in key],
			"value": session.answers[key],
		}
		for key in session.history
		if key in session.answers
	]


def _answer_key(raw):
	"""Return the hashable decision key stored in a payload."""
	if not isinstance(raw, (list, tuple)):
		raise SESError(_("Invalid pruning answer."))

	key = []

	for part in raw:
		if isinstance(part, (list, tuple)):
			key.append(tuple(part))
		else:
			key.append(part)

	return tuple(key)


def restore_pruning_session(ses, entries):
	"""Return a :class:`PruningSession` replaying the stored answers."""
	session = PruningSession(ses)

	if not isinstance(entries, (list, tuple)):
		return session

	for entry in entries:
		if not isinstance(entry, dict):
			continue

		try:
			session.answer(_answer_key(entry.get("key")), entry.get("value"))
		except (SESError, TypeError, ValueError):
			### the SES changed since the answers were stored: stop there
			break

	return session


def _build_pes(entity, path, answers, partial):
	"""Return the pruned entity structure of ``entity``.

	The PES only keeps entities and multiple-aspects: an aspect is an AND
	decomposition, so its entities become direct children, and the chosen
	specialization alternative becomes an entity child. In ``partial`` mode
	the unanswered branches are omitted and the nodes that still need a
	decision are flagged with ``pending``.
	"""
	node = {
		"kind": ENTITY,
		"name": str(entity.get("name") or ""),
		"description": str(entity.get("description") or ""),
		"pending": False,
		"children": [],
	}

	for index, specialization in enumerate(entity.get("specializations") or []):
		key = path + (("decision", PRUNING_SPECIALIZATION, index),)
		alternatives = specialization.get("entities") or []
		choice = answers.get(key)

		if choice is None:
			if partial:
				node["pending"] = True
				continue

			choice = 0

		try:
			choice = int(choice)
		except (TypeError, ValueError):
			choice = 0

		if not 0 <= choice < len(alternatives):
			choice = 0

		if alternatives:
			node["children"].append(
				_build_pes(
					alternatives[choice],
					path + ((PRUNING_SPECIALIZATION, index, choice),),
					answers,
					partial,
				)
			)

	aspects = entity.get("aspects") or []

	if aspects:
		if len(aspects) > 1:
			key = path + (("decision", PRUNING_ASPECT),)
			choice = answers.get(key)
		else:
			choice = 0

		if choice is None:
			if partial:
				node["pending"] = True
			else:
				choice = 0

		if choice is not None:
			try:
				choice = int(choice)
			except (TypeError, ValueError):
				choice = 0

			if not 0 <= choice < len(aspects):
				choice = 0

			for index, child in enumerate(aspects[choice].get("entities") or []):
				node["children"].append(
					_build_pes(
						child,
						path + ((PRUNING_ASPECT, choice, index),),
						answers,
						partial,
					)
				)

	for index, multiple in enumerate(entity.get("multi_aspects") or []):
		key = path + (("decision", PRUNING_MULTIPLICITY, index),)
		minimum = int(multiple.get("min") or 0)
		maximum = multiple.get("max")
		child = multiple.get("entity") or {}
		count = answers.get(key)
		pending = count is None

		if pending:
			### the default count is shown until the user chooses
			count = minimum
		else:
			count = _clamp_instances(count, minimum, maximum)

		node["children"].append(
			{
				"kind": MULTI_ASPECT_KIND,
				"name": str(multiple.get("name") or ""),
				"variable": str(multiple.get("variable") or ""),
				"min": minimum if pending else count,
				"max": maximum if pending else count,
				"count": count,
				"pending": pending and partial,
				"entity": _build_pes(
					child,
					path + ((PRUNING_MULTIPLICITY, index, 0),),
					answers,
					partial,
				),
			}
		)

	return node


def pes_statistics(pes):
	"""Return the counts displayed above the PES tree."""
	counts = {
		"entities": 0,
		"leaves": 0,
		"multi_aspects": 0,
		"instances": 0,
		"depth": 0,
		"submodels": 0,
	}

	def walk(node, depth):
		if not isinstance(node, dict):
			return

		counts["depth"] = max(counts["depth"], depth)

		if node.get("kind") == MULTI_ASPECT_KIND:
			counts["multi_aspects"] += 1
			counts["instances"] += int(node.get("count", node.get("max") or 0) or 0)
			walk(node.get("entity") or {}, depth + 1)
			return

		counts["entities"] += 1
		children = [child for child in node.get("children") or [] if isinstance(child, dict)]

		if not children:
			counts["leaves"] += 1

		for child in children:
			walk(child, depth + 1)

	if isinstance(pes, dict):
		walk(pes, 0)

		try:
			counts["submodels"] = len(pes_submodels(pes))
		except SESError:
			counts["submodels"] = MAX_PES_SUBMODELS + 1

	return counts


def pes_submodels(pes, limit=MAX_PES_SUBMODELS):
	"""Return the atomic submodels described by ``pes``.

	The coupled model is flat: an entity that has a decomposition is
	traversed and only its leaves become submodels. A multiple-aspect is
	expanded into one copy per instance, labelled ``Entity1``, ``Entity2``...
	"""
	if not isinstance(pes, dict):
		return []

	submodels = []
	used = set()

	def unique(base):
		name = _identifier(base, "Model")
		candidate = name
		index = 2

		while candidate.lower() in used:
			candidate = f"{name}{index}"
			index += 1

		used.add(candidate.lower())

		return candidate

	def walk_entity(entity, ancestors, suffix):
		children = [child for child in entity.get("children") or [] if isinstance(child, dict)]

		if not children:
			name = str(entity.get("name") or "Model")
			submodels.append(
				{
					"label": unique(name + suffix),
					"entity": name,
					"description": str(entity.get("description") or ""),
					"path": list(ancestors) + [name],
				}
			)

			if len(submodels) > limit:
				raise SESError(
					_("The PES describes more than {count} atomic submodels.").format(count=limit)
				)

			return

		for child in children:
			walk(child, list(ancestors) + [str(entity.get("name") or "")], suffix)

	def walk(node, ancestors, suffix):
		if not isinstance(node, dict):
			return

		if node.get("kind") == MULTI_ASPECT_KIND:
			count = int(node.get("count", node.get("max") or 0) or 0)
			child = node.get("entity") or {}

			for instance in range(count):
				walk_entity(
					child,
					ancestors,
					suffix + (str(instance + 1) if count > 1 else ""),
				)

			return

		walk_entity(node, ancestors, suffix)

	for child in pes.get("children") or []:
		walk(child, [str(pes.get("name") or "")], "")

	return submodels


def pes_preview_structure(pes, name="", description=""):
	"""Return a coupled structure preview of the submodels of ``pes``.

	The couplings are not known before the AI proposes them: the preview
	shows the atomic submodels fixed by the PES, so the user sees the shape
	of the coupled model that is about to be generated.
	"""
	submodels = []

	for entry in pes_submodels(pes):
		submodels.append(
			{
				"label": entry["label"],
				"model": entry["entity"],
				"entity": entry["entity"],
				"description": entry.get("description", ""),
				"generate": "existing",
				"inputs": 0,
				"outputs": 0,
			}
		)

	return {
		"name": str(name or (pes.get("name") if isinstance(pes, dict) else "") or "CoupledModel"),
		"description": str(description or ""),
		"inputs": 0,
		"outputs": 0,
		"submodels": submodels,
		"connections": [],
	}


def pes_tree_nodes(pes):
	"""Return the nodes of the PES tree as nested dicts.

	The nodes use the same shape as :func:`ses_tree_nodes`, so the tree view
	of the assistant displays a PES with the same icons and details.
	"""
	if not isinstance(pes, dict):
		return []

	def entity_node(entity):
		children = [
			child_node(child) for child in entity.get("children") or [] if isinstance(child, dict)
		]
		leaf = not children
		badges = []

		if entity.get("pending"):
			badges.append(_("decision pending"))

		badges.append(
			_("atomic model") if leaf else _("{count} part(s)").format(count=len(children))
		)

		detail = str(entity.get("description") or "")

		if not detail:
			detail = (
				_("Leaf entity: it becomes an atomic submodel of the coupled model.")
				if leaf
				else _("Entity with a decomposition: the coupled model is built from its leaves.")
			)

		return {
			"kind": ENTITY,
			"name": str(entity.get("name") or ""),
			"label": str(entity.get("name") or ""),
			"detail": detail,
			"badge": ", ".join(badges),
			"children": children,
		}

	def child_node(node):
		if node.get("kind") != MULTI_ASPECT_KIND:
			return entity_node(node)

		count = int(node.get("count", node.get("max") or 0) or 0)
		pending = bool(node.get("pending"))
		maximum = node.get("max")

		if pending:
			range_text = "{min}..{max}".format(
				min=node.get("min"),
				max=maximum if maximum is not None else "*",
			)
			badge = "{variable} = ? ({range})".format(
				variable=node.get("variable"),
				range=range_text,
			)
			detail = _(
				"Multiple-aspect (MultiAspect) '{name}': the number of instances "
				"of '{child}' is not chosen yet. The SES allows {range}."
			).format(
				name=node.get("name"),
				child=(node.get("entity") or {}).get("name", "?"),
				range=range_text,
			)
		else:
			badge = "{variable} = {count}".format(
				variable=node.get("variable"),
				count=count,
			)
			detail = _(
				"Multiple-aspect (MultiAspect) '{name}': '{child}' is replicated "
				"{count} time(s) in the pruned structure."
			).format(
				name=node.get("name"),
				child=(node.get("entity") or {}).get("name", "?"),
				count=count,
			)

		return {
			"kind": MULTI_ASPECT_KIND,
			"name": str(node.get("name") or ""),
			"label": node_label(MULTI_ASPECT_KIND, node.get("name") or ""),
			"detail": detail,
			"badge": badge,
			"children": [entity_node(node.get("entity") or {})],
		}

	return [entity_node(pes)]


def pes_to_tree_rows(pes):
	"""Return the rows of the PES tree (pre-order, with their depth)."""
	rows = []

	def walk(node, depth):
		rows.append(
			{
				"depth": depth,
				"kind": node["kind"],
				"label": node["label"],
				"detail": node["detail"],
				"badge": node["badge"],
			}
		)

		for child in node["children"]:
			walk(child, depth + 1)

	for node in pes_tree_nodes(pes):
		walk(node, 0)

	return rows


def pruning_question_text(decision):
	"""Return the deterministic question of ``decision``.

	It is displayed immediately and replaced by the AI wording when the
	provider answers (see :func:`pruning_question_prompt`).
	"""
	if decision["kind"] == PRUNING_SPECIALIZATION:
		return _("'{entity}' is specialized by '{node}'. Which alternative do you choose?").format(
			entity=decision["entity"], node=decision["node"]
		)

	if decision["kind"] == PRUNING_ASPECT:
		return _(
			"'{entity}' can be decomposed in {count} ways. Which aspect do you choose?"
		).format(entity=decision["entity"], count=len(decision["options"]))

	return _(
		"How many instances of '{child}' do you need for '{variable}' under '{entity}'?"
	).format(
		child=decision.get("child") or "?",
		variable=decision.get("variable") or "?",
		entity=decision["entity"],
	)


def pruning_question_hint(decision):
	"""Return the deterministic hint of ``decision``."""
	if decision["kind"] == PRUNING_MULTIPLICITY:
		maximum = decision.get("max")

		return _(
			"The SES allows between {min} and {max} instance(s); the structure "
			"of every instance is the same."
		).format(
			min=decision.get("min"),
			max=maximum if maximum is not None else "*",
		)

	return _("Every alternative describes a different structure of '{entity}'.").format(
		entity=decision["entity"]
	)


def pes_coupled_prompt(
	prompt,
	pes,
	submodels,
	model_name=None,
	inputs=None,
	outputs=None,
):
	"""Return the prompt asking for the couplings of the PES submodels."""
	lines = [
		(
			"Create a DEVSimPy coupled model from the pruned entity structure "
			"(PES) below. The user has already pruned the SES: the submodels are "
			"fixed."
		),
		"",
		"PES (JSON):",
		json.dumps(pes, indent=2, ensure_ascii=False),
		"",
		"Atomic submodels (fixed labels):",
	]

	for entry in submodels:
		description = str(entry.get("description") or "").strip()
		lines.append(
			f"- {entry['label']} (entity '{entry['entity']}')"
			+ (f": {description}" if description else "")
		)

	lines += [
		"",
		"Rules:",
		"- Declare exactly these submodel labels, with the same spelling.",
		(
			"- Every submodel is generated by DEVSimPy from its behavior: do not "
			"bind it to an existing model."
		),
		(
			"- Give each submodel its input/output port counts and, in "
			"'behavior', a precise description of its DEVS behavior."
		),
		(
			"- Declare the coupled model 'inputs' and 'outputs' and the "
			"'connections' (submodel labels, or 'input'/'output' for the "
			"coupled model ports)."
		),
		"- Use port index 0 for the first port.",
	]

	if model_name:
		lines += ["", f"Coupled model name: {model_name}"]

	if inputs is not None:
		lines.append(f"Number of input ports: {inputs}")

	if outputs is not None:
		lines.append(f"Number of output ports: {outputs}")

	lines += [
		"",
		"User request:",
		str(prompt or "").strip() or "Build the coupled model described by the PES.",
		"",
		"Return only the JSON object described in the system message.",
	]

	return "\n".join(lines)


def merge_pes_structure(structure, submodels):
	"""Restrict an AI coupled structure to the submodels of the PES.

	The labels, the order and the behavior of the submodels come from the
	PES; the AI only contributes the port counts and the couplings. The
	connections that reference a dropped submodel or an out-of-range port are
	removed, so the structure always applies to the diagram.
	"""
	from CoupledStructure import INPUT_REFERENCES, OUTPUT_REFERENCES

	by_label = {
		str(submodel.get("label") or "").strip().lower(): submodel
		for submodel in structure.get("submodels") or []
		if isinstance(submodel, dict)
	}

	merged = []

	for entry in submodels:
		source = by_label.get(entry["label"].lower()) or {}
		behavior = str(source.get("behavior") or "").strip()

		if not behavior:
			behavior = str(entry.get("description") or "").strip() or _(
				"Atomic model '{name}' of the pruned entity structure."
			).format(name=entry["entity"])

		inputs = source.get("inputs")
		outputs = source.get("outputs")

		merged.append(
			{
				"label": entry["label"],
				"model": str(source.get("model") or entry["label"]),
				"python_path": source.get("python_path"),
				"archive": str(source.get("archive") or ""),
				"kind": "atomic",
				"generate": "behavior",
				"behavior": behavior,
				"code": str(source.get("code") or "").strip(),
				"inputs": 1 if inputs is None else max(0, int(inputs)),
				"outputs": 1 if outputs is None else max(0, int(outputs)),
				"x": source.get("x"),
				"y": source.get("y"),
			}
		)

	labels = {submodel["label"].lower(): submodel for submodel in merged}
	structure_inputs = max(0, int(structure.get("inputs") or 0))
	structure_outputs = max(0, int(structure.get("outputs") or 0))
	connections = []

	for connection in structure.get("connections") or []:
		if not isinstance(connection, dict):
			continue

		source = str(connection.get("source") or "").strip()
		target = str(connection.get("target") or "").strip()
		source_port = max(0, int(connection.get("source_port") or 0))
		target_port = max(0, int(connection.get("target_port") or 0))
		source_key = source.lower()
		target_key = target.lower()

		if source_key in INPUT_REFERENCES:
			if source_port >= structure_inputs:
				continue
		else:
			model = labels.get(source_key)

			if model is None or source_port >= model["outputs"]:
				continue

		if target_key in OUTPUT_REFERENCES:
			if target_port >= structure_outputs:
				continue
		else:
			model = labels.get(target_key)

			if model is None or target_port >= model["inputs"]:
				continue

		### DEVSimPy does not allow a direct feedback on the same block
		if source_key == target_key:
			continue

		connections.append(
			{
				"source": source,
				"source_port": source_port,
				"target": target,
				"target_port": target_port,
			}
		)

	return {
		"name": structure.get("name"),
		"description": str(structure.get("description") or ""),
		"inputs": structure_inputs,
		"outputs": structure_outputs,
		"submodels": merged,
		"connections": connections,
	}


def restrict_to_pes(structure, submodels):
	"""Restrict the answer of the AI to the submodels fixed by the PES.

	The PES decides which atomic models exist and how they are obtained, so the
	answer is limited to its labels before it is validated: a stray label, or a
	submodel bound to a catalog model, would make the whole answer invalid even
	though it is dropped by :func:`merge_pes_structure` afterwards. The
	submodels are always generated (``generate`` is ``behavior``) and their
	behavior defaults to the description of the entity. A submodel the AI forgot
	is kept with one input and one output port, because the PES requires it.

	``structure`` is the raw answer of the AI, modified in place and returned.
	"""
	if not isinstance(structure, dict):
		return structure

	from CoupledStructure import INPUT_REFERENCES, OUTPUT_REFERENCES

	entries = {
		str(entry.get("label") or "").strip().lower(): entry
		for entry in submodels or []
		if isinstance(entry, dict)
	}

	raw_submodels = _first_entry_value(structure, SUB_MODEL_CONTAINER_KEYS, [])

	if not isinstance(raw_submodels, list):
		raw_submodels = []

	def label_of(entry):
		return str(_first_entry_value(entry, SUB_MODEL_LABEL_KEYS, "") or "").strip()

	kept = []
	kept_labels = set()

	for entry in raw_submodels:
		if not isinstance(entry, dict):
			continue

		label = label_of(entry).lower()

		if label not in entries or label in kept_labels:
			continue

		kept.append(entry)
		kept_labels.add(label)

	### a submodel the AI forgot is still created by the PES
	for label, entry in entries.items():
		if label in kept_labels:
			continue

		kept.append({"label": entry["label"], "inputs": 1, "outputs": 1})
		kept_labels.add(label)

	for entry in kept:
		entry["generate"] = "behavior"

		behavior = str(
			_first_entry_value(
				entry,
				("behavior", "behaviour", "specification", "description"),
				"",
			)
			or ""
		).strip()

		if not behavior:
			entity = entries[label_of(entry).lower()]
			behavior = str(entity.get("description") or "").strip() or _(
				"Atomic model '{name}' of the pruned entity structure."
			).format(name=entity.get("entity") or entity.get("label"))

		entry["behavior"] = behavior

	structure[SUB_MODEL_CONTAINER_KEYS[0]] = kept

	### the couplings of a dropped submodel are dropped as well
	connections = _first_entry_value(structure, CONNECTION_CONTAINER_KEYS, [])

	if isinstance(connections, list):
		filtered = []

		for connection in connections:
			if not isinstance(connection, dict):
				continue

			source = (
				str(_first_entry_value(connection, CONNECTION_SOURCE_KEYS, "") or "")
				.strip()
				.lower()
			)
			target = (
				str(_first_entry_value(connection, CONNECTION_TARGET_KEYS, "") or "")
				.strip()
				.lower()
			)

			if source not in INPUT_REFERENCES and source not in kept_labels:
				continue

			if target not in OUTPUT_REFERENCES and target not in kept_labels:
				continue

			filtered.append(connection)

		structure[CONNECTION_CONTAINER_KEYS[0]] = filtered

	return structure


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Ontology extraction
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _read_text(path):
	"""Return the text of ``path`` (invalid characters are replaced)."""
	with open(path, "r", encoding="utf-8", errors="replace") as stream:
		return stream.read()


def _json_ontology(text):
	"""Return a readable version of a JSON ontology."""
	try:
		data = json.loads(text)
	except ValueError:
		return text

	return json.dumps(data, indent=2, ensure_ascii=False)


def _strip_markup(text):
	"""Return the text of an XML/HTML document without its markup."""
	text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
	text = re.sub(r"<[^>]+>", " ", text)
	text = html.unescape(text)
	text = re.sub(r"[ \t]+", " ", text)

	return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _xml_ontology(text):
	"""Return a readable summary of an XML/OWL/RDF ontology."""
	try:
		root = ElementTree.fromstring(text)
	except ElementTree.ParseError:
		return _strip_markup(text)

	lines = []

	for element in root.iter():
		tag = str(element.tag).split("}")[-1]
		value = re.sub(r"\s+", " ", element.text or "").strip()
		attributes = " ".join(
			f"{str(key).split('}')[-1]}={value}" for key, value in element.attrib.items()
		)
		line = f"{tag} {attributes} {value}".strip()

		if line:
			lines.append(line)

	return "\n".join(lines)


def _turtle_ontology(text):
	"""Return a Turtle/N-Triples ontology without its comments."""
	lines = []

	for line in text.splitlines():
		stripped = line.strip()

		if not stripped or stripped.startswith("#"):
			continue

		lines.append(stripped)

	return "\n".join(lines)


def extract_ontology_text(path, max_chars=MAX_ONTOLOGY_CHARS):
	"""Return the text of the ontology stored in ``path``.

	JSON, XML/OWL/RDF and Turtle ontologies are converted to a readable
	text; other files are read as plain text. The result is truncated to
	``max_chars`` characters so the prompt stays reasonable.
	"""
	if not path:
		return ""

	extension = os.path.splitext(str(path))[1].lower()
	text = _read_text(path)

	if extension == ".json":
		text = _json_ontology(text)
	elif extension in (".xml", ".owl", ".rdf", ".xsd"):
		text = _xml_ontology(text)
	elif extension in (".ttl", ".nt", ".n3"):
		text = _turtle_ontology(text)

	text = text.strip()

	if len(text) > max_chars:
		text = text[:max_chars].rstrip() + "\n...[ontology truncated]"

	return text


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Prompts
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def ses_system_prompt():
	"""Return the system prompt used to generate a System Entity Structure.

	The definitions follow the SES toolbox of the CEA, Wismar University of
	Applied Sciences (SES elements and axioms).
	"""
	return """You are an expert in System Entity Structures (SES) as defined by the
SES toolbox of the CEA (Wismar University of Applied Sciences) and in DEVS
coupled models built with DEVSimPy.

An SES is a tree of entity nodes and descriptive nodes:
- Entity: an object of the real or imagined world. The root and every leaf of
  the SES are entities.
- Aspect (suffix Dec): decomposes an entity into parts (AND). Several aspect
  nodes under one entity form a decision node: exactly one of them is chosen
  when the SES is pruned.
- Multiple-aspect (suffix MultiAspect): decomposes an entity into a variable
  number of copies of ONE entity. It declares a replication variable and the
  range of that variable; the number of copies is chosen when the SES is
  pruned.
- Specialization (suffix Spec): taxonomy of an entity (XOR). Exactly one
  alternative is chosen when the SES is pruned. Several specialization nodes
  under one entity are independent choices.

The answer must satisfy the SES axioms:
1. Alternating mode: entity nodes and descriptive nodes alternate; a
   descriptive node only connects entities.
2. Strict hierarchy: an entity name never appears twice on the same path.
3. Uniformity: each entity is declared only once in the whole SES.
4. Valid siblings: the parts of one aspect (and the alternatives of one
   specialization) are distinct and describe the same parent entity.
5. Assigned variables: every multiple-aspect declares a replication variable
   and a numeric range.

Rules:
1. Answer with a single JSON object and nothing else: no markdown, no
   explanation, no code fences.
2. When an ontology is provided, use its vocabulary for entity names: prefer
   the class names of the ontology, without namespaces, and do not invent an
   entity that the ontology does not support unless the request requires it.
   When no ontology is provided, derive the entity names from the request.
3. Names must be valid Python identifiers (letters, digits and underscores, no
   spaces) and must be unique in the whole SES.
4. Put the parts of an entity in "aspects", the replicated entity in
   "multi_aspects", and the alternatives in "specializations". An aspect or a
   specialization is a descriptive node, not an entity: it only lists its
   entities under "entities" (a non-empty list) and never has "aspects",
   "multi_aspects" or "specializations" of its own. A multiple-aspect lists
   exactly one entity under "entity".
5. Descriptive node names are bare names: the Dec/MultiAspect/Spec suffix is
   added by the viewer, so do not write it yourself.
6. Do not put a "multiplicity" on an aspect: use a multiple-aspect node when
   an entity is replicated.
7. An entity may have aspects, multiple-aspects and specializations at the
   same time, or none.
8. Keep the structure readable: at most 12 descriptive nodes per entity and at
   most 60 entities in total.
9. The root object is the root entity of the SES: it carries the name of the
   family of models.

Expected JSON shape (the entity shape is recursive):
{
  "name": "RootEntity",
  "description": "short description",
  "aspects": [
    {
      "name": "physical",
      "entities": [
        {
          "name": "PartEntity",
          "description": "short description",
          "aspects": [],
          "multi_aspects": [],
          "specializations": []
        }
      ]
    }
  ],
  "multi_aspects": [
    {
      "name": "pages",
      "variable": "numPages",
      "min": 30,
      "max": 140,
      "entity": {
        "name": "Page",
        "description": "short description",
        "aspects": [],
        "multi_aspects": [],
        "specializations": []
      }
    }
  ],
  "specializations": [
    {
      "name": "genre",
      "entities": [
        {
          "name": "AlternativeEntity",
          "description": "short description",
          "aspects": [],
          "multi_aspects": [],
          "specializations": []
        }
      ]
    }
  ]
}
"""


def ses_user_prompt(prompt, ontology_text, model_name=None):
	"""Return the user prompt asking for a System Entity Structure."""
	lines = [("Design the System Entity Structure (SES) of a family of DEVSimPy coupled models.")]

	if model_name:
		lines.append(f"The root entity is '{model_name}'.")

	lines.append("")

	if str(ontology_text or "").strip():
		lines.append("Ontology (extracted text):")
		lines.append("<<<ONTOLOGY")
		lines.append(str(ontology_text).strip())
		lines.append("ONTOLOGY>>>")
	else:
		lines.append("No ontology was provided: derive the entity names from the request.")

	lines.append("")
	lines.append("User request:")
	lines.append(str(prompt or "").strip() or "Describe a family of coupled models.")
	lines.append("")
	lines.append("Return only the SES JSON object described in the system message.")

	return "\n".join(lines)


def ses_repair_prompt(prompt, answer, error, model_name=None):
	"""Return the prompt asking the AI to correct an invalid SES.

	Small models frequently return an aspect without entity, or nest the
	parts of an aspect directly: the answer and the rule it breaks are shown
	to the model, which returns the corrected structure. The ontology is not
	sent again: the previous answer already carries its vocabulary.
	"""
	lines = [
		"The System Entity Structure you returned cannot be used:",
		f"- {error}",
		"",
		"Your previous answer:",
		"<<<SES",
		str(answer or "").strip(),
		"SES>>>",
		"",
	]

	if model_name:
		lines.append(f"The root entity is '{model_name}'.")
		lines.append("")

	lines.append("User request:")
	lines.append(str(prompt or "").strip() or "Describe a family of coupled models.")
	lines.append("")
	lines.append("Correct the answer and return the whole SES again:")
	lines.append(
		'- every aspect and every specialization declares "entities": [ ... ] '
		"with at least one entity;"
	)
	lines.append('- every multiple-aspect declares "entity": { ... } with exactly one entity;')
	lines.append(
		"- an entity only contains aspects, multi_aspects and specializations: an "
		"aspect or a specialization is not an entity and has no aspects of its own."
	)
	lines.append("")
	lines.append("Return only the JSON object described in the system message.")

	return "\n".join(lines)


def coupled_prompt_from_ses(prompt, ses):
	"""Return the prompt asking for a coupled model consistent with ``ses``."""
	lines = [
		(
			"Create a DEVSimPy coupled model that is one pruned instance of the "
			"System Entity Structure (SES) below."
		),
		"",
		"SES (JSON):",
		json.dumps(ses, indent=2, ensure_ascii=False),
		"",
		"Rules:",
		(
			"- The SES is pruned: choose exactly one aspect when an entity has "
			"several aspects, and exactly one alternative for every "
			"specialization node."
		),
		"- An aspect (Dec) creates one submodel per entity it declares.",
		(
			"- A multiple-aspect (MultiAspect) replicates its entity: pick a number "
			"of instances inside its [min, max] range (label them Entity1, "
			"Entity2, ...)."
		),
		("- Use the entity names of the SES (sanitized as Python identifiers) as submodel labels."),
		"- Keep the couplings and the port counts consistent with the request.",
		"",
		"User request:",
		str(prompt or "").strip() or "Build the coupled model described by the SES.",
		"",
		"Return only the JSON object described in the system message.",
	]

	return "\n".join(lines)


### System message of the questions asked while the SES is pruned
PRUNING_SYSTEM_PROMPT = (
	"You guide the interactive pruning of a System Entity Structure (SES). "
	"Ask one short question, give a one-sentence hint and a recommendation. "
	"Answer with a single JSON object and no markdown."
)


def pruning_question_prompt(decision, prompt, ontology_text="", context=None):
	"""Return the prompt asking the AI to word one pruning question."""
	lines = [
		"You guide the interactive pruning of a System Entity Structure (SES).",
		"",
		"User request:",
		str(prompt or "").strip() or "(not given)",
	]

	ontology_text = str(ontology_text or "").strip()

	if ontology_text:
		lines += ["", "Ontology extract:", _head(ontology_text, 4000)]

	lines += ["", "Current entity: " + " > ".join(decision.get("trail") or ())]

	if decision["kind"] == PRUNING_SPECIALIZATION:
		lines += [
			"",
			(
				"'{entity}' is specialized by '{node}'. Exactly one alternative must be chosen:"
			).format(entity=decision["entity"], node=decision["node"]),
		]
	elif decision["kind"] == PRUNING_ASPECT:
		lines += [
			"",
			(
				"'{entity}' can be decomposed in {count} ways. Exactly one aspect must be chosen:"
			).format(entity=decision["entity"], count=len(decision["options"])),
		]
	else:
		maximum = decision.get("max")

		lines += [
			"",
			(
				"The multiple-aspect '{node}' replicates '{child}' with the variable '{variable}'."
			).format(
				node=decision["node"],
				child=decision.get("child") or "?",
				variable=decision.get("variable") or "?",
			),
			("The SES allows between {min} and {max} instances.").format(
				min=decision.get("min"),
				max=maximum if maximum is not None else "unbounded",
			),
		]

	for index, option in enumerate(decision["options"], 1):
		description = str(option.get("description") or "").strip()

		lines.append(f"{index}. {option['name']}" + (f" - {description}" if description else ""))

	context = [line for line in context or [] if line]

	if context:
		lines += ["", "Decisions already made:"] + [f"- {line}" for line in context]

	lines += [
		"",
		(
			"Write one short question for the user (at most two sentences), a "
			"one-sentence hint that explains the trade-off, and a recommendation."
		),
		(
			'Return only: {"question": "...", "hint": "...", '
			'"recommendation": "<name, number or count>"}'
		),
	]

	return "\n".join(lines)


def parse_pruning_guidance(text):
	"""Return the question, hint and recommendation of an AI answer.

	An answer that is not JSON is kept as the question, so a provider that
	ignores the output format still helps the user.
	"""
	guidance = {"question": "", "hint": "", "recommendation": ""}
	raw = str(text or "").strip()

	if not raw:
		return guidance

	data = None

	try:
		from CoupledStructure import parse_json_object

		data = parse_json_object(raw)
	except Exception:
		### the answer is plain text: use it as the question
		data = None

	if isinstance(data, dict):
		for key in ("question", "hint", "recommendation"):
			value = data.get(key)

			if isinstance(value, str):
				guidance[key] = value.strip()
	elif raw:
		guidance["question"] = " ".join(raw.split())[:400]

	return guidance


def _recommendation_index(decision, recommendation):
	"""Return the option or count recommended by the AI, or None."""
	text = str(recommendation or "").strip()

	if not text:
		return None

	if decision["kind"] == PRUNING_MULTIPLICITY:
		match = re.search(r"-?\d+", text)

		if match:
			return _clamp_instances(
				int(match.group()),
				decision["min"],
				decision["max"],
			)

		return None

	for index, option in enumerate(decision["options"]):
		if text.lower() == str(option["name"]).strip().lower():
			return index

	match = re.search(r"\d+", text)

	if match:
		index = int(match.group()) - 1

		if 0 <= index < len(decision["options"]):
			return index

	return None


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# AI generation
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def model_setting_key(provider=None):
	"""Return the ``PARAMS_IA`` key that holds the model of ``provider``."""
	return MODEL_SETTING_KEYS.get(provider or getattr(builtins, "SELECTED_IA", "") or "")


def current_model_name(provider=None):
	"""Return the model selected for ``provider`` in the Preferences."""
	provider = provider or getattr(builtins, "SELECTED_IA", "") or ""
	key = model_setting_key(provider)

	if not key:
		return ""

	params = getattr(builtins, "PARAMS_IA", {}) or {}

	return str(params.get(key, MODEL_DEFAULT_NAMES.get(provider, "")) or "")


def adapter_signature():
	"""Return the (provider, model) pair used to detect a stale AI adapter."""
	return (getattr(builtins, "SELECTED_IA", "") or "", current_model_name())


def set_current_model(model_name, provider=None):
	"""Store the model chosen for ``provider`` and reset the AI adapter.

	The selection is written to ``builtins.PARAMS_IA`` exactly like the model
	chooser of the atomic-model AI assistant of the editor, so the choice is
	shared by all the AI assistants.

	Returns:
		bool: True when the selection changed.
	"""
	provider = provider or getattr(builtins, "SELECTED_IA", "") or ""
	key = model_setting_key(provider)

	if not key:
		return False

	model_name = str(model_name or "").strip()
	params = getattr(builtins, "PARAMS_IA", {}) or {}

	if params.get(key) == model_name:
		return False

	params[key] = model_name
	builtins.PARAMS_IA = params

	try:
		from AIAdapter import AdapterFactory

		AdapterFactory.reset_instance()
	except Exception as error:
		_log(f"Cannot reset the AI adapter: {error}")

	return True


def provider_models(provider=None):
	"""Return the models available from ``provider``.

	The query reaches the provider (OpenAI API, the Ollama server or the
	LM Studio server) and may raise an exception that the caller reports.
	"""
	provider = provider or getattr(builtins, "SELECTED_IA", "") or ""
	params = getattr(builtins, "PARAMS_IA", {}) or {}

	if provider == "ChatGPT":
		from AIAdapter import ChatGPTDevsAdapter

		adapter = ChatGPTDevsAdapter(
			api_key=params.get("CHATGPT_API_KEY"),
			model_name=current_model_name(provider),
		)

		return list(adapter.get_available_models())

	if provider == "Ollama":
		from AIAdapter import OllamaDevsAdapter

		return list(OllamaDevsAdapter.get_available_models())

	if provider == "LM Studio":
		from AIAdapter import LMStudioDevsAdapter

		adapter = LMStudioDevsAdapter(
			base_url=params.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
			model_name=current_model_name(provider),
		)

		return list(adapter.get_available_models())

	return []


def get_selected_adapter(parent=None):
	"""Return the AI adapter selected in the Preferences, or None."""
	if not getattr(builtins, "SELECTED_IA", ""):
		return None

	try:
		from AIAdapter import AdapterFactory

		params = getattr(builtins, "PARAMS_IA", {}) or {}

		return AdapterFactory.get_adapter_instance(parent=parent, params=params)
	except Exception as error:
		sys.stderr.write(f"Cannot create the AI adapter: {error}\n")
		return None


def generate_ses(
	adapter,
	prompt,
	ontology_text="",
	model_name=None,
	on_token=None,
	stop_event=None,
):
	"""Generate and normalize a SES from a prompt and an optional ontology.

	``ontology_text`` may be empty: the entity names are then derived from
	the prompt only.

	One repair round-trip is attempted when the AI returns a structure that
	breaks the SES rules: the model is shown its answer and the error, then
	asked for the corrected structure. Small models often omit the entities
	of an aspect, which this recovers from without losing the whole run.
	"""
	if adapter is None:
		raise SESError("No AI provider is selected.")

	from CoupledStructure import CoupledStructureError, parse_json_object

	system_prompt = ses_system_prompt()
	answer = adapter.generate_output(
		ses_user_prompt(prompt, ontology_text, model_name=model_name),
		system_prompt=system_prompt,
		on_token=on_token,
		stop_event=stop_event,
	)

	try:
		return normalize_ses(parse_json_object(answer))
	except (SESError, CoupledStructureError) as error:
		first_error = error

	### a stopped generation is not repaired
	if stop_event is not None and stop_event.is_set():
		raise SESError(str(first_error)) from first_error

	answer = adapter.generate_output(
		ses_repair_prompt(prompt, answer, first_error, model_name=model_name),
		system_prompt=system_prompt,
		on_token=on_token,
		stop_event=stop_event,
	)

	try:
		return normalize_ses(parse_json_object(answer))
	except (SESError, CoupledStructureError) as error:
		raise SESError(
			_(
				"The AI returned an invalid SES twice.\n"
				"First error: {first}\n"
				"Second error: {second}\n"
				"Try again, or rephrase the request."
			).format(first=first_error, second=error)
		) from error


def _first_entry_value(mapping, keys, default=None):
	"""Return the first non-empty value of ``mapping`` among ``keys``."""
	for key in keys:
		if key in mapping:
			value = mapping[key]

			if value is not None and value != "":
				return value

	return default


def _port_index(value):
	"""Return the 0-based index of a port declared by the AI."""
	try:
		return max(0, int(value))
	except (TypeError, ValueError):
		return 0


def _port_count(mapping, keys, default=0):
	"""Return a declared port count, or ``default`` when it is absent."""
	value = _first_entry_value(mapping, keys)

	return default if value is None else _port_index(value)


def _set_port_count(mapping, keys, value):
	"""Write ``value`` in the key the AI already used, or in the canonical one."""
	for key in keys:
		if key in mapping:
			mapping[key] = value
			return

	mapping[keys[0]] = value


def grow_declared_ports(structure, inputs=None, outputs=None):
	"""Raise the declared port counts to the ports used by the connections.

	The AI frequently declares two output ports and couples the third one, or
	declares one input port and targets the second one. The declared counts are
	authoritative for the models that are built from the structure, so
	``normalize_coupled_structure`` rejects the whole answer. Instead of losing
	the couplings, the counts are raised to the highest port index really used:
	an atomic model is created with exactly the declared ports, and the coupled
	model receives the missing port shapes before the structure is applied.

	``inputs`` and ``outputs`` are the port counts requested by the caller: they
	are kept when the answer does not declare them, so an existing coupled model
	never loses ports.

	``structure`` is the raw answer of the AI, modified in place and returned.
	Only the counts that a connection exceeds are raised: an untouched submodel
	keeps the counts chosen by the AI (including zero).
	"""
	if not isinstance(structure, dict):
		return structure

	from CoupledStructure import INPUT_REFERENCES, OUTPUT_REFERENCES

	submodels = _first_entry_value(structure, SUB_MODEL_CONTAINER_KEYS, [])

	if not isinstance(submodels, list):
		return structure

	connections = _first_entry_value(structure, CONNECTION_CONTAINER_KEYS, [])

	if not isinstance(connections, list):
		return structure

	### the submodels by label, as the connections reference them
	index = {}

	for position, submodel in enumerate(submodels):
		if not isinstance(submodel, dict):
			continue

		label = str(
			_first_entry_value(submodel, SUB_MODEL_LABEL_KEYS, f"Model{position + 1}") or ""
		).strip()

		if label:
			index.setdefault(label.lower(), submodel)

	### counts requested by the caller when the answer does not declare them
	requested_inputs = 0 if inputs is None else _port_index(inputs)
	requested_outputs = 0 if outputs is None else _port_index(outputs)

	structure_inputs = _port_count(structure, PORT_INPUT_KEYS, requested_inputs)
	structure_outputs = _port_count(structure, PORT_OUTPUT_KEYS, requested_outputs)

	### required counts of the submodels: label -> [inputs, outputs]
	required = {}

	def require(label, input_ports=0, output_ports=0):
		counts = required.setdefault(label, [0, 0])
		counts[0] = max(counts[0], input_ports)
		counts[1] = max(counts[1], output_ports)

	for connection in connections:
		if not isinstance(connection, dict):
			continue

		source = str(_first_entry_value(connection, CONNECTION_SOURCE_KEYS, "") or "").strip()
		target = str(_first_entry_value(connection, CONNECTION_TARGET_KEYS, "") or "").strip()
		source_port = _port_index(_first_entry_value(connection, CONNECTION_SOURCE_PORT_KEYS, 0))
		target_port = _port_index(_first_entry_value(connection, CONNECTION_TARGET_PORT_KEYS, 0))

		if source.lower() in INPUT_REFERENCES:
			structure_inputs = max(structure_inputs, source_port + 1)
		elif source.lower() in index:
			require(source.lower(), output_ports=source_port + 1)

		if target.lower() in OUTPUT_REFERENCES:
			structure_outputs = max(structure_outputs, target_port + 1)
		elif target.lower() in index:
			require(target.lower(), input_ports=target_port + 1)

	for label, (input_ports, output_ports) in required.items():
		submodel = index[label]

		### an absent count defaults to one port in normalize_coupled_structure
		if input_ports > _port_count(submodel, PORT_INPUT_KEYS, 1):
			_set_port_count(submodel, PORT_INPUT_KEYS, input_ports)

		if output_ports > _port_count(submodel, PORT_OUTPUT_KEYS, 1):
			_set_port_count(submodel, PORT_OUTPUT_KEYS, output_ports)

	if structure_inputs > _port_count(structure, PORT_INPUT_KEYS, requested_inputs):
		_set_port_count(structure, PORT_INPUT_KEYS, structure_inputs)

	if structure_outputs > _port_count(structure, PORT_OUTPUT_KEYS, requested_outputs):
		_set_port_count(structure, PORT_OUTPUT_KEYS, structure_outputs)

	return structure


def generate_coupled_structure(
	adapter,
	prompt,
	ses,
	catalog=None,
	model_name=None,
	inputs=None,
	outputs=None,
	generate_atomic_code=True,
	on_token=None,
	stop_event=None,
):
	"""Generate and normalize a coupled structure that prunes ``ses``."""
	if adapter is None:
		raise SESError("No AI provider is selected.")

	from CoupledStructure import normalize_coupled_structure, parse_json_object

	raw = adapter.generate_coupled_model_json(
		coupled_prompt_from_ses(prompt, ses),
		catalog=catalog,
		model_name=model_name,
		inputs=inputs,
		outputs=outputs,
		generate_atomic_code=generate_atomic_code,
		on_token=on_token,
		stop_event=stop_event,
	)

	return normalize_coupled_structure(
		grow_declared_ports(parse_json_object(raw), inputs=inputs, outputs=outputs),
		catalog=catalog,
		name=model_name,
		inputs=inputs,
		outputs=outputs,
	)


def generate_coupled_structure_from_pes(
	adapter,
	prompt,
	pes,
	catalog=None,
	model_name=None,
	inputs=None,
	outputs=None,
	generate_atomic_code=True,
	on_token=None,
	stop_event=None,
):
	"""Generate and normalize the coupled structure of a pruned SES.

	The submodels are derived from the PES (see :func:`pes_submodels`), so the
	AI only chooses the ports and the couplings of the pruned structure.
	"""
	if adapter is None:
		raise SESError(_("No AI provider is selected."))

	from CoupledStructure import normalize_coupled_structure, parse_json_object

	submodels = pes_submodels(pes)

	if not submodels:
		raise SESError(
			_("The pruned structure has no atomic submodel: the SES describes a single entity.")
		)

	raw = adapter.generate_coupled_model_json(
		pes_coupled_prompt(
			prompt,
			pes,
			submodels,
			model_name=model_name,
			inputs=inputs,
			outputs=outputs,
		),
		catalog=catalog,
		model_name=model_name,
		inputs=inputs,
		outputs=outputs,
		generate_atomic_code=generate_atomic_code,
		on_token=on_token,
		stop_event=stop_event,
	)

	structure = normalize_coupled_structure(
		grow_declared_ports(
			restrict_to_pes(parse_json_object(raw), submodels),
			inputs=inputs,
			outputs=outputs,
		),
		catalog=catalog,
		name=model_name,
		inputs=inputs,
		outputs=outputs,
	)

	return merge_pes_structure(structure, submodels)


def _submodel_generate_mode(submodel):
	"""Return the canonical generate mode of a submodel."""
	from CoupledStructure import GENERATE_ALIASES

	mode = str(submodel.get("generate", "existing") or "existing").strip().lower()

	return GENERATE_ALIASES.get(mode, mode)


def generate_missing_submodel_code(
	structure,
	adapter,
	on_token=None,
	stop_event=None,
	progress=None,
	errors=None,
):
	"""Generate the atomic source of the ``behavior`` submodels.

	The generated source is stored in ``submodel["code"]``. A submodel whose
	generation fails is downgraded to an empty ``stub`` model and the error is
	appended to ``errors`` (when given).
	"""
	from CoupledStructure import generate_submodel_code

	if not isinstance(structure, dict):
		return structure

	coupled_name = str(structure.get("name") or "CoupledModel").strip()

	for position, submodel in enumerate(structure.get("submodels") or []):
		if not isinstance(submodel, dict):
			continue

		if _submodel_generate_mode(submodel) != "behavior":
			continue

		### a submodel that already carries code needs no generation
		if str(submodel.get("code") or "").strip():
			continue

		behavior = str(
			submodel.get("behavior")
			or submodel.get("behaviour")
			or submodel.get("specification")
			or submodel.get("description")
			or ""
		).strip()

		if not behavior:
			continue

		if stop_event is not None and stop_event.is_set():
			break

		label = str(submodel.get("label") or f"Model{position + 1}").strip()

		if progress is not None:
			progress(label)

		try:
			code = generate_submodel_code(
				submodel,
				coupled_name,
				adapter,
				on_token=on_token,
				stop_event=stop_event,
			)
		except Exception as error:
			_log(f"Atomic model '{label}' generation failed: {error}")
			submodel["generate"] = "stub"

			if errors is not None:
				errors.append((label, error))

			continue

		### a stopped generation returns no code: fall back to an empty model
		if not str(code or "").strip():
			submodel["generate"] = "stub"
			continue

		submodel["code"] = code

	return structure


def downgrade_behavior_submodels(structure):
	"""Turn the code-less ``behavior`` submodels into empty stubs.

	Used when the atomic model code generation is disabled: the submodel
	still exists in the diagram, as an empty atomic model with its ports.
	"""
	if not isinstance(structure, dict):
		return structure

	for submodel in structure.get("submodels") or []:
		if not isinstance(submodel, dict):
			continue

		if _submodel_generate_mode(submodel) != "behavior":
			continue

		if str(submodel.get("code") or "").strip():
			continue

		submodel["generate"] = "stub"

	return structure


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Model archive
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def is_model_archive(path):
	"""Return True when ``path`` is a readable DEVSimPy model archive."""
	try:
		path = str(path or "")

		return (
			path.lower().endswith(ARCHIVE_EXTENSIONS)
			and os.path.isfile(path)
			and zipfile.is_zipfile(path)
		)
	except OSError:
		return False


def _clear_zip_cache(archive):
	"""Drop the zipimport cache entry so the archive is re-read."""
	try:
		import ZipManager

		ZipManager.Zip.ClearCache(archive)
	except Exception:  # noqa: S110
		### ZipManager is optional (self-test / standalone usage)
		pass


def read_ses(archive):
	"""Return the SES payload stored in ``archive``, or None."""
	if not is_model_archive(archive):
		return None

	try:
		with zipfile.ZipFile(archive, "r") as stream:
			if SES_ENTRY not in set(stream.namelist()):
				return None

			payload = json.loads(stream.read(SES_ENTRY).decode("utf-8"))
	except (OSError, zipfile.BadZipFile, ValueError) as error:
		sys.stderr.write(f"Cannot read the SES of '{archive}': {error}\n")
		return None

	return payload if isinstance(payload, dict) else None


def write_ses(archive, payload):
	"""Store ``payload`` in the SES entry of ``archive``.

	Every other entry of the archive is preserved and the entry is replaced
	instead of duplicated. The archive is replaced atomically.
	"""
	if not is_model_archive(archive):
		return False

	temp_archive = f"{archive}.tmp"

	try:
		with (
			zipfile.ZipFile(archive, "r") as source,
			zipfile.ZipFile(temp_archive, "w", zipfile.ZIP_DEFLATED) as target,
		):
			seen = set()

			for item in source.infolist():
				### archives can contain the same name twice
				if item.filename == SES_ENTRY or item.filename in seen:
					continue

				seen.add(item.filename)
				target.writestr(item, source.read(item.filename))

			target.writestr(
				SES_ENTRY,
				json.dumps(payload, indent=2, ensure_ascii=False),
			)

		os.replace(temp_archive, archive)
	except (OSError, zipfile.BadZipFile, ValueError) as error:
		sys.stderr.write(f"Cannot store the SES of '{archive}': {error}\n")

		try:
			if os.path.exists(temp_archive):
				os.remove(temp_archive)
		except OSError:
			pass

		return False

	_clear_zip_cache(archive)

	return True


def build_ses_payload(
	ses,
	structure=None,
	prompt="",
	ontology_path="",
	ontology_text="",
	model_name="",
	pes=None,
	pruning_answers=None,
	output_dir="",
):
	"""Return the payload stored in the model archive."""
	return {
		"version": SES_PAYLOAD_VERSION,
		"model_name": str(model_name or ""),
		"prompt": str(prompt or ""),
		"ontology": {
			"path": str(ontology_path or ""),
			"text": str(ontology_text or ""),
		},
		"ses": ses,
		"structure": structure,
		"pes": pes,
		"pruning_answers": pruning_answers,
		"output_dir": str(output_dir or ""),
		"generated_at": datetime.now().astimezone().isoformat(),
	}


def attach_ses_payload(block, payload):
	"""Keep ``payload`` on ``block`` so later saves can re-embed it."""
	if block is None or not isinstance(payload, dict):
		return False

	try:
		block.ses_payload = payload
	except Exception as error:
		sys.stderr.write(f"Cannot keep the SES on the coupled model: {error}\n")
		return False

	return True


def persist_ses_entry(block, archive):
	"""Re-embed the SES carried by ``block`` into ``archive``.

	DEVSimPy rewrites ``DEVSimPyModel.dat`` when a model is saved and keeps
	the unknown entries of the archive, so the SES of a normal save already
	survives. This helper covers the other case: the archive is written from
	scratch ('Save as', new model), which drops every entry but the diagram,
	the code and the image.
	"""
	payload = getattr(block, "ses_payload", None)

	if not isinstance(payload, dict) or not is_model_archive(archive):
		return False

	return write_ses(archive, payload)


### Attribute marking the patched SaveFile (prevents a double patch)
SES_SAVE_HOOK = "_ses_generator_save_hook"


def install_ses_persistence_hook():
	"""Re-embed the SES after every save of a coupled model block.

	The plug-in may not modify the project files: the method of the block is
	patched at run time, once, and only for coupled model blocks.
	"""
	try:
		from Container import ContainerBlock
	except Exception as error:
		_log(f"Coupled model persistence hook not installed: {error}")
		return False

	current = ContainerBlock.SaveFile

	if getattr(current, SES_SAVE_HOOK, False):
		return True

	def save_file_with_ses(self, fileName=None):
		"""Save the block and keep its SES in the archive."""
		result = current(self, fileName)

		if result:
			archive = fileName or str(getattr(self, "model_path", "") or "")

			try:
				persist_ses_entry(self, archive)
			except Exception as error:
				sys.stderr.write(f"Cannot store the SES of '{archive}': {error}\n")

		return result

	setattr(save_file_with_ses, SES_SAVE_HOOK, True)
	ContainerBlock.SaveFile = save_file_with_ses

	return True


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Diagram construction
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def ensure_ports(block, inputs, outputs):
	"""Add the missing input/output port shapes of ``block``.

	Returns:
		tuple: ``(added_inputs, added_outputs)``.
	"""
	from Container import iPort, oPort

	input_ports = [shape for shape in block.GetShapeList() if isinstance(shape, iPort)]
	output_ports = [shape for shape in block.GetShapeList() if isinstance(shape, oPort)]

	added_inputs = 0
	next_id = max((getattr(shape, "id", 0) for shape in input_ports), default=-1) + 1

	for offset in range(max(int(inputs), 0) - len(input_ports)):
		port = iPort(label=f"IPort {next_id + offset}")
		port.id = next_id + offset
		block.AddShape(port)
		port.move(50, 100 * port.id)
		added_inputs += 1

	added_outputs = 0
	next_id = max((getattr(shape, "id", 0) for shape in output_ports), default=-1) + 1

	for offset in range(max(int(outputs), 0) - len(output_ports)):
		port = oPort(label=f"OPort {next_id + offset}")
		port.id = next_id + offset
		block.AddShape(port)
		port.move(300, 100 * port.id)
		added_outputs += 1

	if added_inputs:
		block.input = max(int(getattr(block, "input", 0) or 0), int(inputs))

	if added_outputs:
		block.output = max(int(getattr(block, "output", 0) or 0), int(outputs))

	return added_inputs, added_outputs


def _refresh_canvas(block, canvas=None):
	"""Redraw the canvas that contains ``block``."""
	if canvas is None:
		canvas = getattr(block, "parent", None)

	if canvas is None:
		return

	diagram = getattr(canvas, "diagram", None)

	if diagram is not None:
		diagram.modify = True

	diagram_modified = getattr(canvas, "DiagramModified", None)

	if callable(diagram_modified):
		diagram_modified()

	update_shapes = getattr(canvas, "UpdateShapes", None)

	if callable(update_shapes):
		update_shapes()

	refresh = getattr(canvas, "Refresh", None)

	if callable(refresh):
		refresh()


def apply_structure_to_block(block, structure, canvas=None):
	"""Populate ``block`` with ``structure``.

	The ports missing from the block are added first, so a structure that
	declares more ports than the block still applies.

	Returns:
		tuple: ``(submodels, connections, added_inputs, added_outputs)``.
	"""
	from CoupledStructure import apply_coupled_structure

	added_inputs, added_outputs = ensure_ports(
		block,
		int(structure.get("inputs") or 0),
		int(structure.get("outputs") or 0),
	)

	submodels, connections = apply_coupled_structure(block, structure)

	_refresh_canvas(block, canvas)

	return submodels, connections, added_inputs, added_outputs


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Creation of a coupled model block
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _docstring_text(value, limit=200):
	"""Return ``value`` as a single safe docstring line."""
	text = " ".join(str(value or "").split())
	text = text.replace('"', "'").replace("\\", "/")

	return text[:limit]


def _identifier(value, fallback="CoupledModel"):
	"""Return a Python identifier built from ``value``."""
	text = "".join(
		character if (character.isalnum() or character == "_") else "_"
		for character in str(value or "")
	)
	text = re.sub(r"_+", "_", text).strip("_")

	if not text:
		text = fallback

	if text[0].isdigit():
		text = f"_{text}"

	return text


def _model_directory(canvas=None, preferred=None):
	"""Return the directory where a new model archive must be written.

	``preferred`` (the folder chosen in the assistant) wins when it exists.
	Otherwise the archive is stored next to the diagram file. An unsaved
	diagram falls back to the model library, as the model generator wizard
	does, then to the current directory.
	"""
	preferred = str(preferred or "").strip()

	if preferred and os.path.isdir(preferred):
		return preferred

	diagram = getattr(canvas, "diagram", None)
	path = str(getattr(diagram, "last_name_saved", "") or "")

	if path:
		directory = os.path.dirname(os.path.abspath(path))

		if os.path.isdir(directory):
			return directory

	domain = str(getattr(builtins, "DOMAIN_PATH", "") or "")

	if domain and os.path.isdir(domain):
		return domain

	return os.getcwd()


def _remember_output_dir(directory):
	"""Remember the output folder of the assistant (also across sessions)."""
	global _last_output_dir

	directory = str(directory or "").strip()

	if not directory or not os.path.isdir(directory):
		return _last_output_dir

	_last_output_dir = directory

	try:
		from Utilities import getTopLevelWindow

		config = getattr(getTopLevelWindow(), "cfg", None)

		if config is not None:
			config.Write("ses_output_dir", directory)
			config.Flush()
	except Exception:  # noqa: S110
		### the folder is only remembered for the current session
		pass

	return _last_output_dir


def _restore_output_dir():
	"""Return the output folder remembered by the assistant."""
	global _last_output_dir

	if _last_output_dir:
		return _last_output_dir

	try:
		from Utilities import getTopLevelWindow

		config = getattr(getTopLevelWindow(), "cfg", None)

		if config is not None:
			directory = str(config.Read("ses_output_dir") or "").strip()

			if directory and os.path.isdir(directory):
				_last_output_dir = directory
	except Exception:  # noqa: S110
		### no configuration: the default folder is used
		pass

	return _last_output_dir


def unique_model_path(directory, name, extension=".cmd"):
	"""Return a free ``<directory>/<name><extension>`` path."""
	stem = _identifier(name)
	candidate = os.path.join(directory, f"{stem}{extension}")
	index = 1

	while os.path.exists(candidate):
		candidate = os.path.join(directory, f"{stem}_{index}{extension}")
		index += 1

	return candidate


def coupled_code(class_name, description=""):
	"""Return the Python source of a generated coupled model."""
	text = _docstring_text(description) or (
		"Coupled model generated from a System Entity Structure."
	)

	return (
		"# -*- coding: utf-8 -*-\n"
		"\n"
		f'"""\n Name: {class_name}.py\n Model description: {text}\n"""\n'
		"\n"
		"from DomainInterface import DomainStructure\n"
		"\n"
		"\n"
		f"class {class_name}(DomainStructure):\n"
		f'\t"""{text}"""\n'
		"\n"
		"\tdef __init__(self):\n"
		"\t\tDomainStructure.__init__(self)\n"
		"\n"
		"\tdef __str__(self):\n"
		f'\t\treturn "{class_name}"\n'
	)


def _write_model_archive(archive, python_entry, code):
	"""Write a model archive holding ``code`` and an empty diagram."""
	directory = os.path.dirname(archive)

	if directory:
		os.makedirs(directory, exist_ok=True)

	with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as stream:
		stream.writestr(python_entry, code)
		stream.writestr(MODEL_ENTRY, b"Call SaveFile method first!")

	_clear_zip_cache(archive)

	return archive


def create_pending_block(canvas=None, label=None, directory=None):
	"""Return a coupled model block that is not yet in a diagram.

	Nothing is written on the disk: the archive is only created once the
	assistant has produced the coupled model (see
	:func:`finalize_pending_block`), so cancelling the dialog leaves the
	diagram and the model directory untouched. ``directory`` is the output
	folder chosen in the assistant.
	"""
	from Container import ContainerBlock

	directory = _model_directory(canvas, directory)
	archive = unique_model_path(directory, label or "CoupledModel")
	stem = os.path.splitext(os.path.basename(archive))[0]

	block = ContainerBlock(stem, 0, 0)
	### ContainerBlock normally gets these attributes from __setstate__
	block.args = {}
	block.model_path = archive
	block.python_path = os.path.join(archive, f"{stem}.py")
	block.last_name_saved = archive

	return block


def _apply_pending_directory(block, directory, name=None):
	"""Move the archive paths of a not yet written block to ``directory``.

	Nothing is written on the disk: the pending block only carries the paths
	that :func:`finalize_pending_block` uses to create its archive, so the
	folder can be changed until the model is generated.
	"""
	directory = str(directory or "").strip()

	if block is None or not directory or not os.path.isdir(directory):
		return False

	stem = _identifier(name or getattr(block, "label", "") or "CoupledModel")
	archive = unique_model_path(directory, stem)

	block.model_path = archive
	block.python_path = os.path.join(archive, f"{stem}.py")
	block.last_name_saved = archive

	return True


def _canvas_position(canvas, block, position):
	"""Return the canvas coordinates where ``block`` must be moved."""
	try:
		x, y = int(position[0]), int(position[1])
	except (IndexError, TypeError, ValueError):
		return NEW_BLOCK_X, NEW_BLOCK_Y

	get_xy = getattr(canvas, "GetXY", None)

	if callable(get_xy):
		try:
			x, y = get_xy(block, x, y)
		except Exception:  # noqa: S110
			### the canvas has no usable coordinate conversion
			pass

	### a block outside the scrollable area could not be reached again
	return max(0, int(x)), max(0, int(y))


def finalize_pending_block(block, structure, canvas=None, position=None):
	"""Create the archive of ``block``, fill it and add it to ``canvas``.

	The name chosen by the AI becomes the label of the block, the name of
	its archive and the name of its Python class, because DEVSimPy requires
	them to match.

	Returns:
		tuple: ``(submodels, connections, added_inputs, added_outputs)``.
	"""
	from CoupledStructure import apply_coupled_structure

	name = str(structure.get("name") or block.label or "CoupledModel").strip()
	directory = os.path.dirname(str(block.model_path or "")) or _model_directory(canvas)
	archive = unique_model_path(directory, name)
	stem = os.path.splitext(os.path.basename(archive))[0]

	block.label = stem
	block.model_path = archive
	block.python_path = os.path.join(archive, f"{stem}.py")
	block.last_name_saved = archive

	### the submodels are written next to the archive: model_path must be set
	added_inputs, added_outputs = ensure_ports(
		block,
		int(structure.get("inputs") or 0),
		int(structure.get("outputs") or 0),
	)

	submodels, connections = apply_coupled_structure(block, structure)

	_write_model_archive(
		archive,
		f"{stem}.py",
		coupled_code(stem, structure.get("description")),
	)

	### replace the placeholder diagram by the pickled diagram of the block
	### (SaveFile needs the GUI: without it, the archive keeps the placeholder)
	if wx.GetApp() is not None and not block.SaveFile(archive):
		sys.stderr.write(f"Cannot store the diagram of '{archive}'.\n")

	if canvas is not None:
		add_shape = getattr(canvas, "AddShape", None)

		if callable(add_shape):
			add_shape(block)

		if hasattr(block, "move"):
			x, y = _canvas_position(canvas, block, position)
			block.move(x, y)

	_refresh_canvas(block, canvas)

	return submodels, connections, added_inputs, added_outputs


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Generation steps
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### Steps of the generation of a coupled model, in their display order
GENERATION_STEPS = (
	("catalog", "Collect the model catalog"),
	("structure", "Ask the AI for the coupled structure"),
	("code", "Generate the code of the atomic models"),
	("merge", "Merge the structure with the PES"),
	("apply", "Build the coupled model in the diagram"),
	("store", "Store the SES in the model archive"),
)

### Steps of the generation of a SES
SES_STEPS = (
	("ses", "Ask the AI for the System Entity Structure"),
	("ses-store", "Store the SES in the model archive"),
)


def generation_steps(pes=None, generate_atomic_code=True):
	"""Return the ``(key, label)`` steps of a coupled model generation.

	The merge step only exists when the model is generated from a PES, and
	the code step is renamed when the atomic models are not generated.
	"""
	steps = []

	for key, label in GENERATION_STEPS:
		if key == "code" and not generate_atomic_code:
			label = "Build the atomic models without generated code"
		elif key == "merge" and pes is None:
			continue

		steps.append((key, label))

	return steps


def step_state_label(state):
	"""Return the translated label of the state of a step."""
	return _(STEP_APPEARANCE.get(state, STEP_APPEARANCE[STEP_PENDING])[0])


def step_state_colour(state):
	"""Return the colour of the state of a step."""
	return STEP_APPEARANCE.get(state, STEP_APPEARANCE[STEP_PENDING])[1]


class GenerationLog:
	"""Coloured, ordered log of the steps of a generation.

	The dialog adds the planned steps, then updates them as the generation
	runs. Every method runs on the GUI thread: the worker threads use
	``wx.CallAfter``.
	"""

	COLUMNS = (
		("Step", 330),
		("Status", 100),
		("Details", 420),
	)

	def __init__(self, control, header=None):
		self.control = control
		self.header = header
		self.rows = {}
		self._states = {}
		self.reset()

	def reset(self):
		"""Forget every step."""
		self.control.DeleteAllItems()
		self.rows = {}
		self._states = {}
		self._refresh_header()

	def add(self, key, label, detail="", state=STEP_PENDING):
		"""Append a step and return its row index."""
		if key in self.rows:
			self.update(key, state=state, detail=detail)
			return self.rows[key]

		row = self.control.InsertItem(self.control.GetItemCount(), label)
		self.rows[key] = row
		self._states[key] = state
		self.control.SetItem(row, 1, step_state_label(state))
		self.control.SetItem(row, 2, detail or "")
		self.control.SetItemTextColour(row, wx.Colour(*step_state_colour(state)))
		self.control.EnsureVisible(row)
		self._refresh_header()

		return row

	def update(self, key, state=None, detail=None):
		"""Change the state and/or the details of a step."""
		row = self.rows.get(key)

		if row is None:
			return

		if state is not None:
			self._states[key] = state
			self.control.SetItem(row, 1, step_state_label(state))
			self.control.SetItemTextColour(row, wx.Colour(*step_state_colour(state)))

		if detail is not None:
			self.control.SetItem(row, 2, detail)

		self.control.EnsureVisible(row)
		self._refresh_header()

	def running(self):
		"""Return the keys of the steps that are still running."""
		return [key for key, state in self._states.items() if state == STEP_RUNNING]

	def state(self, key):
		"""Return the state of a step (``STEP_PENDING`` when it is unknown)."""
		return self._states.get(key, STEP_PENDING)

	def fail_running(self, detail=""):
		"""Mark every running step as failed."""
		for key in self.running():
			self.update(key, STEP_FAILED, detail or self.detail(key))

	def stop_running(self, detail=""):
		"""Mark every running step as skipped (generation stopped)."""
		for key in self.running():
			self.update(key, STEP_SKIPPED, detail or _("Stopped by the user."))

	def finish_running(self, detail=""):
		"""Mark every running step as done."""
		for key in self.running():
			self.update(key, STEP_DONE, detail or self.detail(key))

	def counts(self):
		"""Return the number of steps in each state."""
		counts = {state: 0 for state in STEP_APPEARANCE}

		for state in self._states.values():
			counts[state] = counts.get(state, 0) + 1

		return counts

	def detail(self, key):
		"""Return the details currently displayed for a step."""
		row = self.rows.get(key)

		return self.control.GetItemText(row, 2) if row is not None else ""

	def _refresh_header(self):
		if self.header is None:
			return

		total = len(self.rows)

		if not total:
			self.header.SetLabel(_("No generation has run yet."))
			self.header.GetParent().Layout()
			return

		counts = self.counts()
		completed = counts[STEP_DONE] + counts[STEP_SKIPPED]
		running = self.running()

		if running:
			row = self.rows[running[-1]]
			label = _("Step {index}/{total}: {title}...").format(
				index=row + 1,
				total=total,
				title=self.control.GetItemText(row, 0),
			)
		elif counts[STEP_FAILED]:
			label = _("{completed}/{total} step(s) completed, {failed} failed.").format(
				completed=completed,
				total=total,
				failed=counts[STEP_FAILED],
			)
		else:
			label = _("{completed}/{total} step(s) completed.").format(
				completed=completed,
				total=total,
			)

		self.header.SetLabel(label)
		self.header.GetParent().Layout()


class WrappedLabel(wx.StaticText):
	"""Static text that wraps to the width of its parent.

	A single-line ``wx.StaticText`` is clipped when its text is longer than
	the panel that holds it. This label keeps the original text and wraps it
	again every time its parent is resized, so the sentences of the
	assistant stay readable.
	"""

	def __init__(self, parent, label="", colour=None, hint=600):
		super().__init__(parent, label=label)

		self._raw_text = str(label or "")
		self._wrap_width = 0
		### width used until the parent is laid out
		self._hint = hint

		if colour is not None:
			self.SetForegroundColour(colour)

		parent.Bind(wx.EVT_SIZE, self._on_parent_size)

		self._wrap()

	def SetLabel(self, label):
		"""Set the text and wrap it to the current width."""
		self._raw_text = str(label or "")
		self._wrap_width = 0
		self._wrap()

	def GetLabel(self):
		"""Return the text before wrapping."""
		return self._raw_text

	def _wrap(self):
		parent_width = self.GetParent().GetClientSize().width - 20
		laid_out = parent_width >= 280
		width = parent_width if laid_out else self._hint

		if width == self._wrap_width:
			return

		self._wrap_width = width
		wx.StaticText.SetLabel(self, self._raw_text)

		if self._raw_text:
			self.Wrap(width)

		### the text is wrapped again by the first size event of the parent
		if laid_out:
			self.GetParent().Layout()

	def _on_parent_size(self, event):
		event.Skip()
		self._wrap()


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Assistant dialog
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class ModelSelector:
	"""Model chooser shared by the AI assistants of the plug-in.

	It reproduces the model chooser of the atomic-model AI assistant (the AI
	panel of the editor): the current model is shown, the refresh button lists
	the models of the provider, and the selection is stored in
	``builtins.PARAMS_IA`` so that every assistant uses the same model.
	"""

	def __init__(self, parent, on_change=None):
		self.parent = parent
		self.on_change = on_change
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.label = wx.StaticText(parent, label=_("Model:"))
		self.sizer.Add(self.label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

		self.choice = wx.ComboBox(
			parent,
			wx.NewIdRef(),
			value="",
			choices=[],
			style=wx.CB_READONLY,
		)
		self.choice.Bind(wx.EVT_COMBOBOX, self.on_choice)
		self.sizer.Add(self.choice, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

		self.refresh_button = wx.BitmapButton(
			parent,
			wx.NewIdRef(),
			load_and_resize_image("db_refresh.png"),
			size=(28, 28),
		)
		self.refresh_button.SetToolTip(_("Refresh available models"))
		self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh)
		self.sizer.Add(self.refresh_button, 0, wx.ALIGN_CENTER_VERTICAL)

		self.reload()

	def _provider(self):
		"""Return the AI provider selected in the Preferences."""
		return getattr(builtins, "SELECTED_IA", "") or ""

	def reload(self):
		"""Show the model stored for the selected AI provider."""
		provider = self._provider()
		key = model_setting_key(provider)
		current = current_model_name(provider)

		self.choice.Clear()

		if current:
			self.choice.Append(current)
			self.choice.SetValue(current)

		if key:
			self.choice.SetToolTip(_("Model used by {provider}.").format(provider=provider))
		else:
			self.choice.SetToolTip(_("Select an AI provider in the Preferences."))

		self.set_enabled(bool(key))

	def set_enabled(self, enabled=True):
		"""Enable/disable the chooser (disabled while a generation runs)."""
		enabled = bool(enabled) and bool(model_setting_key(self._provider()))

		for widget in (self.label, self.choice, self.refresh_button):
			try:
				widget.Enable(enabled)
			except RuntimeError:
				### the dialog has already been destroyed
				pass

	def selected_model(self):
		"""Return the model shown by the chooser."""
		return self.choice.GetValue().strip()

	def on_choice(self, event):
		"""Store the model chosen by the user."""
		model_name = self.selected_model()

		if self.on_change is not None:
			self.on_change(model_name)

	def on_refresh(self, event):
		"""List the models available from the selected provider."""
		provider = self._provider()

		if not provider:
			return

		try:
			models = provider_models(provider)
		except Exception as error:
			wx.MessageBox(
				_("Could not refresh models:\n%s") % error,
				_("Model Refresh Failed"),
				wx.OK | wx.ICON_ERROR,
				self.parent,
			)
			return

		if not models:
			wx.MessageBox(
				_("No models are available from the selected provider."),
				_("Model Refresh Failed"),
				wx.OK | wx.ICON_ERROR,
				self.parent,
			)
			return

		current = current_model_name(provider)

		self.choice.Clear()
		self.choice.AppendItems(models)
		self.choice.SetValue(current if current in models else models[0])

		if self.on_change is not None:
			self.on_change(self.selected_model())


class SESPruningDialog(wx.Dialog):
	"""Prune an SES interactively and return the resulting PES.

	The dialog asks the decisions of the SES one after the other. For every
	decision the AI words the question and recommends an answer, the user
	chooses an alternative (specialization, aspect) or the number of
	instances (multiple-aspect), and the PES tree on the left is updated
	immediately. ``Finish`` is enabled once every reachable decision is
	answered; ``pes`` then holds the pruned entity structure.
	"""

	### width of the question column (the tree takes the remaining room)
	QUESTION_WIDTH = 380

	def __init__(
		self,
		parent,
		ses,
		prompt="",
		ontology_text="",
		adapter=None,
		session=None,
		answers=None,
	):
		screen_width, screen_height = wx.DisplaySize()

		super().__init__(
			parent,
			id=wx.ID_ANY,
			title=_("Prune the SES"),
			size=(min(1040, screen_width - 60), min(760, screen_height - 80)),
		)

		self.ses = normalize_ses(ses)
		self.prompt = str(prompt or "")
		self.ontology_text = str(ontology_text or "")
		self.adapter = adapter
		self.session = (
			session if session is not None else restore_pruning_session(self.ses, answers)
		)
		self.pes = None
		self.answers = []
		self._current = None
		self._undone = {}
		self._option_buttons = []
		self._spin = None
		self._question_plain = ""
		self._hint_plain = ""
		self._guidance = {}
		self._guidance_pending = set()
		self._stop_event = threading.Event()
		self._closing = False

		self._build_ui()
		self.Bind(wx.EVT_CLOSE, self.on_close_window)
		self._refresh()
		self.Center()

	### ------------------------------------------------------------------
	### User interface
	### ------------------------------------------------------------------
	def _build_ui(self):
		"""Create the widgets of the dialog."""
		self.SetMinSize((860, 600))

		icon_bitmap = load_and_resize_image("coupled.png")
		icon = wx.Icon()
		icon.CopyFromBitmap(icon_bitmap)
		self.SetIcon(icon)

		panel = wx.Panel(self)
		self.panel = panel
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		header = WrappedLabel(
			panel,
			label=_(
				"Prune '{name}' one decision at a time. The AI asks the "
				"question, the PES on the left is updated after every answer, "
				"and 'Finish' builds the coupled model from the resulting PES."
			).format(name=str(self.ses.get("name") or "")),
		)
		main_sizer.Add(header, flag=wx.ALL | wx.EXPAND, border=10)

		self.progress_label = wx.StaticText(panel, label="")
		self.progress_label.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)
		main_sizer.Add(
			self.progress_label,
			flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
			border=10,
		)

		content = wx.BoxSizer(wx.HORIZONTAL)

		### PES ----------------------------------------------------------
		pes_static = wx.StaticBox(panel, label=_("Pruned entity structure (PES)"))
		pes_box = wx.StaticBoxSizer(pes_static, wx.VERTICAL)

		self.pes_header = WrappedLabel(pes_static, label="")
		self.pes_header.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)
		pes_box.Add(
			self.pes_header,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)

		self.pes_tree = wx.TreeCtrl(
			pes_static,
			style=(
				wx.TR_DEFAULT_STYLE
				| wx.TR_HAS_BUTTONS
				| wx.TR_LINES_AT_ROOT
				| wx.TR_FULL_ROW_HIGHLIGHT
				| wx.BORDER_SIMPLE
			),
		)
		self.pes_tree.SetIndent(18)
		self.pes_tree.AssignImageList(tree_image_list())
		self.pes_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_pes_selection)
		pes_box.Add(
			self.pes_tree,
			proportion=1,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=5,
		)

		self.pes_detail = wx.TextCtrl(
			pes_static,
			value="",
			size=(-1, 90),
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
		)
		pes_box.Add(
			self.pes_detail,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)

		content.Add(
			pes_box,
			proportion=1,
			flag=wx.EXPAND | wx.RIGHT,
			border=8,
		)

		### Question -----------------------------------------------------
		question_static = wx.StaticBox(panel, label=_("Question"))
		question_box = wx.StaticBoxSizer(question_static, wx.VERTICAL)

		self.question_panel = question_static
		self.question_panel.SetMinSize((self.QUESTION_WIDTH, -1))

		self.step_label = wx.StaticText(question_static, label="")
		self.step_label.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)
		question_box.Add(self.step_label, flag=wx.EXPAND | wx.ALL, border=5)

		self.context_label = WrappedLabel(
			question_static, label="", colour=wx.Colour(100, 100, 100)
		)
		question_box.Add(self.context_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

		self.question_text = WrappedLabel(question_static, label="")
		question_box.Add(
			self.question_text,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
			border=5,
		)

		self.hint_text = WrappedLabel(question_static, label="", colour=wx.Colour(90, 90, 90))
		question_box.Add(
			self.hint_text,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
			border=5,
		)

		self.answer_panel = wx.Panel(question_static)
		self.answer_sizer = wx.BoxSizer(wx.VERTICAL)
		self.answer_panel.SetSizer(self.answer_sizer)
		question_box.Add(
			self.answer_panel,
			proportion=1,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)

		self.ai_label = WrappedLabel(question_static, label="", colour=wx.Colour(60, 90, 150))
		question_box.Add(
			self.ai_label,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
			border=5,
		)

		content.Add(question_box, proportion=0, flag=wx.EXPAND)

		main_sizer.Add(
			content,
			proportion=1,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=10,
		)

		### Buttons ------------------------------------------------------
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.back_button = wx.Button(panel, label=_("Back"), size=(90, 32))
		self.back_button.SetToolTip(_("Forget the last answer."))
		self.back_button.Bind(wx.EVT_BUTTON, self.on_back)
		button_sizer.Add(self.back_button, flag=wx.RIGHT, border=8)

		self.skip_button = wx.Button(panel, label=_("Skip"), size=(90, 32))
		self.skip_button.SetToolTip(_("Accept the proposed answer."))
		self.skip_button.Bind(wx.EVT_BUTTON, self.on_skip)
		button_sizer.Add(self.skip_button, flag=wx.RIGHT, border=8)

		button_sizer.AddStretchSpacer()

		self.next_button = wx.Button(panel, label=_("Next"), size=(90, 32))
		self.next_button.SetToolTip(_("Record this answer and ask the next question."))
		self.next_button.Bind(wx.EVT_BUTTON, self.on_next)
		button_sizer.Add(self.next_button, flag=wx.RIGHT, border=8)

		self.finish_button = wx.Button(panel, label=_("Finish"), size=(110, 32))
		self.finish_button.SetToolTip(_("Build the PES and return it to the SES assistant."))
		self.finish_button.Bind(wx.EVT_BUTTON, self.on_finish)
		button_sizer.Add(self.finish_button, flag=wx.RIGHT, border=8)

		self.cancel_button = wx.Button(panel, wx.ID_CANCEL, _("Cancel"), size=(100, 32))
		self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
		button_sizer.Add(self.cancel_button)

		main_sizer.Add(button_sizer, flag=wx.EXPAND | wx.ALL, border=10)

		panel.SetSizer(main_sizer)
		panel.Layout()

	### ------------------------------------------------------------------
	### State
	### ------------------------------------------------------------------
	def _wrap_width(self):
		"""Return the width used to wrap the question texts."""
		width = self.question_panel.GetClientSize().width - 20

		return width if width > 120 else self.QUESTION_WIDTH - 40

	def _answer_wrap(self):
		"""Return the width used to wrap the descriptions of the options."""
		return max(220, self._wrap_width() - 24)

	def _refresh(self):
		"""Rebuild the PES tree and show the next question."""
		self._current = None
		self._option_buttons = []
		self._spin = None
		self.answer_sizer.Clear(delete_windows=True)

		self._refresh_pes(self.session.partial_pes())

		answered, known = self.session.progress()
		self.back_button.Enable(bool(self.session.history))

		decision = self.session.next_decision()

		if decision is None:
			self._show_complete()
			return

		self._show_decision(decision, answered, known)
		self.panel.Layout()

	def _show_complete(self):
		"""Display the completed state of the pruning."""
		self.progress_label.SetLabel(_("Pruning complete"))
		self.step_label.SetLabel(_("Every decision is answered"))
		self.context_label.SetLabel("")
		self._question_plain = _(
			"The PES below is the pruned entity structure. Click 'Finish' to "
			"build the coupled model from it."
		)
		self._hint_plain = _("You can still go back with 'Back' to change the last answers.")
		self.question_text.SetLabel(self._question_plain)
		self.question_text.Wrap(self._wrap_width())
		self.hint_text.SetLabel(self._hint_plain)
		self.hint_text.Wrap(self._wrap_width())
		self.ai_label.SetLabel("")
		self.next_button.Enable(False)
		self.skip_button.Enable(False)
		self.finish_button.Enable(True)
		self.question_panel.Layout()

	def _show_decision(self, decision, answered, known):
		"""Display ``decision`` and build its answer widgets."""
		self._current = decision
		guidance = self._guidance.get(decision["key"]) or {}

		self.progress_label.SetLabel(
			_("Decision {index} \u00b7 {answered}/{known} answered").format(
				index=answered + 1,
				answered=answered,
				known=known,
			)
		)
		self.step_label.SetLabel(
			_("{kind} \u2014 entity '{entity}'").format(
				kind=pruning_kind_label(decision["kind"]).capitalize(),
				entity=decision["entity"],
			)
		)

		trail = " > ".join(decision.get("trail") or ())
		self.context_label.SetLabel(_("Path: {path}").format(path=trail or "-"))

		self._question_plain = str(guidance.get("question") or pruning_question_text(decision))[
			:600
		]
		self._hint_plain = str(guidance.get("hint") or pruning_question_hint(decision))[:600]

		self.question_text.SetLabel(self._question_plain)
		self.question_text.Wrap(self._wrap_width())
		self.hint_text.SetLabel(self._hint_plain)
		self.hint_text.Wrap(self._wrap_width())

		self._build_answer(decision)
		self._show_guidance(decision, guidance)
		self._request_guidance(decision)

		self.next_button.Enable(True)
		self.skip_button.Enable(True)
		self.finish_button.Enable(False)
		self.question_panel.Layout()

	def _build_answer(self, decision):
		"""Create the radio buttons or the spin control of ``decision``."""
		### going back restores the answer that was just forgotten
		remembered = self._undone.get(decision["key"])

		if decision["kind"] == PRUNING_MULTIPLICITY:
			minimum = int(decision["min"] or 0)
			maximum = decision["max"]
			upper = int(maximum) if maximum is not None else max(minimum, MAX_PES_INSTANCES)
			initial = (
				minimum if remembered is None else _clamp_instances(remembered, minimum, maximum)
			)
			row = wx.BoxSizer(wx.HORIZONTAL)

			label = wx.StaticText(self.answer_panel, label=_("Instances:"))
			row.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

			self._spin = wx.SpinCtrl(
				self.answer_panel,
				min=minimum,
				max=max(minimum, upper),
				initial=initial,
			)
			self._spin.SetToolTip(
				_("Number of copies of '{child}'.").format(child=decision.get("child") or "?")
			)
			row.Add(self._spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

			range_label = wx.StaticText(
				self.answer_panel,
				label=_("SES range: {min}..{max}").format(
					min=minimum,
					max=maximum if maximum is not None else "*",
				),
			)
			range_label.SetForegroundColour(wx.Colour(100, 100, 100))
			row.Add(range_label, 0, wx.ALIGN_CENTER_VERTICAL)

			self.answer_sizer.Add(row, 0, wx.ALL, 6)

			return

		for index, option in enumerate(decision["options"]):
			name = str(option.get("name") or _("Alternative {n}").format(n=index + 1))
			button = wx.RadioButton(
				self.answer_panel,
				label=name,
				style=(wx.RB_GROUP if index == 0 else 0),
			)
			self.answer_sizer.Add(
				button,
				0,
				wx.LEFT | wx.RIGHT | wx.TOP,
				6,
			)
			self._option_buttons.append(button)

			description = " ".join(str(option.get("description") or "").split())

			if description:
				detail = wx.StaticText(self.answer_panel, label=description[:400])
				detail.SetForegroundColour(wx.Colour(110, 110, 110))
				detail.Wrap(self._answer_wrap())
				self.answer_sizer.Add(detail, 0, wx.LEFT | wx.RIGHT, 6)

		if self._option_buttons:
			index = remembered if isinstance(remembered, int) else 0

			if not 0 <= index < len(self._option_buttons):
				index = 0

			self._option_buttons[index].SetValue(True)

		self.answer_panel.Layout()

	def _current_value(self):
		"""Return the answer currently selected in the dialog."""
		if self._current is None:
			return None

		if self._current["kind"] == PRUNING_MULTIPLICITY:
			if self._spin is not None:
				return self._spin.GetValue()

			return self.session.default_answer(self._current)

		for index, button in enumerate(self._option_buttons):
			if button.GetValue():
				return index

		return 0

	### ------------------------------------------------------------------
	### PES tree
	### ------------------------------------------------------------------
	def _refresh_pes(self, pes):
		"""Display the current (partial) PES."""
		nodes = pes_tree_nodes(pes)
		root = fill_tree_ctrl(self.pes_tree, nodes)

		stats = pes_statistics(pes)
		submodels = stats["submodels"]

		if submodels > MAX_PES_SUBMODELS:
			submodel_text = _("more than {count}").format(count=MAX_PES_SUBMODELS)
		else:
			submodel_text = str(submodels)

		self.pes_header.SetLabel(
			_(
				"{entities} entity(ies) \u00b7 {leaves} leaf entity(ies) \u00b7 "
				"{multi} multiple-aspect(s) \u00b7 {instances} instance(s) \u00b7 "
				"{submodels} atomic submodel(s) \u00b7 depth {depth}"
			).format(
				entities=stats["entities"],
				leaves=stats["leaves"],
				multi=stats["multi_aspects"],
				instances=stats["instances"],
				submodels=submodel_text,
				depth=stats["depth"],
			)
		)

		width = self.pes_header.GetParent().GetClientSize().width

		if width > 100:
			self.pes_header.Wrap(width - 12)

		if root is not None and root.IsOk():
			self.pes_tree.SelectItem(root)
			self.pes_detail.SetValue(_describe_node(nodes[0]))
			self.pes_detail.ShowPosition(0)

		self.pes_header.GetParent().Layout()

	def on_pes_selection(self, event):
		"""Show the description of the selected PES node."""
		self.pes_detail.SetValue(_describe_node(self.pes_tree.GetItemData(event.GetItem())))
		self.pes_detail.ShowPosition(0)

	### ------------------------------------------------------------------
	### AI guidance
	### ------------------------------------------------------------------
	def _context_lines(self):
		"""Return the decisions already made, for the AI prompt."""
		decisions = {decision["key"]: decision for decision in self.session.decisions()}
		lines = []

		for key in self.session.history:
			decision = decisions.get(key)

			if decision is None:
				continue

			value = self.session.answers.get(key)

			if decision["kind"] == PRUNING_MULTIPLICITY:
				lines.append(
					_("{entity}: {variable} = {count}").format(
						entity=decision["entity"],
						variable=decision.get("variable") or decision.get("node") or "?",
						count=value,
					)
				)
				continue

			options = decision["options"]
			index = int(value or 0)
			name = (
				str(options[index].get("name") or "") if 0 <= index < len(options) else str(value)
			)
			lines.append(
				_("{entity}: {node} = {name}").format(
					entity=decision["entity"],
					node=decision.get("node") or _("aspect"),
					name=name,
				)
			)

		return lines

	def _request_guidance(self, decision):
		"""Ask the AI to word ``decision`` (in a background thread)."""
		key = decision["key"]

		if self.adapter is None or key in self._guidance or key in self._guidance_pending:
			return

		self._guidance_pending.add(key)
		prompt = pruning_question_prompt(
			decision,
			self.prompt,
			self.ontology_text,
			context=self._context_lines(),
		)
		adapter = self.adapter

		def worker():
			try:
				raw = adapter.generate_output(
					prompt,
					system_prompt=PRUNING_SYSTEM_PROMPT,
					stop_event=self._stop_event,
				)
				guidance = parse_pruning_guidance(raw)
			except Exception as error:
				guidance = {
					"question": "",
					"hint": "",
					"recommendation": "",
					"error": str(error),
				}

			wx.CallAfter(self._on_guidance, key, guidance)

		threading.Thread(target=worker, daemon=True).start()

	def _on_guidance(self, key, guidance):
		"""Store the AI answer and display it when it is still relevant."""
		self._guidance_pending.discard(key)

		if self._closing:
			return

		self._guidance[key] = guidance

		if self._current is None or self._current["key"] != key:
			return

		self._question_plain = str(
			guidance.get("question") or pruning_question_text(self._current)
		)[:600]
		self._hint_plain = str(guidance.get("hint") or pruning_question_hint(self._current))[:600]
		self.question_text.SetLabel(self._question_plain)
		self.question_text.Wrap(self._wrap_width())
		self.hint_text.SetLabel(self._hint_plain)
		self.hint_text.Wrap(self._wrap_width())
		self._show_guidance(self._current, guidance)
		self.question_panel.Layout()

	def _show_guidance(self, decision, guidance):
		"""Display the state or the recommendation of the AI guidance."""
		if self.adapter is None:
			self.ai_label.SetLabel(
				_("No AI provider is selected: the question is generated locally.")
			)
		elif not guidance:
			self.ai_label.SetLabel(_("AI is preparing this question..."))
		elif guidance.get("error"):
			self.ai_label.SetLabel(_("The AI did not answer: the question is generated locally."))
		else:
			index = _recommendation_index(decision, guidance.get("recommendation"))
			### an answer restored by 'Back' is not overwritten
			remembered = decision["key"] in self._undone

			if index is None:
				self.ai_label.SetLabel(_("AI guidance received."))
			elif decision["kind"] == PRUNING_MULTIPLICITY:
				if self._spin is not None and not remembered:
					self._spin.SetValue(index)

				self.ai_label.SetLabel(
					_("AI recommendation: {count} instance(s).").format(count=index)
				)
			else:
				if not remembered and 0 <= index < len(self._option_buttons):
					self._option_buttons[index].SetValue(True)

				name = (
					str(decision["options"][index].get("name") or "")
					if 0 <= index < len(decision["options"])
					else str(index + 1)
				)
				self.ai_label.SetLabel(_("AI recommendation: {name}.").format(name=name))

		self.ai_label.Wrap(self._wrap_width())

	### ------------------------------------------------------------------
	### Actions
	### ------------------------------------------------------------------
	def _answer(self, value):
		"""Record ``value`` for the current decision and refresh the view."""
		if self._current is None:
			return

		key = self._current["key"]

		try:
			self.session.answer(key, value)
		except SESError as error:
			wx.MessageBox(
				str(error),
				_("Invalid answer"),
				wx.OK | wx.ICON_WARNING,
				self,
			)
			return

		self._undone.pop(key, None)
		self._refresh()

	def on_next(self, event):
		"""Record the selected answer and show the next question."""
		self._answer(self._current_value())

	def on_skip(self, event):
		"""Accept the default answer of the current decision."""
		if self._current is None:
			return

		self._answer(self.session.default_answer(self._current))

	def on_back(self, event):
		"""Forget the last answer and show its question again."""
		if not self.session.history:
			return

		key = self.session.history[-1]
		value = self.session.answers.get(key)
		self.session.undo()

		if key is not None:
			self._undone[key] = value

		self._refresh()

	def on_finish(self, event):
		"""Build the PES and close the dialog."""
		if not self.session.is_complete():
			wx.MessageBox(
				_("Answer the remaining questions first."),
				_("Prune the SES"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
			return

		try:
			self.pes = self.session.pes()
		except SESError as error:
			wx.MessageBox(
				str(error),
				_("Prune the SES"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		self.answers = pruning_answers(self.session)
		self._stop_event.set()
		self._closing = True
		self.EndModal(wx.ID_OK)

	def on_cancel(self, event):
		"""Close the dialog without returning a PES."""
		self._stop_event.set()
		self._closing = True
		self.EndModal(wx.ID_CANCEL)

	def on_close_window(self, event):
		"""Close the dialog from the window manager."""
		self.on_cancel(event)


class SESAssistantDialog(wx.Dialog):
	"""Generate an SES and a coupled model from a prompt and an optional ontology."""

	def __init__(
		self,
		parent,
		block,
		adapter=None,
		canvas=None,
		create=False,
		position=None,
	):
		super().__init__(parent, id=wx.ID_ANY, title=_("SES Generator"))

		self.block = block
		self.canvas = canvas
		self.adapter = adapter
		self._adapter_signature = None
		self.create = bool(create)
		self.position = position
		self.ses = None
		self.structure = None
		self.pes = None
		self._pes_ses = None
		self._pruning_answers = None
		self.ontology_path = ""
		self.ontology_text = ""
		self._busy = False
		self._closing = False
		self._stop_event = threading.Event()
		self._thread = None
		### folder where the archive and the atomic models are written
		archive_dir = os.path.dirname(self._archive())

		if self.create or not archive_dir:
			self.output_dir = _model_directory(canvas, _restore_output_dir())
		else:
			### an existing model keeps its own folder
			self.output_dir = archive_dir

		self._can_choose_output = self.create or not is_model_archive(self._archive())

		self._build_ui()
		self._restore_payload()

		self.Bind(wx.EVT_CLOSE, self.on_close_window)
		self.Center()

		### the adapter itself is created on demand (see _ensure_adapter)
		if not getattr(builtins, "SELECTED_IA", ""):
			self._set_status(_("Generative AI must be selected in the Preferences."))

	def _ensure_adapter(self):
		"""Return the AI adapter, creating it on first use.

		The adapter is not created when the dialog opens: some providers need
		an API key or a running server, which must not happen before the user
		asks for a generation. It is recreated when the provider or the model
		changes, because the chooser is shared with the other AI assistants.
		"""
		signature = adapter_signature()

		if self.adapter is None:
			self.adapter = get_selected_adapter(self)
			self._adapter_signature = signature
		elif self._adapter_signature is not None and self._adapter_signature != signature:
			### the model may have been changed in another AI assistant
			self.adapter = get_selected_adapter(self)
			self._adapter_signature = signature

		return self.adapter

	def on_model_changed(self, model_name):
		"""Use the model chosen in the assistant for the next generation."""
		if not model_name:
			return

		if set_current_model(model_name):
			### recreated on demand by _ensure_adapter
			self.adapter = None
			self._set_status(_("Model set to {name}.").format(name=model_name))

	### ------------------------------------------------------------------
	### User interface
	### ------------------------------------------------------------------
	def _build_ui(self):
		"""Create the widgets of the dialog."""
		### fit the dialog on the screen: the SES tree and the JSON tabs need room
		screen_width, screen_height = wx.DisplaySize()
		self.SetSize((min(940, screen_width - 60), min(940, screen_height - 80)))
		self.SetMinSize((760, 560))

		icon_bitmap = load_and_resize_image("coupled.png")
		icon = wx.Icon()
		icon.CopyFromBitmap(icon_bitmap)
		self.SetIcon(icon)

		panel = wx.Panel(self)
		self.panel = panel
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		if self.create:
			info_text = _(
				"New coupled model: it will be created in the diagram when the "
				"generated model is applied."
			)
		else:
			info_text = _("Coupled model: {label} ({inputs} input(s), {outputs} output(s))").format(
				label=getattr(self.block, "label", "") or "-",
				inputs=getattr(self.block, "input", 0),
				outputs=getattr(self.block, "output", 0),
			)

		info = WrappedLabel(panel, label=info_text)
		main_sizer.Add(info, flag=wx.ALL | wx.EXPAND, border=10)

		archive = self._archive()
		archive_text = archive if not self.create else _("created with the model")
		### a path is elided in the middle instead of being clipped
		self.archive_label = wx.StaticText(
			panel,
			label=_("Archive: {path}").format(path=archive_text or _("not saved yet")),
			style=wx.ST_ELLIPSIZE_MIDDLE,
		)
		self.archive_label.SetForegroundColour(wx.Colour(100, 100, 100))
		main_sizer.Add(
			self.archive_label,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
			border=10,
		)

		### output folder of the generated model -------------------------
		output_row = wx.BoxSizer(wx.HORIZONTAL)

		self.output_label = wx.StaticText(panel, label="", style=wx.ST_ELLIPSIZE_MIDDLE)
		output_row.Add(self.output_label, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)

		self.output_button = wx.Button(panel, label=_("Change..."), size=(100, 28))
		self.output_button.Bind(wx.EVT_BUTTON, self.on_pick_output_dir)
		output_row.Add(
			self.output_button,
			flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
			border=8,
		)

		main_sizer.Add(
			output_row,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
			border=10,
		)
		self._refresh_output_label()

		### the AI model can be changed without leaving the assistant
		self.model_selector = ModelSelector(panel, on_change=self.on_model_changed)
		main_sizer.Add(
			self.model_selector.sizer,
			flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
			border=10,
		)

		### Request ------------------------------------------------------
		request_static = wx.StaticBox(panel, label=_("Request"))
		request_box = wx.StaticBoxSizer(request_static, wx.VERTICAL)

		self.prompt_input = wx.TextCtrl(
			request_static,
			value="",
			size=(-1, 80),
			style=wx.TE_MULTILINE,
		)
		self.prompt_input.SetHint(_("Describe the family of coupled models you want to model..."))
		request_box.Add(
			self.prompt_input,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)

		ontology_row = wx.BoxSizer(wx.HORIZONTAL)
		self.ontology_button = wx.Button(
			request_static, label=_("Ontology file..."), size=(140, 28)
		)
		self.ontology_button.SetToolTip(
			_("Optional: the SES is generated from the request alone without an ontology.")
		)
		self.ontology_button.Bind(wx.EVT_BUTTON, self.on_pick_ontology)
		ontology_row.Add(
			self.ontology_button,
			flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
			border=8,
		)

		self.ontology_clear_button = wx.Button(request_static, label=_("Clear"), size=(70, 28))
		self.ontology_clear_button.SetToolTip(_("Remove the loaded ontology."))
		self.ontology_clear_button.Bind(wx.EVT_BUTTON, self.on_clear_ontology)
		self.ontology_clear_button.Enable(False)
		ontology_row.Add(
			self.ontology_clear_button,
			flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
			border=8,
		)

		self.ontology_label = wx.StaticText(
			request_static, label=_("No ontology loaded (optional).")
		)
		ontology_row.Add(
			self.ontology_label,
			proportion=1,
			flag=wx.ALIGN_CENTER_VERTICAL,
		)

		request_box.Add(
			ontology_row,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=5,
		)

		self.ontology_preview = wx.TextCtrl(
			request_static,
			value="",
			size=(-1, 60),
			style=wx.TE_MULTILINE | wx.TE_READONLY,
		)
		request_box.Add(
			self.ontology_preview,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)

		main_sizer.Add(
			request_box,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=10,
		)

		### SES ----------------------------------------------------------
		ses_static = wx.StaticBox(panel, label=_("System Entity Structure"))
		ses_box = wx.StaticBoxSizer(ses_static, wx.VERTICAL)

		toolbar = wx.BoxSizer(wx.HORIZONTAL)

		self.generate_button = wx.Button(ses_static, label=_("Generate SES"), size=(140, 30))
		self.generate_button.Bind(wx.EVT_BUTTON, self.on_generate_ses)
		toolbar.Add(self.generate_button, flag=wx.RIGHT, border=8)

		self.prune_button = wx.Button(ses_static, label=_("Prune interactively..."), size=(190, 30))
		self.prune_button.SetToolTip(_("Answer the pruning questions of the AI and build the PES."))
		self.prune_button.Bind(wx.EVT_BUTTON, self.on_prune)
		toolbar.Add(self.prune_button, flag=wx.RIGHT, border=8)

		self.build_button = wx.Button(ses_static, label=_("Generate coupled model"), size=(190, 30))
		self.build_button.Bind(wx.EVT_BUTTON, self.on_generate_model)
		toolbar.Add(self.build_button, flag=wx.RIGHT, border=8)

		self.stop_button = wx.Button(ses_static, label=_("Stop"), size=(80, 30))
		self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)
		self.stop_button.Enable(False)
		toolbar.Add(self.stop_button, flag=wx.RIGHT, border=8)

		ses_box.Add(toolbar, flag=wx.EXPAND | wx.ALL, border=5)

		status_row = wx.BoxSizer(wx.HORIZONTAL)

		self.atomic_check = wx.CheckBox(
			ses_static,
			label=_("Generate the code of the atomic models"),
		)
		self.atomic_check.SetValue(True)
		status_row.Add(
			self.atomic_check,
			flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
			border=12,
		)

		ses_box.Add(status_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

		### the status is a full row: its sentences are long and must wrap
		self.status_label = WrappedLabel(ses_static, label="", colour=wx.Colour(60, 60, 60))
		ses_box.Add(
			self.status_label,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
			border=5,
		)

		self.gauge = wx.Gauge(
			ses_static,
			range=100,
			size=(-1, 8),
			style=wx.GA_HORIZONTAL | wx.GA_SMOOTH,
		)
		self.gauge.Hide()
		ses_box.Add(
			self.gauge,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
			border=5,
		)

		self.notebook = wx.Notebook(ses_static)

		json_page = wx.Panel(self.notebook)
		self.ses_text = wx.TextCtrl(
			json_page,
			value="",
			style=wx.TE_MULTILINE | wx.TE_RICH2,
		)
		self.ses_text.SetFont(
			wx.Font(
				10,
				wx.FONTFAMILY_TELETYPE,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)
		json_sizer = wx.BoxSizer(wx.VERTICAL)
		json_sizer.Add(self.ses_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
		json_page.SetSizer(json_sizer)

		tree_page = wx.Panel(self.notebook)

		### header: counts and number of variants described by the SES
		self.tree_header = WrappedLabel(
			tree_page,
			label=_("No SES yet: click 'Generate SES' to display the tree."),
		)
		self.tree_header.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)

		### legend of the four node kinds of the SES toolbox
		legend_row = wx.BoxSizer(wx.HORIZONTAL)

		for kind in NODE_KINDS:
			legend = wx.StaticText(
				tree_page,
				label=f"\u25a0 {_(kind_label(kind))}",
			)
			legend.SetForegroundColour(wx.Colour(*NODE_ICON[kind][1]))
			legend.SetToolTip(NODE_TOOLTIP[kind])
			legend_row.Add(
				legend,
				flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
				border=12,
			)

		tree_toolbar = wx.BoxSizer(wx.HORIZONTAL)

		self.expand_button = wx.Button(tree_page, label=_("Expand all"), size=(100, 26))
		self.expand_button.SetToolTip(_("Expand every node of the SES tree."))
		self.expand_button.Bind(wx.EVT_BUTTON, self.on_expand_tree)
		tree_toolbar.Add(
			self.expand_button,
			flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
			border=6,
		)

		self.collapse_button = wx.Button(tree_page, label=_("Collapse all"), size=(110, 26))
		self.collapse_button.SetToolTip(_("Collapse every node of the SES tree."))
		self.collapse_button.Bind(wx.EVT_BUTTON, self.on_collapse_tree)
		tree_toolbar.Add(
			self.collapse_button,
			flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
			border=18,
		)

		tree_toolbar.Add(legend_row, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)

		### the tree and the details of the selected node
		self.ses_tree = wx.TreeCtrl(
			tree_page,
			style=(
				wx.TR_DEFAULT_STYLE
				| wx.TR_HAS_BUTTONS
				| wx.TR_LINES_AT_ROOT
				| wx.TR_FULL_ROW_HIGHLIGHT
				| wx.BORDER_SIMPLE
			),
		)
		self.ses_tree.SetIndent(18)
		self.ses_tree.AssignImageList(self._tree_images())
		self.ses_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)

		### details of the selected node
		self.ses_detail = wx.TextCtrl(
			tree_page,
			value="",
			size=(-1, 96),
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
		)
		self.ses_detail.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)

		tree_footer = WrappedLabel(
			tree_page,
			label=_(
				"Alternating mode: entity nodes and descriptive nodes alternate. "
				"Pruning keeps one aspect per decision node and one alternative "
				"per specialization."
			),
			colour=wx.Colour(100, 100, 100),
		)

		tree_sizer = wx.BoxSizer(wx.VERTICAL)
		tree_sizer.Add(
			self.tree_header,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
			border=6,
		)
		tree_sizer.Add(tree_toolbar, flag=wx.EXPAND | wx.ALL, border=6)
		tree_sizer.Add(
			self.ses_tree,
			proportion=1,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=6,
		)
		tree_sizer.Add(
			self.ses_detail,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
			border=6,
		)
		tree_sizer.Add(
			tree_footer,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
			border=6,
		)
		tree_page.SetSizer(tree_sizer)

		pes_page = wx.Panel(self.notebook)

		self.pes_header = WrappedLabel(
			pes_page,
			label=_("No PES yet: click 'Prune interactively...' to answer the pruning questions."),
		)
		self.pes_header.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)

		self.pes_tree = wx.TreeCtrl(
			pes_page,
			style=(
				wx.TR_DEFAULT_STYLE
				| wx.TR_HAS_BUTTONS
				| wx.TR_LINES_AT_ROOT
				| wx.TR_FULL_ROW_HIGHLIGHT
				| wx.BORDER_SIMPLE
			),
		)
		self.pes_tree.SetIndent(18)
		self.pes_tree.AssignImageList(self._tree_images())
		self.pes_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_pes_selection)

		self.pes_detail = wx.TextCtrl(
			pes_page,
			value="",
			size=(-1, 96),
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
		)
		self.pes_detail.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)

		pes_footer = WrappedLabel(
			pes_page,
			label=_(
				"The PES keeps the entities and the multiple-aspects of the SES: "
				"the aspects are decomposed (AND), the chosen specialization "
				"alternative becomes a child, and every leaf entity becomes an "
				"atomic submodel of the coupled model."
			),
			colour=wx.Colour(100, 100, 100),
		)

		pes_sizer = wx.BoxSizer(wx.VERTICAL)
		pes_sizer.Add(self.pes_header, flag=wx.EXPAND | wx.ALL, border=6)
		pes_sizer.Add(
			self.pes_tree,
			proportion=1,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=6,
		)
		pes_sizer.Add(
			self.pes_detail,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
			border=6,
		)
		pes_sizer.Add(
			pes_footer,
			flag=wx.EXPAND | wx.ALL,
			border=6,
		)
		pes_page.SetSizer(pes_sizer)

		structure_page = wx.Panel(self.notebook)
		self.structure_text = wx.TextCtrl(
			structure_page,
			value="",
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
		)
		self.structure_text.SetFont(
			wx.Font(
				10,
				wx.FONTFAMILY_TELETYPE,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)
		structure_sizer = wx.BoxSizer(wx.VERTICAL)
		structure_sizer.Add(
			self.structure_text,
			proportion=1,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)
		structure_page.SetSizer(structure_sizer)

		### graphical view of the coupled model --------------------------
		preview_page = wx.Panel(self.notebook)

		preview_toolbar = wx.BoxSizer(wx.HORIZONTAL)

		self.preview_refresh_button = wx.Button(preview_page, label=_("Refresh"), size=(100, 26))
		self.preview_refresh_button.SetToolTip(
			_("Redraw the graphical view of the generated coupled model.")
		)
		self.preview_refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_preview)
		preview_toolbar.Add(
			self.preview_refresh_button,
			flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
			border=8,
		)

		self.preview_message = WrappedLabel(
			preview_page,
			label=_("No coupled model to display yet."),
			colour=wx.Colour(100, 100, 100),
		)

		self.structure_preview = StructurePreviewPanel(preview_page)

		preview_sizer = wx.BoxSizer(wx.VERTICAL)
		preview_sizer.Add(preview_toolbar, flag=wx.EXPAND | wx.ALL, border=5)
		preview_sizer.Add(
			self.preview_message,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=5,
		)
		preview_sizer.Add(
			self.structure_preview,
			proportion=1,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)
		preview_page.SetSizer(preview_sizer)

		### steps of the LLM-driven generation ---------------------------
		steps_page = wx.Panel(self.notebook)

		self.steps_header = wx.StaticText(steps_page, label=_("No generation has run yet."))
		self.steps_header.SetFont(
			wx.Font(
				wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(),
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)

		self.steps_list = wx.ListCtrl(
			steps_page,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
		)

		for index, (title, width) in enumerate(GenerationLog.COLUMNS):
			self.steps_list.InsertColumn(index, _(title), width=width)

		self.generation_log = GenerationLog(self.steps_list, header=self.steps_header)

		steps_footer = WrappedLabel(
			steps_page,
			label=_(
				"The steps are updated while the AI generates the model: the "
				"catalog of the existing models, the coupled structure, the code "
				"of the atomic models, the merge with the PES, the construction "
				"in the diagram and the storage of the SES."
			),
			colour=wx.Colour(100, 100, 100),
		)

		steps_sizer = wx.BoxSizer(wx.VERTICAL)
		steps_sizer.Add(self.steps_header, flag=wx.EXPAND | wx.ALL, border=6)
		steps_sizer.Add(
			self.steps_list,
			proportion=1,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=6,
		)
		steps_sizer.Add(steps_footer, flag=wx.EXPAND | wx.ALL, border=6)
		steps_page.SetSizer(steps_sizer)

		### the pages are compared by object in on_page_changed
		self.json_page = json_page
		self.tree_page = tree_page
		self.pes_page = pes_page
		self.structure_page = structure_page
		self.preview_page = preview_page
		self.steps_page = steps_page

		self.notebook.AddPage(json_page, _("SES (JSON)"))
		self.notebook.AddPage(tree_page, _("SES tree"))
		self.notebook.AddPage(pes_page, _("PES"))
		self.notebook.AddPage(structure_page, _("Coupled structure"))
		self.notebook.AddPage(preview_page, _("Graphical view"))
		self.notebook.AddPage(steps_page, _("Generation steps"))
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

		ses_box.Add(
			self.notebook,
			proportion=1,
			flag=wx.EXPAND | wx.ALL,
			border=5,
		)

		main_sizer.Add(
			ses_box,
			proportion=1,
			flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
			border=10,
		)

		### Buttons ------------------------------------------------------
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.help_button = wx.Button(panel, label=_("Help"), size=(100, 32))
		self.help_button.Bind(wx.EVT_BUTTON, self.on_help)
		button_sizer.Add(self.help_button, flag=wx.RIGHT, border=8)

		button_sizer.AddStretchSpacer()

		self.close_button = wx.Button(panel, wx.ID_CLOSE, _("Close"), size=(100, 32))
		self.close_button.Bind(wx.EVT_BUTTON, self.on_close)
		button_sizer.Add(self.close_button)

		main_sizer.Add(button_sizer, flag=wx.EXPAND | wx.ALL, border=10)

		panel.SetSizer(main_sizer)
		panel.Layout()

		### the empty graphical view explains what to do
		self._refresh_preview()

		self._pulse_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_pulse, self._pulse_timer)

	### ------------------------------------------------------------------
	### Payload
	### ------------------------------------------------------------------
	def _archive(self):
		"""Return the archive path of the coupled model block."""
		return str(getattr(self.block, "model_path", "") or "")

	def _model_name(self):
		"""Return the name of the coupled model block."""
		return str(getattr(self.block, "label", "") or "CoupledModel")

	def _refresh_output_label(self):
		"""Display the output folder, the archive and the state of the button."""
		if not hasattr(self, "output_label"):
			return

		self.output_label.SetLabel(_("Output folder: {path}").format(path=self.output_dir))

		if self.create:
			path = _("{name} (created with the model)").format(
				name=os.path.basename(self._archive()) or "CoupledModel.cmd"
			)
		else:
			path = self._archive() or _("not saved yet")

		self.archive_label.SetLabel(_("Archive: {path}").format(path=path))
		self.archive_label.SetToolTip(path)
		self.output_label.SetToolTip(self.output_dir)

		### the folder can only be chosen while the archive does not exist
		if hasattr(self, "output_button"):
			self.output_button.SetToolTip(
				_(
					"Folder where the archive of the generated coupled model and "
					"its atomic models are written."
				)
				if self._can_choose_output
				else _(
					"The model already has a location. Create a new coupled model "
					"to choose another output folder."
				)
			)
			self.output_button.Enable(self._can_choose_output and not self._busy)

		self.panel.Layout()

	def on_pick_output_dir(self, event):
		"""Choose the folder where the generated model is written."""
		if self._busy or not self._can_choose_output:
			return

		dialog = wx.DirDialog(
			self,
			_("Output folder of the generated coupled model"),
			defaultPath=self.output_dir or _model_directory(self.canvas),
			style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
		)

		try:
			if dialog.ShowModal() != wx.ID_OK:
				return

			directory = dialog.GetPath()
		finally:
			dialog.Destroy()

		self._set_output_dir(directory)

	def _set_output_dir(self, directory):
		"""Store the chosen folder and move the pending model into it."""
		directory = str(directory or "").strip()

		if not directory or not os.path.isdir(directory):
			return

		_remember_output_dir(directory)
		self.output_dir = directory
		_apply_pending_directory(self.block, self.output_dir, self._model_name())
		self._refresh_output_label()

	def _restore_payload(self):
		"""Restore the SES previously stored in the model archive."""
		payload = read_ses(self._archive())

		if not payload:
			return

		### the payload is kept on the block so a 'Save as' keeps the SES
		attach_ses_payload(self.block, payload)
		self.prompt_input.SetValue(str(payload.get("prompt") or ""))

		ontology = payload.get("ontology")

		if isinstance(ontology, dict):
			self.ontology_path = str(ontology.get("path") or "")
			self.ontology_text = str(ontology.get("text") or "")

			if self.ontology_text:
				self.ontology_preview.SetValue(_head(self.ontology_text))
				self._refresh_ontology_label()

		ses = payload.get("ses")

		if isinstance(ses, dict):
			try:
				ses = normalize_ses(ses)
			except SESError:
				ses = None

			if ses is not None:
				self.ses = ses
				self.ses_text.SetValue(json.dumps(ses, indent=2, ensure_ascii=False))
				self._refresh_tree(ses)
				self._set_status(_("SES restored from the model archive."))

		structure = payload.get("structure")

		if isinstance(structure, dict):
			self.structure = structure
			self.structure_text.SetValue(json.dumps(structure, indent=2, ensure_ascii=False))

		pes = payload.get("pes")

		if isinstance(pes, dict) and isinstance(self.ses, dict):
			self._set_pes(pes, self.ses)
			self._pruning_answers = payload.get("pruning_answers")

		### the folder chosen for a model that is not created yet
		if self._can_choose_output:
			self._set_output_dir(payload.get("output_dir"))
		elif os.path.dirname(self._archive()):
			### an existing model keeps its own folder
			self.output_dir = os.path.dirname(self._archive())
			self._refresh_output_label()

		self._refresh_preview()

	def _store_payload(self, prompt=None):
		"""Store the current SES in the model archive.

		Returns:
			tuple: ``(stored, message)``, where ``stored`` tells whether the
			archive was updated.
		"""
		archive = self._archive()

		if not is_model_archive(archive):
			return False, _("SES not stored: save the model first.")

		payload = build_ses_payload(
			self.ses,
			structure=self.structure,
			prompt=(self.prompt_input.GetValue().strip() if prompt is None else prompt),
			ontology_path=self.ontology_path,
			ontology_text=self.ontology_text,
			model_name=self._model_name(),
			pes=self._current_pes(self.ses),
			pruning_answers=(
				self._pruning_answers if self._current_pes(self.ses) is not None else None
			),
			output_dir=self.output_dir,
		)

		if not write_ses(archive, payload):
			return False, _("SES not stored: the model archive could not be updated.")

		### a later 'Save as' re-embeds the payload in the new archive
		attach_ses_payload(self.block, payload)

		return True, _("SES stored in {name}.").format(name=os.path.basename(archive))

	### ------------------------------------------------------------------
	### Graphical view of the coupled model
	### ------------------------------------------------------------------
	def _set_preview_status(self, message):
		"""Update the text shown above the graphical view."""
		self.preview_message.SetLabel(message or "")
		self.preview_page.Layout()

	def _refresh_preview(self):
		"""Draw the generated coupled model, or the plan of the PES.

		The structure is already normalized by the generation: it is drawn as
		it will be built. Before the generation, the submodels fixed by the
		PES are drawn without couplings, so the shape of the model is visible
		as soon as the SES is pruned.
		"""
		if not hasattr(self, "structure_preview"):
			return

		if isinstance(self.structure, dict):
			self.structure_preview.SetStructure(self.structure)
			self._set_preview_status(
				_("{submodels} submodel(s), {connections} connection(s).").format(
					submodels=len(self.structure.get("submodels") or []),
					connections=len(self.structure.get("connections") or []),
				)
			)
			return

		if isinstance(self.pes, dict):
			try:
				preview = pes_preview_structure(
					self.pes,
					name=self._model_name(),
					description=str(self.ses.get("description") or "") if self.ses else "",
				)
			except SESError as error:
				self.structure_preview.SetMessage(str(error))
				self._set_preview_status(_("The PES cannot be displayed."))
				return

			self.structure_preview.SetStructure(preview)
			self._set_preview_status(
				_(
					"Submodels fixed by the PES ({count}): the AI adds the ports "
					"and the couplings when the coupled model is generated."
				).format(count=len(preview["submodels"]))
			)
			return

		self.structure_preview.SetMessage(
			_(
				"No coupled model to display yet: generate the SES, prune it and "
				"click 'Generate coupled model'."
			)
		)
		self._set_preview_status(
			_("The graphical view shows the coupled model before it is built.")
		)

	def on_refresh_preview(self, event):
		"""Redraw the graphical view on demand."""
		self._refresh_preview()

	### ------------------------------------------------------------------
	### Generation steps
	### ------------------------------------------------------------------
	def _start_generation_log(self, steps):
		"""Reset the log and add the planned ``(key, label)`` steps."""
		self.generation_log.reset()

		for key, label in steps:
			self.generation_log.add(key, _(label))

	def _log_step(self, key, state=None, detail=None, label=None):
		"""Update a step of the generation log from any thread."""
		wx.CallAfter(self._apply_log_step, key, state, detail, label)

	def _apply_log_step(self, key, state=None, detail=None, label=None):
		"""Update a step of the generation log on the GUI thread."""
		if self._closing:
			return

		if label is not None and key not in self.generation_log.rows:
			self.generation_log.add(key, label, detail or "", state or STEP_PENDING)
			return

		self.generation_log.update(key, state=state, detail=detail)

	def _log_code_model(self, label):
		"""Add the generation of the code of one atomic model to the log."""
		self._apply_log_step(
			f"code:{label}",
			STEP_RUNNING,
			_("Generating the source of '{label}'...").format(label=label),
			label=_("Code of '{label}'").format(label=label),
		)
		self._set_status(_("Generating atomic model '{label}'...").format(label=label))

	def _finish_code_models(self, errors):
		"""Mark every atomic model code step as done, failed or skipped."""
		failed = {str(label) for label, _error in errors or []}
		stopped = self._stop_event.is_set()

		for key in [key for key in self.generation_log.rows if key.startswith("code:")]:
			label = key.split(":", 1)[1]
			current = self.generation_log.state(key)

			if current == STEP_DONE:
				continue

			### a stop leaves the sources that were not generated pending
			if stopped and current != STEP_FAILED:
				self.generation_log.update(
					key,
					STEP_SKIPPED,
					_("Stopped before the source was generated."),
				)
				continue

			state = STEP_FAILED if label in failed else STEP_DONE
			detail = (
				_("The source could not be generated: an empty model is used.")
				if state == STEP_FAILED
				else _("Source generated.")
			)
			self.generation_log.update(key, state, detail)

	def _select_steps_page(self):
		"""Show the generation steps while a generation runs."""
		self._show_page(self.steps_page)

	def _show_page(self, page):
		"""Select a page of the notebook."""
		index = self.notebook.FindPage(page)

		if index != wx.NOT_FOUND:
			self.notebook.SetSelection(index)

	### ------------------------------------------------------------------
	### Status and busy state
	### ------------------------------------------------------------------
	def _set_status(self, message):
		"""Update the status text of the toolbar."""
		self.status_label.SetLabel(message or "")
		self.panel.Layout()

	def _set_busy(self, busy, message=""):
		"""Enable/disable the controls while a generation runs."""
		self._busy = busy
		self.generate_button.Enable(not busy)
		self.prune_button.Enable(not busy)
		self.build_button.Enable(not busy)
		self.ontology_button.Enable(not busy)
		self.ontology_clear_button.Enable(not busy and bool(self.ontology_text.strip()))
		self.atomic_check.Enable(not busy)
		self.output_button.Enable(not busy and self._can_choose_output)
		self.stop_button.Enable(busy)

		if getattr(self, "model_selector", None) is not None:
			self.model_selector.set_enabled(not busy)

		self.gauge.Show(busy)

		if busy:
			self.gauge.Pulse()
			self._pulse_timer.Start(120)
		else:
			self._pulse_timer.Stop()

		self._set_status(message)

	def on_pulse(self, event):
		"""Animate the progress gauge."""
		if self._busy:
			self.gauge.Pulse()

	### ------------------------------------------------------------------
	### Ontology
	### ------------------------------------------------------------------
	def _refresh_ontology_label(self):
		"""Update the ontology file label and the clear button."""
		name = os.path.basename(self.ontology_path) if self.ontology_path else ""
		characters = len(self.ontology_text)

		if not name and not characters:
			self.ontology_label.SetLabel(_("No ontology loaded (optional)."))
		else:
			self.ontology_label.SetLabel(
				_("{name} ({characters} character(s) extracted)").format(
					name=name or _("embedded ontology"),
					characters=characters,
				)
			)

		self.ontology_clear_button.Enable(bool(name or characters))
		self.ontology_label.GetParent().Layout()
		self.panel.Layout()

	def on_pick_ontology(self, event):
		"""Ask the user for an ontology file and extract its text."""
		wildcard = _(
			"Ontology files|*.owl;*.rdf;*.xml;*.ttl;*.nt;*.n3;*.json;*.txt;*.md;"
			"*.yaml;*.yml;*.csv|All files|*.*"
		)

		with wx.FileDialog(
			self,
			_("Select an ontology"),
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dialog:
			if dialog.ShowModal() != wx.ID_OK:
				return

			path = dialog.GetPath()

		try:
			text = extract_ontology_text(path)
		except OSError as error:
			wx.MessageBox(
				_("The ontology cannot be read:\n{}").format(str(error)),
				_("Ontology"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		if not text.strip():
			wx.MessageBox(
				_("No text could be extracted from this ontology."),
				_("Ontology"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
			return

		self.ontology_path = path
		self.ontology_text = text
		self.ontology_preview.SetValue(_head(text))
		self._refresh_ontology_label()
		self._set_status(_("Ontology loaded: {name}.").format(name=os.path.basename(path)))

	def on_clear_ontology(self, event):
		"""Forget the loaded ontology: the SES is generated from the request only."""
		self.ontology_path = ""
		self.ontology_text = ""
		self.ontology_preview.SetValue("")
		self._refresh_ontology_label()
		self._set_status(_("Ontology removed: the SES will be generated from the request."))

	### ------------------------------------------------------------------
	### SES generation
	### ------------------------------------------------------------------
	def on_generate_ses(self, event):
		"""Generate the SES from the prompt and the optional ontology."""
		if self._busy:
			return

		prompt = self.prompt_input.GetValue().strip()

		if not prompt:
			wx.MessageBox(
				_("Describe the family of models first."),
				_("SES Generator"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
			return

		adapter = self._ensure_adapter()

		if adapter is None:
			wx.MessageBox(
				_("Generative AI must be selected in the Preferences."),
				_("SES Generator"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
			return

		### the ontology is optional: an empty text makes the AI rely on the
		### request only (see ses_user_prompt)
		ontology_text = self.ontology_text.strip()
		### a new model has no name yet: the AI chooses it from the SES
		model_name = None if self.create else self._model_name()
		self._stop_event.clear()

		### the log of a new run starts with the SES
		self._start_generation_log(SES_STEPS)
		detail = _("{prompt}").format(prompt=prompt)
		detail += _(" (with an ontology)") if ontology_text else _(" (without ontology)")
		self._apply_log_step("ses", STEP_RUNNING, detail)
		self._select_steps_page()
		self._set_busy(True, _("Generating the SES..."))

		def worker():
			try:
				ses = generate_ses(
					adapter,
					prompt,
					ontology_text,
					model_name=model_name,
					stop_event=self._stop_event,
				)
			except Exception as error:
				wx.CallAfter(self._on_ses_failed, error)
				return

			wx.CallAfter(self._on_ses_ready, ses, prompt)

		self._thread = threading.Thread(target=worker, daemon=True)
		self._thread.start()

	def _on_ses_ready(self, ses, prompt):
		"""Display a generated SES."""
		if self._closing:
			return

		self._set_busy(False)
		self.ses = ses
		self.ses_text.SetValue(json.dumps(ses, indent=2, ensure_ascii=False))
		self._refresh_tree(ses)

		### the previous coupled structure was pruned from another SES
		self.structure = None
		self.structure_text.SetValue("")
		self._clear_pes()

		stats = ses_statistics(ses)
		self._set_status(
			_(
				"SES generated: {entities} entity(ies), {aspects} aspect(s), "
				"{multi} multiple-aspect(s), {spec} specialization node(s)."
			).format(
				entities=stats["entities"],
				aspects=stats["aspects"],
				multi=stats["multi_aspects"],
				spec=stats["specializations"],
			)
		)

		self._apply_log_step(
			"ses",
			STEP_DONE,
			_(
				"{entities} entity(ies), {aspects} aspect(s), {multi} "
				"multiple-aspect(s), {spec} specialization node(s)."
			).format(
				entities=stats["entities"],
				aspects=stats["aspects"],
				multi=stats["multi_aspects"],
				spec=stats["specializations"],
			),
		)

		### show the tree, which is the graphical view of the SES
		self._show_page(self.tree_page)

		self._apply_log_step("ses-store", STEP_RUNNING)
		stored, message = self._store_payload(prompt=prompt)
		self._apply_log_step("ses-store", STEP_DONE if stored else STEP_SKIPPED, message)

		if not stored:
			self._set_status(f"{self.status_label.GetLabel()} {message}")

	def _on_ses_failed(self, error):
		"""Report a SES generation error."""
		if self._closing:
			return

		### a stop is not an error: the running steps are only skipped
		if self._stop_event.is_set():
			self.generation_log.stop_running(_("Stopped by the user."))
			self._set_busy(False, _("SES generation stopped."))
			return

		### the log keeps the reason: it tells the user what the AI broke
		reason = " ".join(str(error).split())

		self.generation_log.fail_running(
			_("The SES could not be generated: {reason}").format(reason=reason[:200])
		)
		self._set_busy(False, _("SES generation failed."))
		wx.MessageBox(
			_("The SES could not be generated:\n{}").format(str(error)),
			_("SES Generator"),
			wx.OK | wx.ICON_ERROR,
			self,
		)

	### ------------------------------------------------------------------
	### Coupled model generation
	### ------------------------------------------------------------------
	def _current_ses(self):
		"""Return the normalized SES written in the JSON tab, or None."""
		from CoupledStructure import parse_json_object

		text = self.ses_text.GetValue().strip()

		if not text:
			wx.MessageBox(
				_("Generate the SES first."),
				_("SES Generator"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
			return None

		try:
			return normalize_ses(parse_json_object(text))
		except Exception as error:
			wx.MessageBox(
				_("The SES is not valid:\n{}").format(str(error)),
				_("Invalid SES"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return None

	### ------------------------------------------------------------------
	### PES (interactive pruning)
	### ------------------------------------------------------------------
	def _current_pes(self, ses):
		"""Return the PES pruned from ``ses``, or None when it is stale."""
		if isinstance(self.pes, dict) and self._pes_ses == ses:
			return self.pes

		return None

	def _set_pes(self, pes, ses=None):
		"""Store the PES pruned from ``ses`` and display it."""
		self.pes = pes if isinstance(pes, dict) else None
		self._pes_ses = ses if self.pes is not None else None

		if self.pes is None:
			self._pruning_answers = None

		self._refresh_pes_tree()

	def _clear_pes(self):
		"""Forget the PES because the SES it was pruned from changed."""
		self._set_pes(None, None)

	def _refresh_pes_tree(self):
		"""Display the stored PES in the PES tab."""
		self.pes_tree.DeleteAllItems()
		self.pes_detail.SetValue("")

		if not isinstance(self.pes, dict):
			self.pes_header.SetLabel(
				_("No PES yet: click 'Prune interactively...' to answer the pruning questions.")
			)
			self.pes_header.GetParent().Layout()
			return

		nodes = pes_tree_nodes(self.pes)
		root = fill_tree_ctrl(self.pes_tree, nodes)
		stats = pes_statistics(self.pes)

		if stats["submodels"] > MAX_PES_SUBMODELS:
			submodels = _("more than {count}").format(count=MAX_PES_SUBMODELS)
		else:
			submodels = str(stats["submodels"])

		self.pes_header.SetLabel(
			_(
				"{entities} entity(ies) \u00b7 {leaves} leaf entity(ies) \u00b7 "
				"{multi} multiple-aspect(s) \u00b7 {instances} instance(s) \u00b7 "
				"{submodels} atomic submodel(s) \u00b7 depth {depth}"
			).format(
				entities=stats["entities"],
				leaves=stats["leaves"],
				multi=stats["multi_aspects"],
				instances=stats["instances"],
				submodels=submodels,
				depth=stats["depth"],
			)
		)

		width = self.pes_header.GetParent().GetClientSize().width

		if width > 100:
			self.pes_header.Wrap(width - 12)

		if root is not None and root.IsOk():
			self.pes_tree.SelectItem(root)
			self.pes_detail.SetValue(_describe_node(nodes[0]))
			self.pes_detail.ShowPosition(0)

		self.pes_header.GetParent().Layout()

	def on_pes_selection(self, event):
		"""Show the description of the selected PES node."""
		self.pes_detail.SetValue(_describe_node(self.pes_tree.GetItemData(event.GetItem())))
		self.pes_detail.ShowPosition(0)

	def on_prune(self, event):
		"""Prune the SES interactively and store the resulting PES."""
		if self._busy:
			return

		ses = self._current_ses()

		if ses is None:
			return

		self.ses = ses
		adapter = self._ensure_adapter()
		### the previous answers can be replayed while the SES is unchanged
		answers = self._pruning_answers if self._pes_ses == ses else None
		dialog = SESPruningDialog(
			self,
			ses,
			prompt=self.prompt_input.GetValue().strip(),
			ontology_text=self.ontology_text,
			adapter=adapter,
			answers=answers,
		)

		try:
			result = dialog.ShowModal()
			pes = dialog.pes
			answers = dialog.answers
		finally:
			dialog.Destroy()

		if result != wx.ID_OK or not isinstance(pes, dict):
			return

		self._set_pes(pes, ses)
		self._pruning_answers = answers

		stats = pes_statistics(pes)
		self._set_status(
			_(
				"PES built: {entities} entity(ies), {leaves} leaf entity(ies), "
				"{submodels} atomic submodel(s)."
			).format(
				entities=stats["entities"],
				leaves=stats["leaves"],
				submodels=stats["submodels"],
			)
		)

		page = self.notebook.FindPage(self.pes_tree.GetParent())

		if page != wx.NOT_FOUND:
			self.notebook.SetSelection(page)

		self._refresh_preview()
		self._store_payload()

	def on_generate_model(self, event):
		"""Prune the SES into a coupled model and apply it to the block."""
		if self._busy:
			return

		ses = self._current_ses()

		if ses is None:
			return

		adapter = self._ensure_adapter()

		if adapter is None:
			wx.MessageBox(
				_("Generative AI must be selected in the Preferences."),
				_("SES Generator"),
				wx.OK | wx.ICON_INFORMATION,
				self,
			)
			return

		### the interactive pruning fixes the submodels: when the SES changed
		### since the pruning, the PES is stale and the SES is used instead
		pes = self._current_pes(ses)

		if self.create:
			message = _(
				"A new coupled model will be created in the diagram from the "
				"generated model.\nContinue?"
			)
		else:
			message = _(
				"The content of the coupled model '{label}' will be replaced "
				"by the generated model.\nContinue?"
			).format(label=self._model_name())

		if pes is not None:
			try:
				pes_count = len(pes_submodels(pes))
			except SESError as error:
				wx.MessageBox(
					str(error),
					_("SES Generator"),
					wx.OK | wx.ICON_ERROR,
					self,
				)
				return

			if self.create:
				message = _(
					"A new coupled model will be created in the diagram from the "
					"PES pruned interactively: its {count} submodel(s) are "
					"fixed.\n\nContinue?"
				).format(count=pes_count)
			else:
				message = _(
					"The coupled model is generated from the PES pruned "
					"interactively: its {count} submodel(s) are fixed.\n\nContinue?"
				).format(count=pes_count)
		elif isinstance(self.pes, dict):
			if self.create:
				message = _(
					"A new coupled model will be created in the diagram. The SES "
					"changed since the last pruning: the model is generated from "
					"the SES.\n\nContinue?"
				)
			else:
				message = _(
					"The SES changed since the last pruning: the coupled model is "
					"generated from the SES.\n\nContinue?"
				)

		answer = wx.MessageBox(
			message,
			_("SES Generator"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
			self,
		)

		if answer != wx.YES:
			return

		prompt = self.prompt_input.GetValue().strip() or str(
			ses.get("description") or ses.get("name") or ""
		)
		generate_atomic_code = self.atomic_check.GetValue()
		### a new model has no name and no ports yet: the AI decides them
		model_name = None if self.create else self._model_name()
		inputs = None if self.create else int(getattr(self.block, "input", 0) or 0)
		outputs = None if self.create else int(getattr(self.block, "output", 0) or 0)

		self.ses = ses
		self._stop_event.clear()

		### the steps of the coupled model generation are appended to the log
		steps = generation_steps(pes=pes, generate_atomic_code=generate_atomic_code)
		self._start_generation_log(steps)
		self._select_steps_page()
		self._set_busy(True, _("Generating the coupled model..."))

		def progress(label):
			wx.CallAfter(self._log_code_model, label)

		def worker():
			errors = []

			try:
				from CoupledStructure import build_model_catalog

				self._log_step("catalog", STEP_RUNNING)
				catalog = build_model_catalog()
				self._log_step(
					"catalog",
					STEP_DONE,
					_("{count} model(s) available.").format(count=len(catalog)),
				)

				self._log_step(
					"structure",
					STEP_RUNNING,
					_("Pruning the PES.") if pes is not None else _("Pruning the SES."),
				)

				if pes is not None:
					structure = generate_coupled_structure_from_pes(
						adapter,
						prompt,
						pes,
						catalog=catalog,
						model_name=model_name,
						inputs=inputs,
						outputs=outputs,
						generate_atomic_code=generate_atomic_code,
						stop_event=self._stop_event,
					)
				else:
					structure = generate_coupled_structure(
						adapter,
						prompt,
						ses,
						catalog=catalog,
						model_name=model_name,
						inputs=inputs,
						outputs=outputs,
						generate_atomic_code=generate_atomic_code,
						stop_event=self._stop_event,
					)

				self._log_step(
					"structure",
					STEP_DONE,
					_("{submodels} submodel(s), {connections} connection(s) proposed.").format(
						submodels=len(structure.get("submodels") or []),
						connections=len(structure.get("connections") or []),
					),
				)

				if pes is not None:
					self._log_step(
						"merge",
						STEP_RUNNING,
						_("Keeping the submodels fixed by the PES."),
					)
					self._log_step(
						"merge",
						STEP_DONE,
						_("{count} submodel(s) kept from the PES.").format(
							count=len(pes_submodels(pes))
						),
					)

				if generate_atomic_code:
					self._log_step("code", STEP_RUNNING)
					generate_missing_submodel_code(
						structure,
						adapter,
						stop_event=self._stop_event,
						progress=progress,
						errors=errors,
					)
				else:
					downgrade_behavior_submodels(structure)
					self._log_step(
						"code",
						STEP_SKIPPED,
						_("The atomic models are built without generated code."),
					)
			except Exception as error:
				wx.CallAfter(self._on_structure_failed, error)
				return

			wx.CallAfter(self._on_structure_ready, structure, prompt, errors)

		self._thread = threading.Thread(target=worker, daemon=True)
		self._thread.start()

	def _on_structure_ready(self, structure, prompt, errors):
		"""Apply a generated coupled structure to the block."""
		if self._closing:
			return

		self.structure = structure
		self.structure_text.SetValue(json.dumps(structure, indent=2, ensure_ascii=False))

		self._finish_code_models(errors)

		if "code" in self.generation_log.running():
			if self._stop_event.is_set():
				self.generation_log.update(
					"code",
					STEP_SKIPPED,
					_("Stopped by the user: the remaining models are empty."),
				)
			else:
				self.generation_log.update(
					"code",
					STEP_DONE,
					_("{generated} source(s) generated, {failed} failed.").format(
						generated=len(
							[
								submodel
								for submodel in structure.get("submodels") or []
								if str(submodel.get("code") or "").strip()
							]
						),
						failed=len(errors or []),
					),
				)

		self.generation_log.update("apply", STEP_RUNNING)

		created = self.create

		try:
			if created:
				submodels, connections, added_inputs, added_outputs = finalize_pending_block(
					self.block,
					structure,
					self.canvas,
					self.position,
				)
				### the block now lives in the diagram: later runs update it
				self.create = False
				### its archive exists: moving the folder would break the model
				self._can_choose_output = False
			else:
				submodels, connections, added_inputs, added_outputs = apply_structure_to_block(
					self.block, structure, self.canvas
				)
		except Exception as error:
			self.generation_log.update("apply", STEP_FAILED, str(error))
			self._set_busy(False, _("The coupled model could not be built."))
			wx.MessageBox(
				_("The generated structure could not be applied to the coupled model:\n{}").format(
					str(error)
				),
				_("SES Generator"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		self.generation_log.update(
			"apply",
			STEP_DONE,
			_("{submodels} submodel(s), {connections} connection(s) created.").format(
				submodels=submodels,
				connections=connections,
			),
		)

		self._refresh_output_label()

		self._set_busy(False)
		self._set_status(
			_(
				"Coupled model generated: {submodels} submodel(s), {connections} connection(s)."
			).format(
				submodels=submodels,
				connections=connections,
			)
		)

		stored, stored_message = self._store_payload(prompt=prompt)
		self.generation_log.update(
			"store",
			STEP_DONE if stored else STEP_SKIPPED,
			stored_message,
		)

		### the graphical view shows what was built in the diagram
		self._refresh_preview()
		self._show_page(self.preview_page)

		details = [
			_("{submodels} submodel(s) and {connections} connection(s) were created.").format(
				submodels=submodels, connections=connections
			)
		]

		if created:
			details.insert(
				0,
				_("Coupled model '{name}' created in the diagram.").format(name=self.block.label),
			)

		if added_inputs or added_outputs:
			details.append(
				_(
					"{inputs} input port(s) and {outputs} output port(s) were "
					"added to the coupled model."
				).format(
					inputs=added_inputs,
					outputs=added_outputs,
				)
			)

		details.append(stored_message)

		if created:
			details.append(
				_("The archive {name} was written in {folder}.").format(
					name=os.path.basename(self._archive()),
					folder=os.path.dirname(self._archive()) or self.output_dir,
				)
			)

		if errors:
			details.append(
				_(
					"The code of {count} atomic model(s) could not be "
					"generated; an empty model was created instead."
				).format(count=len(errors))
			)

		details.append(_("Save the model to keep the generated diagram."))

		wx.MessageBox(
			"\n\n".join(details),
			_("SES Generator"),
			wx.OK | wx.ICON_INFORMATION,
			self,
		)

	def _on_structure_failed(self, error):
		"""Report a coupled model generation error."""
		if self._closing:
			return

		### a stop is not an error: the running steps are only skipped
		if self._stop_event.is_set():
			self.generation_log.stop_running(_("Stopped by the user."))
			self._set_busy(False, _("Coupled model generation stopped."))
			return

		self.generation_log.fail_running(str(error))
		self._set_busy(False, _("Coupled model generation failed."))
		wx.MessageBox(
			_("The coupled model could not be generated:\n{}").format(str(error)),
			_("SES Generator"),
			wx.OK | wx.ICON_ERROR,
			self,
		)

	### ------------------------------------------------------------------
	### Tree
	### ------------------------------------------------------------------
	def _tree_images(self):
		"""Return the image list of the SES tree (one icon per node kind)."""
		return tree_image_list()

	def _update_tree_header(self, ses):
		"""Display the counts and the variant count of ``ses`` above the tree."""
		if not isinstance(ses, dict):
			self.tree_header.SetLabel(_("No SES yet: click 'Generate SES' to display the tree."))
			return

		stats = ses_statistics(ses)

		if stats["variants"] is None:
			variants = _("more than {count}").format(count=MAX_SES_VARIANTS)
		else:
			variants = str(stats["variants"])

		self.tree_header.SetLabel(
			_(
				"{entities} entity(ies) \u00b7 {aspects} aspect(s) (Dec) \u00b7 "
				"{multi} multiple-aspect(s) (MultiAspect) \u00b7 {spec} "
				"specialization node(s) (Spec) \u00b7 {alternatives} "
				"alternative(s) \u00b7 {variants} variant(s) \u00b7 depth {depth}"
			).format(
				entities=stats["entities"],
				aspects=stats["aspects"],
				multi=stats["multi_aspects"],
				spec=stats["specializations"],
				alternatives=stats["alternatives"],
				variants=variants,
				depth=stats["depth"],
			)
		)

		### the counts can be long: wrap the header on the width of the page
		width = self.tree_header.GetParent().GetClientSize().width

		if width > 100:
			self.tree_header.Wrap(width - 12)

	def _refresh_tree(self, ses):
		"""Display ``ses`` in the tree tab."""
		self.ses_tree.DeleteAllItems()
		self.ses_detail.SetValue("")
		self._update_tree_header(ses)

		nodes = ses_tree_nodes(ses)
		root = fill_tree_ctrl(self.ses_tree, nodes)

		if root is None or not root.IsOk():
			return

		self.ses_tree.SelectItem(root)
		self.ses_detail.SetValue(_describe_node(nodes[0]))
		self.ses_detail.ShowPosition(0)
		self.tree_header.GetParent().Layout()

	def on_tree_selection(self, event):
		"""Show the description of the selected node."""
		node = self.ses_tree.GetItemData(event.GetItem())
		self.ses_detail.SetValue(_describe_node(node))
		self.ses_detail.ShowPosition(0)

	def on_expand_tree(self, event):
		"""Expand every node of the SES tree."""
		if self.ses_tree.GetRootItem().IsOk():
			self.ses_tree.ExpandAll()

	def on_collapse_tree(self, event):
		"""Collapse every node of the SES tree."""
		root = self.ses_tree.GetRootItem()

		if root.IsOk():
			self.ses_tree.CollapseAll()
			self.ses_tree.SelectItem(root)

	def _refresh_tree_from_text(self):
		"""Refresh the tree from the JSON currently displayed."""
		from CoupledStructure import parse_json_object

		text = self.ses_text.GetValue().strip()

		if not text:
			return

		try:
			ses = normalize_ses(parse_json_object(text))
		except Exception:
			### keep the last valid tree while the user is editing
			return

		### a PES pruned from another SES is stale
		if ses != self.ses:
			self._clear_pes()

		self.ses = ses
		self._refresh_tree(ses)

	def on_page_changed(self, event):
		"""Refresh the tree and the graphical view when their tab is selected."""
		if event is not None:
			event.Skip()

		page = self.notebook.GetCurrentPage()

		if page is self.tree_page:
			self._refresh_tree_from_text()
		elif page is self.preview_page:
			self._refresh_preview()

	### ------------------------------------------------------------------
	### Help and closing
	### ------------------------------------------------------------------
	def on_help(self, event):
		"""Explain how the plug-in is used."""
		wx.MessageBox(
			_(
				"SES Generator - Help\n\n"
				"0. Right-click a coupled model block, the background of its "
				"diagram, or the background of a model diagram (even empty), "
				"and choose 'Generate SES / AI model...'.\n\n"
				"1. Describe the family of coupled models you want to model.\n\n"
				"2. Optionally load an ontology (OWL/RDF/XML, JSON, Turtle or "
				"plain text). Its extracted text is sent with the request and "
				"drives the entity names. Without an ontology the AI derives "
				"them from the request alone; 'Clear' removes it.\n\n"
				"3. Click 'Generate SES': the AI returns a System Entity "
				"Structure that follows the SES toolbox of the CEA (Wismar "
				"University of Applied Sciences): entity nodes (the real "
				"nodes), aspect nodes (Dec, decomposition into parts), "
				"multiple-aspect nodes (MultiAspect, replication of one entity "
				"with a variable and a range) and specialization nodes (Spec, "
				"XOR between alternatives). The axioms are enforced: "
				"alternating mode, strict hierarchy, uniformity, valid "
				"siblings and assigned variables.\n\n"
				"4. Check the SES in the 'SES (JSON)' tab or in the 'SES tree' "
				"tab. The tree colours and icons show the node kinds, the "
				"header counts the nodes and the variants (PES) the SES "
				"describes, and the panel below the tree explains the selected "
				"node. 'Expand all'/'Collapse all' browse large trees. The "
				"JSON can be edited before it is used.\n\n"
				"5. Click 'Prune interactively...' to prune the SES step by "
				"step. The AI asks the question of every decision (which "
				"specialization alternative, which aspect, how many instances "
				"of a multiple-aspect), recommends an answer, and the PES tree "
				"is updated after every answer. 'Back' forgets the last "
				"answer, 'Skip' accepts the proposed one and 'Finish' returns "
				"the resulting PES, displayed in the 'PES' tab.\n\n"
				"6. Click 'Generate coupled model': the coupled DEVS model is "
				"generated from the PES when one was pruned (its submodels are "
				"fixed), otherwise the AI prunes the SES itself. The structure "
				"replaces the content of the selected coupled model block, or "
				"creates a new coupled model block in the diagram when the "
				"menu was opened on its background. The 'Generation steps' tab "
				"follows the whole process (catalog, AI structure, atomic model "
				"code, merge with the PES, construction, storage) and the "
				"'Graphical view' tab draws the resulting coupled model.\n\n"
				"7. The output folder, shown above the tabs, is the folder "
				"where the archive of a new coupled model and its atomic "
				"models are written. 'Change...' selects another one; it is "
				"remembered for the next model.\n\n"
				"8. Save the model to keep the generated diagram. The SES, the "
				"PES, the pruning answers and the output folder are stored in "
				"the model archive (ses.json). The SES is restored when the "
				"assistant is opened again on that model, so it can be pruned "
				"again, and it is re-embedded after every save."
			),
			_("SES Generator - Help"),
			wx.OK | wx.ICON_INFORMATION,
			self,
		)

	def on_stop(self, event):
		"""Ask the running generation to stop."""
		if not self._busy or self._stop_event.is_set():
			return

		self._stop_event.set()
		self.stop_button.Enable(False)
		self._set_status(_("Stop requested; waiting for the current answer..."))

	def _confirm_close(self):
		"""Return True when the dialog may be closed."""
		if not self._busy:
			return True

		answer = wx.MessageBox(
			_("A generation is running. Stop it and close the dialog?"),
			_("SES Generator"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
			self,
		)

		if answer != wx.YES:
			return False

		self._stop_event.set()

		return True

	def on_close(self, event):
		"""Close the dialog from the Close button."""
		if not self._confirm_close():
			return

		self._closing = True
		self._pulse_timer.Stop()
		self.EndModal(wx.ID_CLOSE)

	def on_close_window(self, event):
		"""Close the dialog from the window manager."""
		if not self._confirm_close():
			if event is not None and event.CanVeto():
				event.Veto()
			return

		self._closing = True
		self._pulse_timer.Stop()
		self.EndModal(wx.ID_CLOSE)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Plug-in hooks
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _is_container_block(shape):
	"""Return True when ``shape`` is a coupled model block."""
	try:
		from Container import ContainerBlock
	except Exception:
		return False

	return isinstance(shape, ContainerBlock)


def _menu_canvas(menu):
	"""Return the canvas that opened ``menu`` when it is available."""
	for name in ("_ShapePopupMenu__canvas", "canvas", "_Menu__canvas"):
		canvas = getattr(menu, name, None)

		if canvas is not None:
			return canvas

	return None


def _plugin_enabled():
	"""Return False when the plug-in has been disabled by the plug-in manager."""
	return PLUGIN_NAME not in PluginManager.disabled_plugin


def _canvas_block(canvas):
	"""Return the coupled model block displayed by ``canvas``, if any.

	The diagram of a coupled model is displayed in a canvas whose diagram is
	the block itself. A canvas showing one abstraction layer of a diagram
	keeps the layers and the frame, so both are inspected as a fallback.
	"""
	if canvas is None:
		return None

	diagram = getattr(canvas, "diagram", None)

	if _is_container_block(diagram):
		return diagram

	layers = getattr(canvas, "layers", None)

	if isinstance(layers, dict):
		for layer in layers.values():
			if _is_container_block(layer):
				return layer

	### a detached frame keeps the diagram it was created from
	frame = getattr(canvas, "parent", None)

	diagram = getattr(frame, "diagram", None)

	if _is_container_block(diagram):
		return diagram

	return None


def _canvas_blocks(canvas):
	"""Return the coupled model blocks a diagram canvas can be used for.

	The canvas of a coupled model diagram returns that block. The canvas of
	a model diagram returns the coupled model blocks it contains.
	"""
	block = _canvas_block(canvas)

	if block is not None:
		return [block]

	diagram = getattr(canvas, "diagram", None)

	get_shape_list = getattr(diagram, "GetShapeList", None)

	if not callable(get_shape_list):
		return []

	try:
		shapes = get_shape_list()
	except Exception:
		return []

	return [shape for shape in shapes if _is_container_block(shape)]


def _choose_block(blocks):
	"""Ask which coupled model block the assistant must edit."""
	if not blocks:
		return None

	if len(blocks) == 1:
		return blocks[0]

	dialog = wx.SingleChoiceDialog(
		None,
		_("Choose the coupled model block to edit:"),
		_("SES Generator"),
		[block.label for block in blocks],
	)

	try:
		if dialog.ShowModal() != wx.ID_OK:
			return None

		index = dialog.GetSelection()
	finally:
		dialog.Destroy()

	if 0 <= index < len(blocks):
		return blocks[index]

	return None


def _canvas_can_create(canvas):
	"""Return True when ``canvas`` can receive a new coupled model block.

	Only a model diagram can create a block: the canvas of a coupled model
	shows the inside of a block, whose submodels are added with the regular
	``New`` entry of its menu.
	"""
	if canvas is None or _canvas_block(canvas) is not None:
		return False

	try:
		from Container import Diagram
	except Exception:
		return False

	return isinstance(getattr(canvas, "diagram", None), Diagram)


def _choose_target(blocks, can_create):
	"""Return the ``(block, create)`` target chosen by the user.

	``block`` is the coupled model block to edit; ``create`` asks for a new
	block in the diagram. Both are falsy when the user cancels.
	"""
	if not can_create:
		return _choose_block(blocks), False

	if not blocks:
		return None, True

	labels = [block.label for block in blocks]
	labels.append(_(NEW_MODEL_LABEL))

	dialog = wx.SingleChoiceDialog(
		None,
		_("Choose the coupled model to build:"),
		_("SES Generator"),
		labels,
	)

	try:
		if dialog.ShowModal() != wx.ID_OK:
			return None, False

		index = dialog.GetSelection()
	finally:
		dialog.Destroy()

	if index == len(blocks):
		return None, True

	if 0 <= index < len(blocks):
		return blocks[index], False

	return None, False


def _menu_position(canvas):
	"""Return the canvas coordinates of the mouse when the entry is chosen."""
	if canvas is None:
		return None

	try:
		return canvas.ScreenToClient(wx.GetMousePosition())
	except Exception:
		return None


def _append_ses_item(menu, blocks, canvas, create=False):
	"""Append the plug-in entry to a menu opened on ``blocks``."""
	label = _(MENU_LABEL)

	### the two registered events may both fire for the same menu
	for item in menu.GetMenuItems():
		if item.GetItemLabelText() == label:
			return None

	item = wx.MenuItem(
		menu,
		wx.NewIdRef(),
		label,
		_("Generate a System Entity Structure and a coupled model with the Generative AI"),
	)
	item.SetBitmap(load_and_resize_image("coupled.png"))
	menu.Append(item)

	def on_select(event, models=tuple(blocks), target=canvas, can_create=create):
		position = _menu_position(target)
		block, new = _choose_target(models, can_create)

		if block is not None or new:
			open_ses_assistant(
				block,
				canvas=target,
				create=new,
				position=position,
			)

	target = canvas if canvas is not None else menu
	target.Bind(wx.EVT_MENU, on_select, id=item.GetId())

	return item


def _install_canvas_menu_hook():
	"""Add the plug-in entry to the contextual menu of a diagram.

	DEVSimPy does not send an event when the background of a diagram is
	right-clicked, so the menu builder of ``Menu.ShapeCanvasPopupMenu`` is
	wrapped at run time. The item is added when the canvas shows a coupled
	model block (its own diagram, or a model diagram that contains one) and
	when it shows a model diagram, even empty: the assistant then creates a
	new coupled model block in that diagram.
	"""
	try:
		from Menu import ShapeCanvasPopupMenu
	except Exception:
		return False

	current = ShapeCanvasPopupMenu._add_menu_items

	if getattr(current, "_ses_generator_hook", False):
		return True

	original = current

	def _add_menu_items(self, parent):
		original(self, parent)

		if not _plugin_enabled():
			return

		blocks = _canvas_blocks(parent)
		create = _canvas_can_create(parent)

		if not blocks and not create:
			return

		_append_ses_item(self.menu, blocks, parent, create=create)

	_add_menu_items._ses_generator_hook = True

	ShapeCanvasPopupMenu._add_menu_items = _add_menu_items

	return True


def _ses_on_model_changed(self, model_name):
	"""Use the model chosen in the coupled-model AI assistant.

	Bound to ``AIPrompterDialog`` by :func:`_install_coupled_model_selector_hook`.
	"""
	if not model_name:
		return

	if set_current_model(model_name):
		### recreated with the new model on the next request
		self.adapter = None


def _install_coupled_model_selector_hook():
	"""Add the model chooser to the coupled-model AI assistant.

	``AIPrompterDialog`` belongs to the project and is not modified: its user
	interface is extended at run time, like the diagram menu. The chooser is
	the one of the atomic-model AI assistant (the AI panel of the editor) and
	stores the selection in ``builtins.PARAMS_IA``.
	"""
	try:
		import AIPrompterDialog as module
	except Exception as error:
		_log(f"Coupled-model AI assistant not importable: {error}")
		return False

	cls = module.AIPrompterDialog

	### ``__init_ui`` is a private method: its name is mangled by Python
	init_ui_name = f"_{cls.__name__.lstrip('_')}__init_ui"
	original_init_ui = getattr(cls, init_ui_name, None)

	if original_init_ui is None:
		_log("The coupled-model AI assistant has no __init_ui method")
		return False

	if getattr(original_init_ui, "_ses_generator_hook", False):
		return True

	original_send = cls.on_send_ai
	original_finish = cls._finish_generation

	def __init_ui(self):
		original_init_ui(self)

		if not _plugin_enabled():
			return

		### the chooser is only added to the coupled-model assistant
		if getattr(self, "model_kind", "atomic") != "coupled":
			return

		panel = getattr(self, "_main_panel", None)
		sizer = panel.GetSizer() if panel is not None else None

		if sizer is None:
			return

		try:
			selector = ModelSelector(panel, on_change=self._ses_on_model_changed)
		except Exception as error:
			_log(f"Cannot add the model chooser: {error}")
			return

		self._ses_model_selector = selector
		sizer.Insert(0, selector.sizer, 0, wx.EXPAND | wx.ALL, 8)

		### keep the working area of the dialog: the chooser adds a row
		width, height = self.GetSize()
		extra = selector.sizer.GetMinSize()[1] + 16
		max_height = max(640, wx.DisplaySize()[1] - 80)

		self.SetSize((width, min(height + extra, max_height)))
		panel.Layout()

	def on_send_ai(self, event):
		selector = getattr(self, "_ses_model_selector", None)

		if selector is not None:
			### the original handler ignores a click while a generation runs
			if getattr(self, "_generation_active", False):
				return

			signature = adapter_signature()
			previous = getattr(self, "_ses_adapter_signature", None)

			### the adapter was reset when the model changed; the chooser is
			### shared, so the model may also have changed elsewhere
			if getattr(self, "adapter", None) is None or (
				previous is not None and previous != signature
			):
				self.adapter = get_selected_adapter(self)
				self._ses_adapter_signature = signature

			selector.set_enabled(False)

		original_send(self, event)

	def _finish_generation(self, *args, **kwargs):
		try:
			return original_finish(self, *args, **kwargs)
		finally:
			selector = getattr(self, "_ses_model_selector", None)

			if selector is not None:
				selector.set_enabled(True)

	__init_ui._ses_generator_hook = True

	setattr(cls, init_ui_name, __init_ui)
	cls.on_send_ai = on_send_ai
	cls._finish_generation = _finish_generation
	cls._ses_on_model_changed = _ses_on_model_changed

	return True


def open_ses_assistant(block, parent=None, canvas=None, create=False, position=None):
	"""Open the SES assistant on a coupled model block.

	When ``create`` is True (or no block is given), the assistant builds a
	new coupled model block in ``canvas`` instead of editing an existing one.
	"""
	if parent is None:
		try:
			from Utilities import getTopLevelWindow

			parent = getTopLevelWindow()
		except Exception:
			parent = None

	if create or block is None:
		block = create_pending_block(canvas, directory=_restore_output_dir())
		create = True

	dialog = SESAssistantDialog(
		parent,
		block,
		canvas=canvas,
		create=create,
		position=position,
	)

	try:
		dialog.ShowModal()
	finally:
		dialog.Destroy()


@PluginManager.register("ADD_STATE_TRAJECTORY_MENU", "ADD_WCOMP_STRATEGY_MENU")
def add_ses_menu(*args, **kwargs):
	"""Add the plug-in entry to the contextual menu of a coupled model."""
	### the diagram menu is patched lazily: the Menu module may not be loaded yet
	_install_canvas_menu_hook()
	_install_coupled_model_selector_hook()

	menu = kwargs.get("parent")
	model = kwargs.get("model")

	if menu is None or not _is_container_block(model):
		return

	_append_ses_item(menu, [model], _menu_canvas(menu))


def Config(parent):
	"""Explain how the plug-in is used (Preferences > Configure)."""
	### the menu of the diagrams is patched when the plug-in is configured
	_install_canvas_menu_hook()
	_install_coupled_model_selector_hook()
	install_ses_persistence_hook()

	wx.MessageBox(
		_(
			"SES Generator\n\n"
			"Right-click a coupled model block, the background of its "
			"diagram, or the background of a model diagram (even empty), and "
			"choose 'Generate SES / AI model...' to:\n"
			"- generate a System Entity Structure (SES toolbox elements: "
			"entity, aspect Dec, multiple-aspect MultiAspect, specialization "
			"Spec) from a prompt and an optional ontology;\n"
			"- prune it into a coupled DEVS model with the AI assistant;\n"
			"- follow the steps of the generation and display the resulting "
			"coupled model in a graphical view;\n"
			"- choose the folder where the archive of a new coupled model and "
			"its atomic models are written;\n"
			"- fill an existing coupled model block, or create a new one in "
			"the diagram;\n"
			"- choose the AI model in the SES assistant and in the coupled-model "
			"assistant (same chooser as the atomic-model assistant);\n"
			"- store the SES in the model archive (ses.json), restore it when "
			"the assistant is opened again on that model and keep it after "
			"every save.\n\n"
			"The ontology is optional: it can be an OWL/RDF/XML, JSON, "
			"Turtle or plain text file, and the request alone is enough "
			"without one."
		),
		_("SES Generator"),
		wx.OK | wx.ICON_INFORMATION,
		parent,
	)


def UnConfig():
	"""Hide the diagram menu entry while the plug-in is disabled.

	The contextual menu of a diagram is patched once (DEVSimPy has no event
	for it) and checks ``PluginManager.disabled_plugin`` each time it is
	built, so enabling the plug-in again restores the entry.
	"""


### the diagram contextual menu is patched as soon as the plug-in is loaded;
### the call is repeated from the plug-in hooks in case Menu is not ready yet
if not _install_canvas_menu_hook():
	_log("Diagram contextual menu not patched yet")

### the coupled-model AI assistant receives its model chooser the same way
_install_coupled_model_selector_hook()

### the SES of a coupled model is re-embedded after every save
if not install_ses_persistence_hook():
	_log("SES persistence hook not installed")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Self-test (no graphical display needed)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def _sample_ses():
	"""Return a small SES used by the self-test (SES toolbox notation)."""
	return {
		"name": "ProductionLine",
		"description": "A family of production lines",
		"specializations": [
			{
				"name": "automation",
				"entities": [
					{"name": "ManualLine", "aspects": []},
					{"name": "AutomatedLine", "aspects": []},
				],
			}
		],
		"aspects": [
			{
				"name": "processing",
				"entities": [
					{
						"name": "Machine",
						"aspects": [
							{
								"name": "parts",
								"entities": [{"name": "Sensor"}],
							}
						],
						"multi_aspects": [
							{
								"name": "stations",
								"variable": "numStations",
								"min": 1,
								"max": 4,
								"entity": {"name": "Station"},
							}
						],
					},
					{"name": "Buffer"},
				],
			}
		],
	}


def _self_test():
	"""Run the non-GUI tests of the plug-in helpers."""
	import tempfile

	print("Running SES generator self-tests...\n")

	### Normalization -------------------------------------------------
	ses = normalize_ses(_sample_ses())

	assert ses["name"] == "ProductionLine"
	assert [item["name"] for item in ses["specializations"]] == ["automation"]
	assert [item["name"] for item in ses["specializations"][0]["entities"]] == [
		"ManualLine",
		"AutomatedLine",
	]
	assert [item["name"] for item in ses["aspects"]] == ["processing"]
	assert ses["aspects"][0]["entities"][0]["multi_aspects"][0]["name"] == "stations"
	assert ses["aspects"][0]["entities"][0]["multi_aspects"][0]["variable"] == "numStations"

	### the wrapper form is accepted
	assert normalize_ses({"ses": _sample_ses()})["name"] == "ProductionLine"

	### multiplicities: ``(minimum, maximum)``, None when unbounded
	assert _parse_multiplicity(None) == (1, 1)
	assert _parse_multiplicity(3) == (3, 3)
	assert _parse_multiplicity("2") == (2, 2)
	assert _parse_multiplicity("2..5") == (2, 5)
	assert _parse_multiplicity("1..*") == (1, None)
	assert _parse_multiplicity("0..*") == (0, None)
	assert _parse_multiplicity("*") == (1, None)
	assert _parse_multiplicity("n") == (1, None)
	assert _parse_multiplicity({"min": 2, "max": 7}) == (2, 7)
	assert _parse_multiplicity({"min": 2}) == (2, None)
	assert _normalize_multiplicity(3) == 3
	assert _normalize_multiplicity("2") == 2
	assert _normalize_multiplicity("*") == MULTI_ASPECT
	assert _normalize_multiplicity("1..*") == MULTI_ASPECT

	### the toolbox suffix is stored once and added by the viewer
	assert _strip_node_suffix("physicalDec") == "physical"
	assert _strip_node_suffix("pageMultiAspect") == "page"
	assert _strip_node_suffix("genreSpec") == "genre"
	assert _strip_node_suffix("Dec") == "Dec"
	assert _strip_node_suffix("Machine") == "Machine"
	assert node_label(ASPECT, "physical") == "physicalDec"
	assert node_label(MULTI_ASPECT_KIND, "pages") == "pagesMultiAspect"
	assert node_label(SPECIALIZATION, "genre") == "genreSpec"
	assert node_label(ASPECT, "physicalDec") == "physicalDec"
	assert node_label(ENTITY, "Machine") == "Machine"
	assert kind_label(MULTI_ASPECT_KIND) == "Multiple-aspect (MultiAspect)"

	### a legacy aspect multiplicity becomes a multiple-aspect node
	legacy = normalize_ses(
		{
			"name": "Root",
			"aspects": [
				{
					"name": "pages",
					"multiplicity": "1..*",
					"entities": [{"name": "Page"}],
				}
			],
		}
	)

	assert legacy["aspects"] == []
	assert len(legacy["multi_aspects"]) == 1
	assert legacy["multi_aspects"][0]["min"] == 1
	assert legacy["multi_aspects"][0]["max"] is None
	assert legacy["multi_aspects"][0]["variable"] == "numRep_pages"
	assert legacy["multi_aspects"][0]["entity"]["name"] == "Page"

	fixed = normalize_ses(
		{
			"name": "Root",
			"aspects": [{"name": "pages", "multiplicity": 3, "entities": [{"name": "Page"}]}],
		}
	)

	assert (fixed["multi_aspects"][0]["min"], fixed["multi_aspects"][0]["max"]) == (3, 3)

	### the legacy list of specializations becomes one specialization node
	legacy_spec = normalize_ses({"name": "Root", "specializations": [{"name": "A"}, {"name": "B"}]})

	assert [node["name"] for node in legacy_spec["specializations"]] == ["Root"]
	assert [item["name"] for item in legacy_spec["specializations"][0]["entities"]] == [
		"A",
		"B",
	]

	### an aspect written with the singular key of a multiple-aspect is read
	singular = normalize_ses(
		{
			"name": "Warehouse",
			"aspects": [
				{"name": "storageQueue", "entity": {"name": "Pallet", "aspects": []}},
			],
		}
	)

	assert [item["name"] for item in singular["aspects"][0]["entities"]] == ["Pallet"]

	### an aspect without entity is still rejected (the AI repairs it)
	empty_aspect = {"name": "Warehouse", "aspects": [{"name": "storageType"}]}

	try:
		normalize_ses(empty_aspect)
	except SESError as error:
		assert "must declare at least one entity" in str(error)
	else:
		raise AssertionError("an aspect without entity must be rejected")

	### the repair prompt shows the answer and the broken rule
	repair_prompt = ses_repair_prompt(
		"Build a warehouse system",
		'{"name": "Warehouse", "aspects": [{"name": "storageType"}]}',
		"SES > aspect #1 'storageType' must declare at least one entity.",
		model_name="Warehouse",
	)

	assert "must declare at least one entity" in repair_prompt
	assert "storageType" in repair_prompt
	assert "Build a warehouse system" in repair_prompt
	assert "'Warehouse'" in repair_prompt
	assert '"entities"' in repair_prompt
	assert "Return only the JSON object" in repair_prompt

	### the generation repairs one invalid answer
	class RepairingAdapter:
		"""Adapter returning an invalid SES, then the corrected one."""

		def __init__(self, answers):
			self.answers = list(answers)
			self.prompts = []

		def generate_output(self, prompt, system_prompt=None, on_token=None, stop_event=None):
			self.prompts.append(prompt)
			return self.answers.pop(0)

	repairing = RepairingAdapter(
		[
			'{"name": "Warehouse", "aspects": [{"name": "storageType"}]}',
			(
				'{"name": "Warehouse", "aspects": [{"name": "storageType", '
				'"entities": [{"name": "Shelf"}]}]}'
			),
		]
	)

	repaired = generate_ses(repairing, "Build a warehouse system")

	assert repaired["name"] == "Warehouse"
	assert repaired["aspects"][0]["entities"][0]["name"] == "Shelf"
	assert len(repairing.prompts) == 2
	assert "cannot be used" in repairing.prompts[1]

	### two invalid answers raise a message with both errors
	failing = RepairingAdapter(
		[
			'{"name": "Warehouse", "aspects": [{"name": "storageType"}]}',
			'{"name": "Warehouse", "aspects": [{"name": "storageType"}]}',
		]
	)

	try:
		generate_ses(failing, "Build a warehouse system")
	except SESError as error:
		message = str(error)
		assert "invalid SES twice" in message
		assert "must declare at least one entity" in message
	else:
		raise AssertionError("two invalid answers must be reported")

	### a stopped generation is not repaired
	class StoppingAdapter(RepairingAdapter):
		"""Adapter which reports the stop of the user after its answer."""

		def __init__(self):
			super().__init__(['{"name": "Warehouse", "aspects": [{"name": "storageType"}]}'])

		def generate_output(self, prompt, system_prompt=None, on_token=None, stop_event=None):
			answer = super().generate_output(prompt, system_prompt, on_token, stop_event)

			if stop_event is not None:
				stop_event.set()

			return answer

	stopping = StoppingAdapter()

	try:
		generate_ses(stopping, "Build a warehouse system", stop_event=threading.Event())
	except SESError:
		pass
	else:
		raise AssertionError("a stopped generation must not be repaired")

	assert len(stopping.prompts) == 1

	### statistics
	stats = ses_statistics(ses)
	assert stats["entities"] == 7
	assert stats["aspects"] == 2
	assert stats["multi_aspects"] == 1
	assert stats["specializations"] == 1
	assert stats["alternatives"] == 2
	assert stats["descriptive"] == 4
	assert stats["decision_nodes"] == 2
	assert stats["depth"] == 4
	assert stats["variants"] == 8
	assert not stats["unbounded"]

	### an unbounded multiple-aspect has no finite variant count
	unbounded = ses_statistics(
		normalize_ses(
			{
				"name": "Root",
				"multi_aspects": [
					{"name": "pages", "min": 1, "max": None, "entity": {"name": "Page"}}
				],
			}
		)
	)

	assert unbounded["variants"] is None
	assert unbounded["unbounded"]

	### tree nodes
	tree = ses_tree_nodes(ses)
	assert len(tree) == 1
	assert tree[0]["kind"] == ENTITY
	assert tree[0]["label"] == "ProductionLine"
	assert tree[0]["badge"] == "decision: 2 alternatives"
	assert [child["kind"] for child in tree[0]["children"]] == [
		ASPECT,
		SPECIALIZATION,
	]
	assert [child["label"] for child in tree[0]["children"]] == [
		"processingDec",
		"automationSpec",
	]
	assert [child["label"] for child in tree[0]["children"][0]["children"]] == [
		"Machine",
		"Buffer",
	]
	assert [child["label"] for child in tree[0]["children"][1]["children"]] == [
		"ManualLine",
		"AutomatedLine",
	]

	machine = tree[0]["children"][0]["children"][0]
	assert machine["kind"] == ENTITY
	assert [child["kind"] for child in machine["children"]] == [
		ASPECT,
		MULTI_ASPECT_KIND,
	]
	assert machine["children"][1]["label"] == "stationsMultiAspect"
	assert machine["children"][1]["badge"] == "numStations = 1..4"
	assert [child["label"] for child in machine["children"][1]["children"]] == ["Station"]
	assert machine["badge"] == "decision: numStations"
	assert "MultiAspect" in _describe_node(machine["children"][1])
	assert _describe_node(tree[0]).startswith("Entity: ProductionLine")
	assert _tree_item_label(machine["children"][1]).startswith("stationsMultiAspect")

	### tree rows
	rows = ses_to_tree_rows(ses)
	assert [row["depth"] for row in rows[:4]] == [0, 1, 2, 3]
	assert rows[0]["kind"] == ENTITY
	assert rows[1]["kind"] == ASPECT
	assert [row["label"] for row in rows] == [
		"ProductionLine",
		"processingDec",
		"Machine",
		"partsDec",
		"Sensor",
		"stationsMultiAspect",
		"Station",
		"Buffer",
		"automationSpec",
		"ManualLine",
		"AutomatedLine",
	]
	assert ses_entity_names(ses) == [
		"ProductionLine",
		"Machine",
		"Sensor",
		"Station",
		"Buffer",
		"ManualLine",
		"AutomatedLine",
	]

	### Interactive pruning -------------------------------------------
	session = PruningSession(ses)
	assert session.progress() == (0, 1)
	assert not session.is_complete()

	first = session.next_decision()
	assert first["kind"] == PRUNING_SPECIALIZATION
	assert first["entity"] == "ProductionLine"
	assert first["node"] == "automation"
	assert [option["name"] for option in first["options"]] == [
		"ManualLine",
		"AutomatedLine",
	]
	assert first["key"] == (("decision", PRUNING_SPECIALIZATION, 0),)
	assert pruning_question_text(first)
	assert pruning_question_hint(first)
	assert _recommendation_index(first, "AutomatedLine") == 1
	assert _recommendation_index(first, "2") == 1
	assert _recommendation_index(first, "9") is None

	session.answer(first["key"], 1)
	second = session.next_decision()
	assert second["kind"] == PRUNING_MULTIPLICITY
	assert second["node"] == "stations"
	assert second["child"] == "Station"
	assert (second["min"], second["max"]) == (1, 4)
	assert session.progress() == (1, 2)
	assert _recommendation_index(second, "3 stations") == 3
	assert _recommendation_index(second, "0") == 1
	assert _recommendation_index(second, "9") == 4
	assert _clamp_instances(5, 1, 4) == 4
	assert _clamp_instances(0, 1, None) == 1
	assert _clamp_instances(500, 1, None) == MAX_PES_INSTANCES

	### an answer outside the choices or the range is rejected
	for value in (0, 9):
		try:
			session.answer(second["key"], value)
		except SESError:
			pass
		else:
			raise AssertionError(f"Multiplicity {value} was accepted")

	### undo forgets the last answer
	assert session.undo() == first["key"]
	assert session.next_decision()["kind"] == PRUNING_SPECIALIZATION

	session.answer(first["key"], 0)
	multi = session.next_decision()
	session.answer(multi["key"], 2)
	assert session.is_complete()

	### changing an earlier answer invalidates the answers that follow
	session.answer(first["key"], 1)
	assert multi["key"] not in session.answers
	assert session.next_decision()["kind"] == PRUNING_MULTIPLICITY

	session.answer(multi["key"], 3)
	assert session.is_complete()

	pes = session.pes()
	assert pes["kind"] == ENTITY
	assert pes["name"] == "ProductionLine"
	assert [child["name"] for child in pes["children"]] == [
		"AutomatedLine",
		"Machine",
		"Buffer",
	]

	machine = pes["children"][1]
	assert [child["name"] for child in machine["children"]] == ["Sensor", "stations"]

	stations = machine["children"][1]
	assert stations["kind"] == MULTI_ASPECT_KIND
	assert stations["count"] == 3
	assert stations["entity"]["name"] == "Station"

	pes_stats = pes_statistics(pes)
	assert pes_stats["entities"] == 6
	assert pes_stats["leaves"] == 4
	assert pes_stats["multi_aspects"] == 1
	assert pes_stats["instances"] == 3
	assert pes_stats["submodels"] == 6

	### the coupled model is flat: every leaf entity is an atomic submodel
	submodels = pes_submodels(pes)
	assert [entry["label"] for entry in submodels] == [
		"AutomatedLine",
		"Sensor",
		"Station1",
		"Station2",
		"Station3",
		"Buffer",
	]
	assert submodels[2]["entity"] == "Station"
	assert submodels[2]["path"] == ["ProductionLine", "Machine", "Station"]

	### the graphical view of a pruned SES shows its atomic submodels
	preview = pes_preview_structure(pes, name="ProductionLine")
	assert preview["name"] == "ProductionLine"
	assert [entry["label"] for entry in preview["submodels"]] == [
		entry["label"] for entry in submodels
	]
	assert preview["submodels"][0]["model"] == "AutomatedLine"
	assert preview["connections"] == []
	assert preview["inputs"] == 0
	assert preview["outputs"] == 0

	from CoupledStructurePreview import compute_preview_layout

	preview_layout = compute_preview_layout(preview)
	assert len(preview_layout["boxes"]) == len(submodels)
	assert preview_layout["connections"] == []
	assert preview_layout["width"] > 0
	assert preview_layout["height"] > 0

	### the steps of the generation follow the path of the model
	assert [key for key, _label in generation_steps()] == [
		"catalog",
		"structure",
		"code",
		"apply",
		"store",
	]
	assert [key for key, _label in generation_steps(pes=pes)] == [
		"catalog",
		"structure",
		"code",
		"merge",
		"apply",
		"store",
	]
	without_code = dict(generation_steps(pes=pes, generate_atomic_code=False))
	assert "without generated code" in without_code["code"]
	assert step_state_label(STEP_DONE) == STEP_APPEARANCE[STEP_DONE][0]
	assert step_state_colour(STEP_FAILED) == STEP_APPEARANCE[STEP_FAILED][1]

	pes_nodes = pes_tree_nodes(pes)
	assert pes_nodes[0]["label"] == "ProductionLine"
	assert [child["kind"] for child in pes_nodes[0]["children"]] == [
		ENTITY,
		ENTITY,
		ENTITY,
	]

	station_node = pes_nodes[0]["children"][1]["children"][1]
	assert station_node["kind"] == MULTI_ASPECT_KIND
	assert station_node["label"] == "stationsMultiAspect"
	assert station_node["badge"] == "numStations = 3"
	assert pes_to_tree_rows(pes)[0]["depth"] == 0

	### a partial PES flags the branches that still need a decision
	partial = PruningSession(ses).partial_pes()
	assert partial["pending"]
	assert [child["name"] for child in partial["children"]] == ["Machine", "Buffer"]
	assert partial["children"][0]["children"][1]["pending"]
	assert partial["children"][0]["children"][1]["count"] == 1

	### a single aspect is an AND decomposition: it is not a decision
	flat = PruningSession(
		normalize_ses({"name": "Root", "aspects": [{"name": "a", "entities": [{"name": "Leaf"}]}]})
	)
	assert flat.is_complete()
	assert flat.decisions() == []
	assert [entry["label"] for entry in pes_submodels(flat.pes())] == ["Leaf"]

	### several aspects of one entity are an XOR decision
	two_aspects = PruningSession(
		normalize_ses(
			{
				"name": "Root",
				"aspects": [
					{"name": "first", "entities": [{"name": "A"}]},
					{"name": "second", "entities": [{"name": "B"}]},
				],
			}
		)
	)
	aspect_decision = two_aspects.next_decision()
	assert aspect_decision["kind"] == PRUNING_ASPECT
	assert [option["name"] for option in aspect_decision["options"]] == [
		"first",
		"second",
	]
	two_aspects.answer(aspect_decision["key"], 1)
	assert [entry["label"] for entry in pes_submodels(two_aspects.pes())] == ["B"]

	### the answers are stored in the archive and replayed
	stored_answers = pruning_answers(session)
	assert stored_answers and all(isinstance(entry["key"], list) for entry in stored_answers)
	restored = restore_pruning_session(ses, stored_answers)
	assert restored.is_complete()
	assert restored.pes() == pes

	### the AI wording is parsed, plain text is kept as the question
	guidance = parse_pruning_guidance(
		'{"question": "Which line?", "hint": "Automated is faster.", '
		'"recommendation": "AutomatedLine"}'
	)
	assert guidance == {
		"question": "Which line?",
		"hint": "Automated is faster.",
		"recommendation": "AutomatedLine",
	}
	assert parse_pruning_guidance("Which line do you need?")["question"] == (
		"Which line do you need?"
	)
	assert parse_pruning_guidance("")["question"] == ""

	### the AI only chooses the ports and the couplings of the PES
	structure = {
		"name": "ProductionLine",
		"inputs": 2,
		"outputs": 2,
		"submodels": [
			{
				"label": label,
				"inputs": 2,
				"outputs": 2,
				"behavior": f"{label} behavior",
			}
			for label in [
				"AutomatedLine",
				"Sensor",
				"Station1",
				"Station2",
				"Station3",
				"Buffer",
				"Ghost",
			]
		],
		"connections": [
			{
				"source": "input",
				"source_port": 0,
				"target": "AutomatedLine",
				"target_port": 0,
			},
			{
				"source": "AutomatedLine",
				"source_port": 0,
				"target": "Station1",
				"target_port": 0,
			},
			{"source": "Station1", "source_port": 0, "target": "Ghost", "target_port": 0},
			{"source": "Ghost", "source_port": 0, "target": "Buffer", "target_port": 0},
			{
				"source": "Buffer",
				"source_port": 0,
				"target": "output",
				"target_port": 0,
			},
			{"source": "Sensor", "source_port": 0, "target": "Sensor", "target_port": 0},
			{"source": "Station2", "source_port": 5, "target": "Buffer", "target_port": 0},
			{"source": "input", "source_port": 3, "target": "Buffer", "target_port": 0},
		],
	}
	merged = merge_pes_structure(structure, submodels)
	assert [entry["label"] for entry in merged["submodels"]] == [
		entry["label"] for entry in submodels
	]
	assert all(entry["generate"] == "behavior" for entry in merged["submodels"])
	assert merged["submodels"][0]["behavior"] == "AutomatedLine behavior"
	assert merged["submodels"][0]["inputs"] == 2
	assert len(merged["connections"]) == 3
	assert [connection["source"] for connection in merged["connections"]] == [
		"input",
		"AutomatedLine",
		"Buffer",
	]

	pes_prompt = pes_coupled_prompt("build it", pes, submodels)
	assert "PES (JSON)" in pes_prompt
	assert "Station1" in pes_prompt
	assert "build it" in pes_prompt

	### the declared ports are grown to the ports used by the couplings
	### (the AI declares two outputs and couples the third one)
	from CoupledStructure import normalize_coupled_structure

	assembly = {
		"name": "AssemblyLine",
		"inputs": 1,
		"outputs": 1,
		"submodels": [
			{
				"label": "RobotInstance",
				"generate": "behavior",
				"behavior": "Welds a part.",
				"inputs": 1,
				"outputs": 2,
			},
			{
				"label": "ConveyorInstance",
				"generate": "behavior",
				"behavior": "Moves a part.",
				"inputs": 1,
				"outputs": 1,
			},
		],
		"connections": [
			{
				"source": "input",
				"source_port": 0,
				"target": "RobotInstance",
				"target_port": 0,
			},
			{
				"source": "RobotInstance",
				"source_port": 2,
				"target": "ConveyorInstance",
				"target_port": 0,
			},
			{
				"source": "ConveyorInstance",
				"source_port": 0,
				"target": "output",
				"target_port": 1,
			},
		],
	}

	grown = grow_declared_ports(assembly)

	assert grown is assembly
	assert grown["submodels"][0]["outputs"] == 3
	assert grown["submodels"][1]["outputs"] == 1
	assert grown["inputs"] == 1
	assert grown["outputs"] == 2

	grown_structure = normalize_coupled_structure(grown)

	assert grown_structure["submodels"][0]["outputs"] == 3
	assert grown_structure["outputs"] == 2
	assert len(grown_structure["connections"]) == 3

	### an untouched submodel keeps the counts chosen by the AI
	untouched = json.loads(
		json.dumps(
			{
				"submodels": [
					{
						"label": "Sink",
						"generate": "behavior",
						"behavior": "Consumes.",
						"inputs": 0,
						"outputs": 0,
					},
					{
						"label": "Source",
						"generate": "behavior",
						"behavior": "Emits.",
						"inputs": 1,
						"outputs": 1,
					},
				],
				"connections": [
					{
						"source": "Source",
						"source_port": 0,
						"target": "output",
						"target_port": 0,
					}
				],
			}
		)
	)

	grow_declared_ports(untouched)

	assert untouched["submodels"][0]["inputs"] == 0
	assert untouched["submodels"][0]["outputs"] == 0
	assert untouched["submodels"][1]["outputs"] == 1

	### the counts requested by the caller are kept when the answer omits them
	requested = json.loads(
		json.dumps(
			{
				"submodels": [{"label": "Gen", "generate": "behavior", "behavior": "Emits."}],
				"connections": [
					{"source": "Gen", "source_port": 0, "target": "output", "target_port": 0}
				],
			}
		)
	)

	grow_declared_ports(requested, inputs=4, outputs=4)

	assert "inputs" not in requested
	assert "outputs" not in requested

	requested_structure = normalize_coupled_structure(requested, inputs=4, outputs=4)

	assert requested_structure["inputs"] == 4
	assert requested_structure["outputs"] == 4

	### the aliases of the AI answer are grown in place
	aliases = {
		"submodels": [
			{"name": "Node", "generate": "behavior", "behavior": "Emits.", "nb_outputs": 1}
		],
		"connections": [{"from": "Node", "out_port": 1, "to": "output", "in_port": 0}],
	}

	grow_declared_ports(aliases)

	assert aliases["submodels"][0]["nb_outputs"] == 2
	assert aliases["outputs"] == 1

	### the PES generation grows the ports before merging the submodels
	class PortAdapter:
		"""Adapter returning the coupled structure of the assembly line."""

		def __init__(self, answer):
			self.answer = json.dumps(answer)

		def generate_coupled_model_json(self, prompt, **kwargs):
			return self.answer

	assembly_pes = normalize_ses(
		{
			"name": "AssemblyLine",
			"aspects": [
				{
					"name": "floor",
					"entities": [
						{"name": "RobotInstance", "description": "Welds a part."},
						{"name": "ConveyorInstance", "description": "Moves a part."},
					],
				}
			],
		}
	)

	assembly_session = PruningSession(assembly_pes)
	assembly_decision = assembly_session.next_decision()

	if assembly_decision is not None:
		assembly_session.answer(assembly_decision["key"], 0)

	built = generate_coupled_structure_from_pes(
		PortAdapter(json.loads(json.dumps(assembly))),
		"Build an assembly line",
		assembly_session.pes(),
		model_name="AssemblyLine",
	)

	assert [entry["label"] for entry in built["submodels"]] == [
		"RobotInstance",
		"ConveyorInstance",
	]
	assert built["submodels"][0]["outputs"] == 3
	assert len(built["connections"]) == 3
	assert built["outputs"] == 2

	### the answer is restricted to the PES before it is validated: a stray
	### submodel and a missing behavior do not invalidate the structure
	loose = {
		"name": "AssemblyLine",
		"submodels": [
			{"label": "robotinstance", "inputs": 1, "outputs": 3},
			{"label": "Ghost", "model": "UnknownModel"},
		],
		"connections": [
			{"source": "input", "target": "robotinstance"},
			{"source": "robotinstance", "source_port": 2, "target": "Ghost"},
			{"source": "Ghost", "target": "output"},
		],
	}

	restricted = restrict_to_pes(loose, pes_submodels(assembly_session.pes()))

	assert restricted is loose
	assert [entry["label"] for entry in restricted["submodels"]] == [
		"robotinstance",
		"ConveyorInstance",
	]
	assert all(entry["generate"] == "behavior" for entry in restricted["submodels"])
	assert restricted["submodels"][0]["behavior"] == "Welds a part."
	assert restricted["submodels"][1]["behavior"] == "Moves a part."
	assert len(restricted["connections"]) == 1

	loose_structure = normalize_coupled_structure(grow_declared_ports(restricted), catalog=[])

	assert [entry["label"] for entry in loose_structure["submodels"]] == [
		"robotinstance",
		"ConveyorInstance",
	]
	assert loose_structure["inputs"] == 1
	assert loose_structure["outputs"] == 0

	### the prompt of the PES says the submodels are generated
	assert "do not bind it to an existing model" in pes_coupled_prompt("build it", pes, submodels)

	### invalid SES ---------------------------------------------------
	def error_message(data):
		try:
			normalize_ses(data)
		except SESError as error:
			return str(error)
		raise AssertionError(f"An invalid SES was accepted: {data!r}")

	assert error_message("not a dict")
	assert "at least one entity" in error_message(
		{"name": "Root", "aspects": [{"name": "a", "entities": []}]}
	)
	### axiom of uniformity: an entity is declared only once
	assert "uniformity" in error_message(
		{
			"name": "A",
			"aspects": [
				{"name": "a", "entities": [{"name": "B"}]},
				{"name": "b", "entities": [{"name": "B"}]},
			],
		}
	)
	### axiom of strict hierarchy: no entity twice on one path
	assert "strict hierarchy" in error_message(
		{
			"name": "A",
			"aspects": [
				{
					"name": "a",
					"entities": [
						{
							"name": "B",
							"aspects": [{"name": "b", "entities": [{"name": "A"}]}],
						}
					],
				}
			],
		}
	)
	### valid siblings: two children of one aspect cannot share a name
	assert "uniformity" in error_message(
		{
			"name": "Root",
			"aspects": [{"name": "a", "entities": [{"name": "A"}, {"name": "A"}]}],
		}
	)
	### two descriptive nodes of the same kind cannot share a name
	assert "two aspect nodes" in error_message(
		{
			"name": "Root",
			"aspects": [
				{"name": "a", "entities": [{"name": "A"}]},
				{"name": "a", "entities": [{"name": "B"}]},
			],
		}
	)
	### a specialization needs at least two alternatives
	assert "two alternatives" in error_message(
		{"name": "Root", "specializations": [{"name": "s", "entities": [{"name": "A"}]}]}
	)
	### a multiple-aspect replicates exactly one entity
	assert "exactly one entity" in error_message(
		{
			"name": "Root",
			"multi_aspects": [{"name": "m", "entities": [{"name": "A"}, {"name": "B"}]}],
		}
	)
	### an aspect multiplicity cannot hide several entities
	assert "replicates a single entity" in error_message(
		{
			"name": "Root",
			"aspects": [
				{
					"name": "a",
					"multiplicity": "1..*",
					"entities": [{"name": "A"}, {"name": "B"}],
				}
			],
		}
	)
	assert "Invalid multiplicity" in error_message(
		{
			"name": "Root",
			"aspects": [{"name": "a", "multiplicity": "many!", "entities": [{"name": "A"}]}],
		}
	)
	### a nameless root entity falls back to a default name
	assert normalize_ses({"aspects": []})["name"] == "SES"
	assert "at least one entity" in error_message({"name": "Root", "aspects": [{"name": "a"}]})

	### the icons need a running wx.App; the self-test runs without one
	if wx.GetApp() is not None:
		icon = _node_bitmap(ENTITY)

		assert icon.IsOk()
		assert icon.GetSize() == (16, 16)

	### Prompts -------------------------------------------------------
	system_prompt = ses_system_prompt()
	assert "MultiAspect" in system_prompt
	assert "Alternating mode" in system_prompt
	assert "Strict hierarchy" in system_prompt
	assert "Uniformity" in system_prompt
	assert '"multi_aspects"' in system_prompt
	assert '"specializations"' in system_prompt

	user_prompt = ses_user_prompt("Build a line", "Machine Sensor")
	assert "Build a line" in user_prompt
	assert "Machine Sensor" in user_prompt

	### the ontology is optional: without it the AI relies on the request
	no_ontology_prompt = ses_user_prompt("Build a line", "")
	assert "No ontology was provided" in no_ontology_prompt
	assert "<<<ONTOLOGY" not in no_ontology_prompt
	assert "Build a line" in no_ontology_prompt
	### blank ontology text is treated as no ontology
	assert "No ontology was provided" in ses_user_prompt("Build a line", "   \n ")
	assert "derive the entity names from the request" in system_prompt

	### SES generation without an ontology ---------------------------
	class FakeSESAdapter:
		"""Stand-in adapter recording the prompts it receives."""

		def __init__(self):
			self.prompts = []

		def generate_output(self, prompt, system_prompt=None, on_token=None, stop_event=None):
			self.prompts.append((prompt, system_prompt))
			return json.dumps(_sample_ses())

	fake_adapter = FakeSESAdapter()
	generated_ses = generate_ses(fake_adapter, "Build a line")

	assert generated_ses["name"] == "ProductionLine"
	assert "No ontology was provided" in fake_adapter.prompts[0][0]
	assert "derive the entity names from the request" in fake_adapter.prompts[0][1]

	coupled_prompt = coupled_prompt_from_ses("Build a line", ses)
	assert '"ProductionLine"' in coupled_prompt
	assert "MultiAspect" in coupled_prompt
	assert "Build a line" in coupled_prompt

	### Ontology extraction -------------------------------------------
	with tempfile.TemporaryDirectory() as directory:

		def write(name, content):
			path = os.path.join(directory, name)

			with open(path, "w", encoding="utf-8") as stream:
				stream.write(content)

			return path

		json_text = extract_ontology_text(
			write("ontology.json", '{"classes": ["Machine", "Buffer"]}')
		)
		assert "Machine" in json_text
		assert "Buffer" in json_text

		owl_text = extract_ontology_text(
			write(
				"ontology.owl",
				'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
				'xmlns:owl="http://www.w3.org/2002/07/owl#">'
				'<owl:Class rdf:about="#Machine">'
				"<rdfs:label>Machine</rdfs:label>"
				"</owl:Class></rdf:RDF>",
			)
		)
		assert "Machine" in owl_text
		assert "<" not in owl_text

		broken_owl_text = extract_ontology_text(
			write("broken.owl", "<owl:Class>Machine &amp; Buffer</owl:Class")
		)
		assert "Machine & Buffer" in broken_owl_text

		ttl_text = extract_ontology_text(
			write("ontology.ttl", "# a comment\n:Machine a owl:Class .\n")
		)
		assert ttl_text == ":Machine a owl:Class ."

		plain_text = extract_ontology_text(write("ontology.txt", "Machine\n"))
		assert plain_text == "Machine"

		long_text = extract_ontology_text(
			write("long.txt", "x" * 500),
			max_chars=100,
		)
		assert long_text.endswith("[ontology truncated]")
		assert len(long_text) < 160

		assert extract_ontology_text("") == ""

		### a missing file raises OSError, which the dialog reports
		try:
			extract_ontology_text(os.path.join(directory, "missing.json"))
		except OSError:
			pass
		else:
			raise AssertionError("A missing ontology file was accepted.")

		### Model archive -------------------------------------------
		archive = os.path.join(directory, "ProductionLine.cmd")

		with zipfile.ZipFile(archive, "w") as stream:
			stream.writestr("ProductionLine.py", "# model\n")
			stream.writestr("DEVSimPyModel.dat", b"diagram")

		assert is_model_archive(archive)
		assert read_ses(archive) is None
		assert not is_model_archive(os.path.join(directory, "missing.cmd"))

		payload = build_ses_payload(
			ses,
			structure={"name": "ProductionLine", "submodels": []},
			prompt="Build a line",
			ontology_path="ontology.owl",
			ontology_text="Machine",
			model_name="ProductionLine",
			output_dir=directory,
		)

		assert write_ses(archive, payload)
		loaded = read_ses(archive)

		assert loaded["ses"]["name"] == "ProductionLine"
		assert loaded["structure"]["name"] == "ProductionLine"
		assert loaded["prompt"] == "Build a line"
		assert loaded["ontology"]["path"] == "ontology.owl"
		assert loaded["ontology"]["text"] == "Machine"
		assert loaded["output_dir"] == directory
		assert loaded["version"] == SES_PAYLOAD_VERSION

		with zipfile.ZipFile(archive, "r") as stream:
			names = stream.namelist()

		assert names.count(SES_ENTRY) == 1
		assert "ProductionLine.py" in names
		assert "DEVSimPyModel.dat" in names

		### an update replaces the entry instead of duplicating it
		payload["prompt"] = "Updated line"
		assert write_ses(archive, payload)

		with zipfile.ZipFile(archive, "r") as stream:
			assert stream.namelist().count(SES_ENTRY) == 1

		assert read_ses(archive)["prompt"] == "Updated line"

		### a non archive is rejected
		plain_file = write("plain.txt", "not an archive")

		assert not write_ses(plain_file, payload)
		assert read_ses(plain_file) is None

		### the SES of a block survives the next save of its archive
		class FakeBlock:
			"""Stand-in for a coupled model block."""

			ses_payload = payload

		assert persist_ses_entry(FakeBlock(), archive)
		assert read_ses(archive)["prompt"] == "Updated line"
		assert not persist_ses_entry(object(), archive)
		assert not persist_ses_entry(FakeBlock(), plain_file)

		### the output folder of a new model is honoured
		assert _model_directory(None, directory) == directory
		assert os.path.isdir(_model_directory(None, os.path.join(directory, "missing")))

		class FakePending:
			"""Stand-in for a coupled model block not yet written."""

			label = "CoupledModel"
			model_path = ""
			python_path = ""
			last_name_saved = ""

		pending = FakePending()

		assert _apply_pending_directory(pending, directory, "CoupledModel")
		assert pending.model_path == os.path.join(directory, "CoupledModel.cmd")
		assert pending.python_path == os.path.join(pending.model_path, "CoupledModel.py")
		assert pending.last_name_saved == pending.model_path
		assert not _apply_pending_directory(
			pending, os.path.join(directory, "missing"), "CoupledModel"
		)
		assert pending.model_path == os.path.join(directory, "CoupledModel.cmd")

		### the chosen folder is remembered by the assistant
		global _last_output_dir
		previous_dir = _last_output_dir

		try:
			assert _remember_output_dir(directory) == directory
			assert _restore_output_dir() == directory
			### an empty or missing folder keeps the previous one
			assert _remember_output_dir("") == directory
			assert _remember_output_dir(os.path.join(directory, "missing")) == directory
		finally:
			_last_output_dir = previous_dir

	### Code-less behavior submodels ----------------------------------
	structure = {
		"name": "Coupled",
		"submodels": [
			{"label": "A", "generate": "behavior", "behavior": "does A"},
			{
				"label": "B",
				"generate": "behavior",
				"behavior": "does B",
				"code": "class B: pass\n",
			},
		],
	}

	downgrade_behavior_submodels(structure)

	assert structure["submodels"][0]["generate"] == "stub"
	assert structure["submodels"][1]["generate"] == "behavior"

	### the generate mode aliases are honoured
	assert _submodel_generate_mode({"generate": "AI"}) == "behavior"
	assert _submodel_generate_mode({"generate": "EMPTY"}) == "stub"
	assert _submodel_generate_mode({}) == "existing"

	### Atomic model code generation ----------------------------------
	class FakeCodeAdapter:
		"""Stand-in adapter returning a fixed atomic model source."""

		def __init__(self, code):
			self.code = code

		def generate_model_json(self, prompt, on_token=None, stop_event=None):
			return {"specifications": {"model_name": "Ignored"}}

		def generate_model_code(self, model_json, on_token=None, stop_event=None):
			if isinstance(self.code, Exception):
				raise self.code
			return self.code

	def behavior_structure():
		return {
			"name": "Coupled",
			"submodels": [
				{"label": "Gen", "generate": "behavior", "behavior": "emits"},
				{"label": "Existing", "model": "SomeModel"},
			],
		}

	generated = behavior_structure()
	generate_missing_submodel_code(generated, FakeCodeAdapter("class Gen: pass\n"))

	assert generated["submodels"][0]["code"] == "class Gen: pass\n"
	assert generated["submodels"][0]["generate"] == "behavior"
	assert "code" not in generated["submodels"][1]

	### no code (stopped generation) falls back to an empty model
	stopped = behavior_structure()
	generate_missing_submodel_code(stopped, FakeCodeAdapter(""))

	assert stopped["submodels"][0]["generate"] == "stub"
	assert "code" not in stopped["submodels"][0]

	### a failure is reported and the submodel becomes a stub
	failed = behavior_structure()
	errors = []
	generate_missing_submodel_code(
		failed,
		FakeCodeAdapter(RuntimeError("boom")),
		errors=errors,
	)

	assert failed["submodels"][0]["generate"] == "stub"
	assert len(errors) == 1 and errors[0][0] == "Gen"
	assert "boom" in str(errors[0][1])

	### a submodel without behavior is left untouched
	empty_behavior = {
		"name": "Coupled",
		"submodels": [{"label": "NoBehavior", "generate": "behavior"}],
	}
	generate_missing_submodel_code(empty_behavior, FakeCodeAdapter("class X: pass\n"))
	assert empty_behavior["submodels"][0]["generate"] == "behavior"

	### Coupled model block creation -----------------------------------
	assert _identifier("Plant Model!") == "Plant_Model"
	assert _identifier("2 plants") == "_2_plants"
	assert _identifier("") == "CoupledModel"
	assert _identifier("__") == "CoupledModel"

	source = coupled_code("Plant_Model", 'A "plant" model')
	compile(source, "Plant_Model.py", "exec")

	import ast

	declared = [node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)]
	assert [node.name for node in declared] == ["Plant_Model"]
	assert declared[0].bases[0].id == "DomainStructure"

	### a description cannot break the generated docstring
	compile(coupled_code("Model", 'ends with \\ and "quotes"'), "Model.py", "exec")

	from Container import ContainerBlock, Diagram, iPort, oPort

	assert not _canvas_can_create(None)
	assert _canvas_can_create(type("Canvas", (), {"diagram": Diagram()})())
	assert not _canvas_can_create(type("Canvas", (), {"diagram": ContainerBlock()})())

	with tempfile.TemporaryDirectory() as directory:

		class FakeDiagram:
			last_name_saved = os.path.join(directory, "model.dsp")

		class FakeCanvas:
			diagram = FakeDiagram()

		assert _model_directory(FakeCanvas()) == directory

		block = create_pending_block(FakeCanvas())

		assert block.label == "CoupledModel"
		assert block.model_path == os.path.join(directory, "CoupledModel.cmd")
		assert block.python_path == os.path.join(block.model_path, "CoupledModel.py")
		assert block.args == {}
		### nothing is written before the assistant produces the model
		assert not os.path.exists(block.model_path)

		assert _choose_target([], True) == (None, True)
		assert _choose_target([block], False) == (block, False)

		created = {
			"name": "Plant Model",
			"description": "A plant",
			"inputs": 1,
			"outputs": 1,
			"submodels": [
				{"label": "Gen", "generate": "stub", "inputs": 1, "outputs": 1},
				{"label": "Sink", "generate": "stub", "inputs": 1, "outputs": 1},
			],
			"connections": [
				{"source": "input", "source_port": 0, "target": "Gen", "target_port": 0},
				{"source": "Gen", "source_port": 0, "target": "Sink", "target_port": 0},
				{"source": "Sink", "source_port": 0, "target": "output", "target_port": 0},
			],
		}

		result = finalize_pending_block(block, created)

		assert result == (2, 3, 1, 1)
		assert block.label == "Plant_Model"
		assert block.model_path == os.path.join(directory, "Plant_Model.cmd")
		assert block.last_name_saved == block.model_path
		assert is_model_archive(block.model_path)

		### the generated submodels are stored next to the coupled model
		assert os.path.exists(os.path.join(directory, "Plant_Model_Gen.amd"))
		assert os.path.exists(os.path.join(directory, "Plant_Model_Sink.amd"))

		with zipfile.ZipFile(block.model_path) as stream:
			names = stream.namelist()
			code = stream.read("Plant_Model.py").decode("utf-8")

		assert "Plant_Model.py" in names
		assert MODEL_ENTRY in names
		assert "class Plant_Model(DomainStructure)" in code

		### the ports of the new block match the generated structure
		assert len([s for s in block.GetShapeList() if isinstance(s, iPort)]) == 1
		assert len([s for s in block.GetShapeList() if isinstance(s, oPort)]) == 1

		### an existing model is never overwritten
		assert unique_model_path(directory, "Plant Model") == os.path.join(
			directory, "Plant_Model_1.cmd"
		)

	### AI model selection --------------------------------------------
	assert model_setting_key("ChatGPT") == "CHATGPT_MODEL"
	assert model_setting_key("Ollama") == "OLLAMA_MODEL"
	assert model_setting_key("LM Studio") == "LMSTUDIO_MODEL"
	assert model_setting_key("Unknown") is None
	assert provider_models("Unknown") == []

	old_selected = getattr(builtins, "SELECTED_IA", None)
	old_params = getattr(builtins, "PARAMS_IA", None)

	try:
		builtins.SELECTED_IA = "Ollama"
		builtins.PARAMS_IA = {"OLLAMA_MODEL": "mistral"}

		assert current_model_name() == "mistral"
		assert current_model_name("Ollama") == "mistral"

		### the default of the provider is used when nothing is stored
		builtins.PARAMS_IA = {}
		assert current_model_name() == "mistral"
		assert current_model_name("ChatGPT") == "gpt-4.1-nano"
		assert current_model_name("LM Studio") == ""

		### the selection is stored where the atomic assistant stores it
		assert set_current_model("qwen2.5-coder")
		assert builtins.PARAMS_IA["OLLAMA_MODEL"] == "qwen2.5-coder"
		assert current_model_name() == "qwen2.5-coder"
		assert adapter_signature() == ("Ollama", "qwen2.5-coder")

		### storing the same model again is a no-op
		assert not set_current_model("qwen2.5-coder")

		### no provider selected: no model can be chosen
		builtins.SELECTED_IA = ""
		assert model_setting_key() is None
		assert current_model_name() == ""
		assert adapter_signature() == ("", "")
		assert not set_current_model("mistral")
	finally:
		if old_selected is None:
			try:
				del builtins.SELECTED_IA
			except AttributeError:
				pass
		else:
			builtins.SELECTED_IA = old_selected

		if old_params is None:
			try:
				del builtins.PARAMS_IA
			except AttributeError:
				pass
		else:
			builtins.PARAMS_IA = old_params

	### Plug-in hooks ------------------------------------------------
	assert callable(Config)
	assert callable(UnConfig)

	assert PluginManager.plugins["ADD_STATE_TRAJECTORY_MENU"]
	assert any(
		plugin is add_ses_menu for plugin in PluginManager.plugins["ADD_STATE_TRAJECTORY_MENU"]
	)
	assert any(
		plugin is add_ses_menu for plugin in PluginManager.plugins["ADD_WCOMP_STRATEGY_MENU"]
	)

	### a non coupled block is ignored by the menu hook
	add_ses_menu(parent=None, model=None)

	### the diagram (canvas background) menu hook can be installed once
	assert _canvas_block(None) is None
	assert _canvas_blocks(None) == []
	assert _plugin_enabled()

	if _install_canvas_menu_hook():
		from Menu import ShapeCanvasPopupMenu

		assert getattr(ShapeCanvasPopupMenu._add_menu_items, "_ses_generator_hook", False)

		### installing again keeps a single wrapper
		wrapped = ShapeCanvasPopupMenu._add_menu_items
		assert _install_canvas_menu_hook()
		assert ShapeCanvasPopupMenu._add_menu_items is wrapped

		### a disabled plug-in hides the entry
		PluginManager.disabled_plugin.append(PLUGIN_NAME)
		try:
			assert not _plugin_enabled()
		finally:
			PluginManager.disabled_plugin.remove(PLUGIN_NAME)

		assert _plugin_enabled()
	else:
		print("Menu module not importable: diagram menu hook not tested")

	### the coupled-model AI assistant receives the model chooser
	if _install_coupled_model_selector_hook():
		import AIPrompterDialog as ai_module

		ai_dialog = ai_module.AIPrompterDialog
		init_ui_name = f"_{ai_dialog.__name__.lstrip('_')}__init_ui"
		wrapped_ui = getattr(ai_dialog, init_ui_name)

		assert getattr(wrapped_ui, "_ses_generator_hook", False)

		### installing again keeps a single wrapper
		assert _install_coupled_model_selector_hook()
		assert getattr(ai_dialog, init_ui_name) is wrapped_ui
		assert ai_dialog._ses_on_model_changed is _ses_on_model_changed
	else:
		print("AI prompter dialog not importable: model chooser hook not tested")

	print("All SES generator self-tests passed!")


if __name__ == "__main__":
	_self_test()
