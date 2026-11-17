# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_coupledstructuregui.py --- Build a coupled model from a structure.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  12/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

"""GUI test: apply an AI coupled structure to a real ``ContainerBlock``.

Usage:
    python test_coupledstructuregui.py --autoclose
"""

import os
import pickle
import shutil
import sys
import tempfile
import zipfile

### ApplicationController appends devsimpy/ to sys.path and updates builtins
from ApplicationController import TestApp

import Container  # type: ignore
import CoupledStructure as cs

MODEL_TEMPLATE = '''# -*- coding: utf-8 -*-

from DomainInterface import DomainBehavior


class {name}(DomainBehavior):
	"""Minimal atomic model used by the coupled structure test."""

	def __init__(self):
		DomainBehavior.__init__(self)
'''


def write_model(directory, name):
	"""Create a minimal atomic model and return its python path."""
	path = os.path.join(directory, f"{name}.py")
	with open(path, "w", encoding="utf-8") as stream:
		stream.write(MODEL_TEMPLATE.format(name=name))
	return path


def make_container(label, inputs=1, outputs=1):
	"""Create a ContainerBlock with its graphical input/output ports."""
	block = Container.ContainerBlock(label, inputs, outputs)

	for index in range(inputs):
		port = Container.iPort(label=f"IPort {index}")
		port.id = index
		block.AddShape(port)

	for index in range(outputs):
		port = Container.oPort(label=f"OPort {index}")
		port.id = index
		block.AddShape(port)

	return block


def structure_for(catalog):
	return cs.normalize_coupled_structure(
		{
			"name": "CoupledAI",
			"description": "source and sink",
			"inputs": 1,
			"outputs": 1,
			"submodels": [
				{"label": "Src", "model": "AiSource", "inputs": 0, "outputs": 1},
				{"label": "Snk", "model": "AiSink", "inputs": 1, "outputs": 1},
			],
			"connections": [
				{"source": "__input__", "source_port": 0, "target": "Snk", "target_port": 0},
				{"source": "Src", "source_port": 0, "target": "Snk", "target_port": 0},
				{"source": "Snk", "source_port": 0, "target": "__output__", "target_port": 0},
			],
		},
		catalog=catalog,
	)


