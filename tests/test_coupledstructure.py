# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_coupledstructure.py --- Tests for the coupled model structure module.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  12/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

"""Pure (non-GUI) tests for ``devsimpy/CoupledStructure.py``.

Run with:
    python tests/test_coupledstructure.py
"""

import json
import os
import shutil
import sys
import tempfile
import zipfile

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")

if PACKAGE_DIR not in sys.path:
	sys.path.append(PACKAGE_DIR)

import CoupledStructure as cs


### Helpers -------------------------------------------------------------
def catalog():
	"""Small in-memory catalog used by most tests."""
	return [
		{
			"name": "Generator",
			"model": "Generator",
			"kind": "atomic",
			"python_path": os.path.join("models", "Generator.py"),
			"archive": "",
			"inputs": 0,
			"outputs": 1,
		},
		{
			"name": "Queue",
			"model": "Queue",
			"kind": "atomic",
			"python_path": os.path.join("models", "Queue.py"),
			"archive": "",
			"inputs": 1,
			"outputs": 1,
		},
		{
			"name": "Collector",
			"model": "Collector",
			"kind": "atomic",
			"python_path": os.path.join("models", "Collector.py"),
			"archive": "",
			"inputs": 1,
			"outputs": 0,
		},
	]


def valid_structure():
	return {
		"name": "MyCoupled",
		"description": "generator -> queue -> collector",
		"inputs": 1,
		"outputs": 1,
		"submodels": [
			{"label": "Gen", "model": "Generator", "inputs": 0, "outputs": 1},
			{"label": "Q", "model": "Queue", "inputs": 1, "outputs": 1},
			{"label": "Sink", "model": "Collector", "inputs": 1, "outputs": 0},
		],
		"connections": [
			{"source": "Gen", "source_port": 0, "target": "Q", "target_port": 0},
			{"source": "__input__", "source_port": 0, "target": "Q", "target_port": 0},
			{"source": "Q", "source_port": 0, "target": "Sink", "target_port": 0},
			{"source": "Q", "source_port": 0, "target": "__output__", "target_port": 0},
		],
	}


def expect_error(function, *args, **kwargs):
	"""Assert that ``function`` raises ``CoupledStructureError``."""
	try:
		function(*args, **kwargs)
	except cs.CoupledStructureError as error:
		return str(error)

	raise AssertionError("CoupledStructureError was not raised")


### JSON parsing --------------------------------------------------------
def test_parse_plain_object():
	data = cs.parse_json_object('{"name": "M", "submodels": []}')
	assert data == {"name": "M", "submodels": []}
	print("OK test_parse_plain_object")


def test_parse_fenced_object():
	raw = '```json\n{"name": "M"}\n```'
	assert cs.parse_json_object(raw) == {"name": "M"}
	print("OK test_parse_fenced_object")


def test_parse_object_with_prose():
	raw = 'Here is the model:\n{"name": "M", "x": 1}\nEnjoy!'
	assert cs.parse_json_object(raw) == {"name": "M", "x": 1}
	print("OK test_parse_object_with_prose")


def test_parse_invalid_raises():
	expect_error(cs.parse_json_object, "")
	expect_error(cs.parse_json_object, "no json here")
	expect_error(cs.parse_json_object, "[1, 2, 3]")
	print("OK test_parse_invalid_raises")


### Normalization -------------------------------------------------------
def test_normalize_valid_structure():
	structure = cs.normalize_coupled_structure(valid_structure(), catalog=catalog())

	assert structure["name"] == "MyCoupled"
	assert structure["inputs"] == 1
	assert structure["outputs"] == 1
	assert len(structure["submodels"]) == 3
	assert len(structure["connections"]) == 4

	by_label = {s["label"]: s for s in structure["submodels"]}
	assert by_label["Gen"]["python_path"].endswith("Generator.py")
	assert by_label["Gen"]["kind"] == "atomic"
	assert by_label["Q"]["inputs"] == 1

	### the structure must stay JSON serializable
	json.dumps(structure)
	print("OK test_normalize_valid_structure")


def test_normalize_applies_defaults_and_layout():
	data = {
		"submodels": [{"label": "A", "model": "Queue"}],
	}

	structure = cs.normalize_coupled_structure(
		data,
		catalog=catalog(),
		name="Fallback",
		inputs=2,
		outputs=3,
	)

	assert structure["name"] == "Fallback"
	assert structure["inputs"] == 2
	assert structure["outputs"] == 3
	assert structure["connections"] == []

	submodel = structure["submodels"][0]
	assert submodel["x"] == cs.DEFAULT_X
	assert submodel["y"] == cs.DEFAULT_Y
	print("OK test_normalize_applies_defaults_and_layout")


def test_normalize_unknown_model():
	error = expect_error(
		cs.normalize_coupled_structure,
		{"submodels": [{"label": "A", "model": "MissingModel"}]},
		catalog=catalog(),
	)
	assert "Unknown model" in error
	assert "Generator" in error or "Queue" in error
	print("OK test_normalize_unknown_model")


def test_normalize_duplicate_labels():
	expect_error(
		cs.normalize_coupled_structure,
		{
			"submodels": [
				{"label": "Same", "model": "Queue"},
				{"label": "Same", "model": "Generator"},
			]
		},
		catalog=catalog(),
	)
	print("OK test_normalize_duplicate_labels")


def test_normalize_missing_submodels():
	expect_error(cs.normalize_coupled_structure, {"submodels": []}, catalog=catalog())
	expect_error(cs.normalize_coupled_structure, {}, catalog=catalog())
	print("OK test_normalize_missing_submodels")


def test_normalize_port_index_out_of_range():
	expect_error(
		cs.normalize_coupled_structure,
		{
			"inputs": 1,
			"outputs": 1,
			"submodels": [{"label": "Gen", "model": "Generator"}],
			"connections": [
				{"source": "Gen", "source_port": 5, "target": "__output__", "target_port": 0}
			],
		},
		catalog=catalog(),
	)

	expect_error(
		cs.normalize_coupled_structure,
		{
			"inputs": 1,
			"outputs": 1,
			"submodels": [{"label": "Q", "model": "Queue"}],
			"connections": [
				{"source": "__input__", "source_port": 4, "target": "Q", "target_port": 0}
			],
		},
		catalog=catalog(),
	)
	print("OK test_normalize_port_index_out_of_range")


def test_normalize_unknown_connection_endpoint():
	expect_error(
		cs.normalize_coupled_structure,
		{
			"inputs": 1,
			"outputs": 1,
			"submodels": [{"label": "Q", "model": "Queue"}],
			"connections": [
				{"source": "Ghost", "source_port": 0, "target": "Q", "target_port": 0}
			],
		},
		catalog=catalog(),
	)
	print("OK test_normalize_unknown_connection_endpoint")


def test_normalize_reports_every_connection_error():
	"""A structure with several bad couplings must list them all."""
	error = expect_error(
		cs.normalize_coupled_structure,
		{
			"inputs": 1,
			"outputs": 1,
			"submodels": [
				{"label": "Gen", "model": "Generator", "inputs": 0, "outputs": 1},
				{"label": "Form", "model": "Queue", "inputs": 0, "outputs": 1},
				{"label": "Value", "model": "Queue", "inputs": 0, "outputs": 1},
			],
			"connections": [
				{"source": "__input__", "source_port": 0, "target": "Gen", "target_port": 0},
				{"source": "Gen", "source_port": 0, "target": "Form", "target_port": 0},
				{"source": "Gen", "source_port": 0, "target": "Value", "target_port": 0},
			],
		},
		catalog=catalog(),
	)

	assert "Connection #1" in error
	assert "Connection #2" in error
	assert "Connection #3" in error
	assert error.count("targets input port 0") == 3
	print("OK test_normalize_reports_every_connection_error")