def generated_structure():
	"""Structure whose submodels must be generated on disk."""
	return cs.normalize_coupled_structure(
		{
			"name": "GeneratedAI",
			"description": "generated source and stub sink",
			"inputs": 0,
			"outputs": 1,
			"submodels": [
				{
					"label": "Gen",
					"generate": "behavior",
					"behavior": "emits a message every second",
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


def run_checks():
	"""Exercise apply_coupled_structure and return the collected results."""
	results = []

	def check(name, condition, extra=None):
		results.append((name, bool(condition), extra))
		return bool(condition)

	temp_dir = tempfile.mkdtemp()

	try:
		source_py = write_model(temp_dir, "AiSource")
		sink_py = write_model(temp_dir, "AiSink")

		catalog = [
			{
				"name": "AiSource",
				"model": "AiSource",
				"kind": "atomic",
				"python_path": source_py,
				"archive": "",
				"inputs": 0,
				"outputs": 1,
			},
			{
				"name": "AiSink",
				"model": "AiSink",
				"kind": "atomic",
				"python_path": sink_py,
				"archive": "",
				"inputs": 1,
				"outputs": 1,
			},
		]

		structure = structure_for(catalog)
		block = make_container("CoupledAI", 1, 1)

		counts = cs.apply_coupled_structure(block, structure)
		check("apply returns counts", counts == (2, 3), counts)

		shapes = list(block.GetShapeList())
		blocks = [shape for shape in shapes if isinstance(shape, Container.Block)]
		connections = [
			shape for shape in shapes if isinstance(shape, Container.ConnectionShape)
		]

		check("two submodels", len(blocks) == 2, len(blocks))
		check("three connections", len(connections) == 3, len(connections))
		check("ports are preserved", len(shapes) - len(blocks) - len(connections) == 2)

		labels = {b.label for b in blocks}
		check("submodel labels", labels == {"Src", "Snk"}, labels)

		input_port = next(s for s in shapes if isinstance(s, Container.iPort))
		output_port = next(s for s in shapes if isinstance(s, Container.oPort))

		external_input = [
			c
			for c in connections
			if c.input and c.input[0] is input_port and c.output and c.output[0].label == "Snk"
		]
		check("external input coupling", len(external_input) == 1, len(external_input))

		internal = [
			c
			for c in connections
			if c.input and c.input[0].label == "Src" and c.output and c.output[0].label == "Snk"
		]
		check("internal coupling", len(internal) == 1, len(internal))

		external_output = [
			c
			for c in connections
			if c.input and c.input[0].label == "Snk" and c.output and c.output[0] is output_port
		]
		check("external output coupling", len(external_output) == 1, len(external_output))

		### applying twice must not duplicate the diagram content
		cs.apply_coupled_structure(block, structure)
		shapes = list(block.GetShapeList())
		blocks = [shape for shape in shapes if isinstance(shape, Container.Block)]
		connections = [
			shape for shape in shapes if isinstance(shape, Container.ConnectionShape)
		]

		check("idempotent submodels", len(blocks) == 2, len(blocks))
		check("idempotent connections", len(connections) == 3, len(connections))
		check("idempotent ports", len(shapes) == 7, len(shapes))

		### a container without enough input port shapes must be rejected
		small = Container.ContainerBlock("Small", 0, 1)
		try:
			cs.apply_coupled_structure(small, structure)
		except cs.CoupledStructureError:
			check("missing input port rejected", True)
		else:
			check("missing input port rejected", False)

		### generated submodels are written next to the coupled model
		generated = generated_structure()
		generated_block = make_container("GeneratedAI", 0, 1)
		generated_block.model_path = os.path.join(temp_dir, "GeneratedAI.cmd")

		counts = cs.apply_coupled_structure(generated_block, generated)
		check("generated apply counts", counts == (2, 1), counts)

		gen_archive = os.path.join(temp_dir, "GeneratedAI_Gen.amd")
		sink_archive = os.path.join(temp_dir, "GeneratedAI_Sink.amd")

		check("generated Gen archive", os.path.exists(gen_archive))
		check("generated Sink archive", os.path.exists(sink_archive))

		with zipfile.ZipFile(gen_archive) as archive:
			names = archive.namelist()
			code = archive.read("GeneratedAI_Gen.py").decode("utf-8")
			dat = archive.read("DEVSimPyModel.dat")

		check(
			"generated archive entries",
			"GeneratedAI_Gen.py" in names and "DEVSimPyModel.dat" in names,
			names,
		)
		check(
			"generated code class",
			"class Gen(DomainBehavior)" in code,
		)

		try:
			pickle.loads(dat)
		except Exception as error:
			check("generated dat is a pickle", False, error)
		else:
			check("generated dat is a pickle", True)

		generated_blocks = [
			shape
			for shape in generated_block.GetShapeList()
			if isinstance(shape, Container.Block)
		]
		check(
			"generated submodel labels",
			{block.label for block in generated_blocks} == {"Gen", "Sink"},
			{block.label for block in generated_blocks},
		)

		### the generated archive must be loadable as a normal library model
		import Components

		loaded = Components.AMDComponent.Load(gen_archive, "Gen")
		check(
			"generated archive loads",
			loaded is not None and loaded.label == "Gen",
			getattr(loaded, "label", None),
		)

		generated_class = Components.GetClass(loaded.python_path)
		try:
			generated_class()
		except Exception as error:
			check("generated model instantiates", False, error)
		else:
			check("generated model instantiates", True)

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	return results


def main():
	import wx

	app = TestApp(0)
	top = wx.Frame(None)
	top.Hide()
	app.SetTopWindow(top)

	results = run_checks()

	failed = [result for result in results if not result[1]]
	for name, ok, extra in results:
		status = "OK" if ok else "FAIL"
		suffix = "" if extra is None else f" ({extra})"
		print(f"{status} {name}{suffix}")

	top.Destroy()

	if failed:
		print(f"\n{len(failed)} check(s) failed!")
		sys.exit(1)

	print("\nAll checks passed!")


if __name__ == "__main__":
	main()