def test_normalize_zero_input_target_explains_the_fix():
	error = expect_error(
		cs.normalize_coupled_structure,
		{
			"inputs": 1,
			"outputs": 1,
			"submodels": [{"label": "Gen", "model": "Generator", "inputs": 0}],
			"connections": [
				{"source": "__input__", "source_port": 0, "target": "Gen", "target_port": 0}
			],
		},
		catalog=catalog(),
	)

	assert '"inputs": 1' in error
	assert "remove this connection" in error
	print("OK test_normalize_zero_input_target_explains_the_fix")


def test_normalize_rejects_direct_feedback():
	expect_error(
		cs.normalize_coupled_structure,
		{
			"inputs": 1,
			"outputs": 1,
			"submodels": [{"label": "Q", "model": "Queue"}],
			"connections": [
				{"source": "Q", "source_port": 0, "target": "Q", "target_port": 0}
			],
		},
		catalog=catalog(),
	)
	print("OK test_normalize_rejects_direct_feedback")


### Catalog -------------------------------------------------------------
def test_classify_python_model():
	temp_dir = tempfile.mkdtemp()

	try:
		atomic = os.path.join(temp_dir, "AtomicModel.py")
		with open(atomic, "w", encoding="utf-8") as stream:
			stream.write(
				"from DomainInterface import DomainBehavior\n"
				"class AtomicModel(DomainBehavior):\n"
				"    pass\n"
			)

		coupled = os.path.join(temp_dir, "CoupledModel.py")
		with open(coupled, "w", encoding="utf-8") as stream:
			stream.write(
				"from DomainInterface import DomainStructure\n"
				"class CoupledModel(DomainStructure):\n"
				"    pass\n"
			)

		helper = os.path.join(temp_dir, "Helper.py")
		with open(helper, "w", encoding="utf-8") as stream:
			stream.write("class Helper(object):\n    pass\n")

		assert cs._classify_python_model(atomic) == ("AtomicModel", "atomic")
		assert cs._classify_python_model(coupled) == ("CoupledModel", "coupled")
		assert cs._classify_python_model(helper) is None
	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_classify_python_model")


def test_build_catalog_from_directory():
	temp_dir = tempfile.mkdtemp()

	try:
		with open(os.path.join(temp_dir, "GenModel.py"), "w", encoding="utf-8") as stream:
			stream.write(
				"from DomainInterface import DomainBehavior\n"
				"class GenModel(DomainBehavior):\n"
				"    pass\n"
			)

		### an archive must be resolved to the python entry it embeds
		archive = os.path.join(temp_dir, "ArchivedModel.amd")
		with zipfile.ZipFile(archive, "w") as zf:
			zf.writestr(
				"ArchivedModel.py",
				"from DomainInterface import DomainBehavior\n"
				"class ArchivedModel(DomainBehavior):\n"
				"    pass\n",
			)
			zf.writestr("DEVSimPyModel.dat", "placeholder")

		catalog_entries = cs.build_model_catalog([temp_dir])
		names = {entry["name"] for entry in catalog_entries}

		assert "GenModel" in names
		assert "ArchivedModel" in names

		archived = next(e for e in catalog_entries if e["name"] == "ArchivedModel")
		assert archived["archive"] == archive
		assert archived["python_path"].endswith("ArchivedModel.py")
		assert archived["kind"] == "atomic"

		### no duplicate name
		assert len([e for e in catalog_entries if e["name"] == "ArchivedModel"]) == 1
	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_build_catalog_from_directory")


def test_catalog_for_prompt():
	entries = cs.catalog_for_prompt(catalog())

	assert len(entries) == 3
	assert set(entries[0]) == {"name", "kind", "inputs", "outputs"}
	assert entries[0]["name"] == "Generator"
	print("OK test_catalog_for_prompt")


### Prompts -------------------------------------------------------------
def test_coupled_prompts():
	system_prompt = cs.coupled_system_prompt(catalog())
	user_prompt = cs.coupled_user_prompt(
		"generator feeding a queue",
		model_name="MyCoupled",
		inputs=2,
		outputs=3,
	)

	assert "__input__" in system_prompt
	assert "__output__" in system_prompt
	assert "Generator" in system_prompt
	assert 'A submodel with "inputs": 0 must never be the target' in system_prompt
	assert "Common mistake to avoid" in system_prompt
	assert '"generate": "behavior"' in system_prompt
	assert "Never bind a described behavior" in system_prompt

	assert "MyCoupled" in user_prompt
	assert "2 input port(s)" in user_prompt
	assert "3 output port(s)" in user_prompt
	assert "generator feeding a queue" in user_prompt
	print("OK test_coupled_prompts")


def test_coupled_structure_only_prompts():
	"""Structure-only mode forbids behavior submodels."""
	system_prompt = cs.coupled_system_prompt(catalog(), generate_atomic_code=False)
	user_prompt = cs.coupled_user_prompt(
		"generator feeding a queue",
		model_name="MyCoupled",
		generate_atomic_code=False,
	)

	assert "Atomic model code generation is disabled for this request" in system_prompt
	assert '"generate": "stub"' in system_prompt
	assert "never use" in system_prompt
	### no submodel may ask for generated code
	assert '"generate": "behavior",\n      "behavior"' not in system_prompt

	assert "Return the structure only" in user_prompt
	assert '"generate": "stub"' in user_prompt

	### the default mode still allows behavior submodels
	assert '"generate": "behavior",\n      "behavior"' in cs.coupled_system_prompt(catalog())

	print("OK test_coupled_structure_only_prompts")


def test_coupled_revision_prompt():
	"""Reopening a session asks for the complete updated structure."""
	previous = {
		"name": "MyCoupled",
		"inputs": 1,
		"outputs": 1,
		"submodels": [
			{
				"label": "Generator1",
				"generate": "existing",
				"model": "Generator",
				"inputs": 0,
				"outputs": 1,
				"x": 160,
				"y": 80,
			}
		],
		"connections": [
			{
				"source": "Generator1",
				"source_port": 0,
				"target": "__output__",
				"target_port": 0,
			}
		],
	}

	user_prompt = cs.coupled_user_prompt(
		"add a formatter",
		model_name="MyCoupled",
		inputs=1,
		outputs=1,
		previous_structure=previous,
	)

	assert "Update the DEVSimPy coupled model structure" in user_prompt
	assert "Current coupled model structure (JSON)" in user_prompt
	assert "Generator1" in user_prompt
	assert "add a formatter" in user_prompt
	assert "return the complete updated JSON object" in user_prompt
	assert "Keep every submodel and connection" in user_prompt

	### an empty previous structure is not a revision
	creation_prompt = cs.coupled_user_prompt(
		"build a model",
		previous_structure={},
	)

	assert "Create a DEVSimPy coupled model." in creation_prompt
	assert "Current coupled model structure" not in creation_prompt
	print("OK test_coupled_revision_prompt")


### Generated submodels --------------------------------------------------
def test_normalize_generated_submodels():
	structure = cs.normalize_coupled_structure(
		{
			"name": "CoupledAI",
			"inputs": 0,
			"outputs": 1,
			"submodels": [
				{
					"label": "Gen",
					"generate": "behavior",
					"behavior": "emits a tuple every second",
					"inputs": 0,
					"outputs": 1,
				},
				{"label": "Sink", "generate": "stub", "inputs": 1, "outputs": 0},
			],
			"connections": [
				{"source": "Gen", "source_port": 0, "target": "Sink", "target_port": 0},
			],
		},
		catalog=[],
	)

	generator, sink = structure["submodels"]

	assert generator["generate"] == "behavior"
	assert generator["behavior"] == "emits a tuple every second"
	assert generator["code"] == ""
	assert generator["python_path"] is None
	assert generator["archive"] == ""

	assert sink["generate"] == "stub"
	assert sink["model"] == "Sink"
	assert sink["python_path"] is None
	print("OK test_normalize_generated_submodels")


def test_normalize_behavior_requires_description():
	message = expect_error(
		cs.normalize_coupled_structure,
		{
			"submodels": [
				{"label": "X", "generate": "behavior", "inputs": 1, "outputs": 1}
			]
		},
		catalog=[],
	)

	assert "behavior" in message
	assert "no" in message
	print("OK test_normalize_behavior_requires_description")


def test_normalize_rejects_unknown_generate_mode():
	message = expect_error(
		cs.normalize_coupled_structure,
		{"submodels": [{"label": "X", "generate": "magic"}]},
		catalog=[],
	)

	assert "Unknown generate mode" in message
	print("OK test_normalize_rejects_unknown_generate_mode")


def test_normalize_accepts_generated_code():
	code = cs.stub_atomic_code("CoupledAI_X", 1, 1)
	structure = cs.normalize_coupled_structure(
		{
			"submodels": [
				{
					"label": "X",
					"generate": "behavior",
					"code": code,
					"inputs": 1,
					"outputs": 1,
				}
			]
		},
		catalog=[],
	)

	assert structure["submodels"][0]["code"] == code.strip()
	print("OK test_normalize_accepts_generated_code")


def test_normalize_rejects_invalid_generated_code():
	message = expect_error(
		cs.normalize_coupled_structure,
		{
			"submodels": [
				{
					"label": "X",
					"generate": "behavior",
					"code": "def broken(:",
				}
			]
		},
		catalog=[],
	)

	assert "invalid generated code" in message
	print("OK test_normalize_rejects_invalid_generated_code")


def test_normalize_rejects_code_without_class():
	message = expect_error(
		cs.normalize_coupled_structure,
		{"submodels": [{"label": "X", "generate": "behavior", "code": "x = 1"}]},
		catalog=[],
	)

	assert "does not declare a class" in message
	print("OK test_normalize_rejects_code_without_class")


def test_stub_atomic_code_compiles():
	code = cs.stub_atomic_code("CoupledAI_Gen", 0, 1)
	compile(code, "CoupledAI_Gen.py", "exec")

	assert "class CoupledAI_Gen(DomainBehavior)" in code
	assert "initPhase" in code
	print("OK test_stub_atomic_code_compiles")


def test_generated_submodel_name():
	assert cs.generated_submodel_name("My Coupled", "Form 1") == "My_Coupled_Form_1"
	assert cs.generated_submodel_name("9Coupled", "Value") == "_9Coupled_Value"
	print("OK test_generated_submodel_name")


def test_generated_submodel_class_name():
	"""The generated class is named after its code block."""
	assert cs.generated_submodel_class_name("Form") == "Form"
	assert cs.generated_submodel_class_name("Form 1") == "Form_1"
	assert cs.generated_submodel_class_name("") == "GeneratedModel"
	print("OK test_generated_submodel_class_name")


def test_atomic_submodel_prompt():
	prompt = cs.atomic_submodel_prompt(
		{
			"label": "Form",
			"behavior": "converts colors into shapes",
			"inputs": 1,
			"outputs": 1,
		},
		"CoupledAI",
	)

	assert "'Form'" in prompt
	assert "named exactly 'Form'" in prompt
	assert "code block" in prompt
	assert "Do not add a prefix or a suffix" in prompt
	assert "CoupledAI_Form" not in prompt
	assert "converts colors into shapes" in prompt
	assert "1 input port(s)" in prompt
	assert "1 output port(s)" in prompt
	print("OK test_atomic_submodel_prompt")


class DummyAtomicAdapter:
	"""Minimal adapter recording the atomic generation pipeline calls."""

	def __init__(self):
		self.calls = []
		self.prompts = []
		self.model_jsons = []

	def generate_model_json(self, prompt, on_token=None, stop_event=None):
		self.calls.append("json")
		self.prompts.append(prompt)
		return {"specifications": {"model_name": "AiForm"}}

	def generate_model_code(self, model_json=None, on_token=None, stop_event=None):
		self.calls.append("code")
		self.model_jsons.append(model_json)
		return (
			"from DomainInterface import DomainBehavior\n\n\n"
			"class AiForm(DomainBehavior):\n"
			"\tpass\n"
		)


def test_generate_submodel_code_uses_atomic_pipeline():
	adapter = DummyAtomicAdapter()
	submodel = {
		"label": "Form",
		"behavior": "converts colors into shapes",
		"inputs": 1,
		"outputs": 1,
	}

	code = cs.generate_submodel_code(submodel, "CoupledAI", adapter)

	assert adapter.calls == ["json", "code"]
	assert "'Form'" in adapter.prompts[0]
	assert "class AiForm" in code
	### the model name given to the code generator is the code block name
	assert adapter.model_jsons[0]["specifications"]["model_name"] == "Form"
	print("OK test_generate_submodel_code_uses_atomic_pipeline")


def test_prepare_generated_submodel_writes_archive():
	temp_dir = tempfile.mkdtemp()

	try:
		submodel = {
			"label": "Form",
			"generate": "behavior",
			"behavior": "converts colors into shapes",
			"inputs": 1,
			"outputs": 1,
			"code": "",
		}

		archive, entry, code = cs._prepare_generated_submodel(
			submodel, temp_dir, "CoupledAI"
		)

		assert archive == os.path.join(temp_dir, "CoupledAI_Form.amd")
		assert entry == "CoupledAI_Form.py"
		assert submodel["python_path"] == os.path.join(archive, entry)
		assert submodel["archive"] == archive
		### the class is named after the code block, not after the archive
		assert submodel["model"] == "Form"

		with zipfile.ZipFile(archive) as zf:
			assert entry in zf.namelist()
			assert "DEVSimPyModel.dat" in zf.namelist()
			assert b"class Form(DomainBehavior)" in zf.read(entry)

		compile(code, entry, "exec")
	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_prepare_generated_submodel_writes_archive")


def test_prepare_generated_submodel_renames_ai_class():
	temp_dir = tempfile.mkdtemp()

	try:
		code = (
			"from DomainInterface import DomainBehavior\n\n\n"
			"class AiForm(DomainBehavior):\n"
			"\tpass\n"
		)

		submodel = {
			"label": "Form",
			"generate": "behavior",
			"inputs": 1,
			"outputs": 1,
			"code": code,
		}

		_, entry, renamed = cs._prepare_generated_submodel(
			submodel, temp_dir, "CoupledAI"
		)

		assert "class Form(DomainBehavior)" in renamed
		assert "class AiForm" not in renamed
		compile(renamed, entry, "exec")
	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_prepare_generated_submodel_renames_ai_class")


### Diagram application guards -----------------------------------------
def test_apply_rejects_non_dict():
	expect_error(cs.apply_coupled_structure, object(), None)
	expect_error(cs.apply_coupled_structure, object(), "not a dict")
	print("OK test_apply_rejects_non_dict")


if __name__ == "__main__":
	print("Running Coupled Structure tests...\n")

	test_parse_plain_object()
	test_parse_fenced_object()
	test_parse_object_with_prose()
	test_parse_invalid_raises()
	test_normalize_valid_structure()
	test_normalize_applies_defaults_and_layout()
	test_normalize_unknown_model()
	test_normalize_duplicate_labels()
	test_normalize_missing_submodels()
	test_normalize_port_index_out_of_range()
	test_normalize_unknown_connection_endpoint()
	test_normalize_reports_every_connection_error()
	test_normalize_zero_input_target_explains_the_fix()
	test_normalize_rejects_direct_feedback()
	test_classify_python_model()
	test_build_catalog_from_directory()
	test_catalog_for_prompt()
	test_coupled_prompts()
	test_coupled_structure_only_prompts()
	test_coupled_revision_prompt()
	test_normalize_generated_submodels()
	test_normalize_behavior_requires_description()
	test_normalize_rejects_unknown_generate_mode()
	test_normalize_accepts_generated_code()
	test_normalize_rejects_invalid_generated_code()
	test_normalize_rejects_code_without_class()
	test_stub_atomic_code_compiles()
	test_generated_submodel_name()
	test_generated_submodel_class_name()
	test_atomic_submodel_prompt()
	test_generate_submodel_code_uses_atomic_pipeline()
	test_prepare_generated_submodel_writes_archive()
	test_prepare_generated_submodel_renames_ai_class()
	test_apply_rejects_non_dict()

	print("\nAll tests passed!")
