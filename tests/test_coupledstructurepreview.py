# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_coupledstructurepreview.py --- Tests for the structure preview.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  11/17/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

"""Pure (non-GUI) tests for ``devsimpy/CoupledStructurePreview.py``.

Run with:
    python tests/test_coupledstructurepreview.py
"""

import os
import sys

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")

if PACKAGE_DIR not in sys.path:
	sys.path.append(PACKAGE_DIR)

import CoupledStructure as cs
import CoupledStructurePreview as preview


### Helpers -------------------------------------------------------------
def structure():
	"""Normalized structure used by the layout tests."""
	return cs.normalize_coupled_structure(
		{
			"name": "Preview",
			"inputs": 1,
			"outputs": 1,
			"submodels": [
				{"label": "Src", "generate": "stub", "inputs": 0, "outputs": 1},
				{"label": "Snk", "generate": "stub", "inputs": 1, "outputs": 1},
			],
			"connections": [
				{
					"source": "__input__",
					"source_port": 0,
					"target": "Snk",
					"target_port": 0,
				},
				{
					"source": "Src",
					"source_port": 0,
					"target": "Snk",
					"target_port": 0,
				},
				{
					"source": "Snk",
					"source_port": 0,
					"target": "__output__",
					"target_port": 0,
				},
			],
		}
	)


def box(layout, label):
	"""Return the box of ``label`` in ``layout``."""
	for candidate in layout["boxes"]:
		if candidate["label"] == label:
			return candidate
	return None


### Tests ---------------------------------------------------------------
def test_layout_boxes():
	layout = preview.compute_preview_layout(structure())

	assert [item["label"] for item in layout["boxes"]] == ["Src", "Snk"]
	assert len(box(layout, "Src")["outputs"]) == 1
	assert len(box(layout, "Snk")["inputs"]) == 1
	assert len(box(layout, "Snk")["outputs"]) == 1
	assert layout["width"] > 0
	assert layout["height"] > 0
	print("OK test_layout_boxes")


def test_layout_external_ports():
	layout = preview.compute_preview_layout(structure())

	assert len(layout["inputs"]) == 1
	assert len(layout["outputs"]) == 1
	assert layout["inputs"][0]["x"] < box(layout, "Src")["x"]
	assert layout["outputs"][0]["x"] > box(layout, "Snk")["x"]
	print("OK test_layout_external_ports")


def test_layout_connections():
	layout = preview.compute_preview_layout(structure())
	connections = layout["connections"]

	assert len(connections) == 3

	### coupled input -> Snk input 0
	assert connections[0]["x1"] == layout["inputs"][0]["x"]
	assert connections[0]["y1"] == layout["inputs"][0]["y"]
	assert connections[0]["x2"] == box(layout, "Snk")["inputs"][0]["x"]

	### Src output 0 -> Snk input 0
	assert connections[1]["x1"] == box(layout, "Src")["outputs"][0]["x"]
	assert connections[1]["x2"] == box(layout, "Snk")["inputs"][0]["x"]

	### Snk output 0 -> coupled output
	assert connections[2]["x1"] == box(layout, "Snk")["outputs"][0]["x"]
	assert connections[2]["x2"] == layout["outputs"][0]["x"]
	print("OK test_layout_connections")


def test_layout_ports_are_on_box_sides():
	layout = preview.compute_preview_layout(structure())

	for item in layout["boxes"]:
		for port in item["inputs"]:
			assert port["x"] == item["x"]
			assert item["y"] < port["y"] < item["y"] + item["height"]

		for port in item["outputs"]:
			assert port["x"] == item["x"] + item["width"]
			assert item["y"] < port["y"] < item["y"] + item["height"]
	print("OK test_layout_ports_are_on_box_sides")


def test_layout_default_grid():
	layout = preview.compute_preview_layout(
		{
			"inputs": 0,
			"outputs": 0,
			"submodels": [
				{"label": "A", "inputs": 1, "outputs": 1},
				{"label": "B", "inputs": 1, "outputs": 1},
				{"label": "C", "inputs": 1, "outputs": 1},
				{"label": "D", "inputs": 1, "outputs": 1},
			],
			"connections": [],
		}
	)

	first, second, third, fourth = layout["boxes"]

	### three submodels per row, then a new row
	assert first["y"] == second["y"] == third["y"]
	assert fourth["y"] > first["y"]
	assert second["x"] > first["x"]
	print("OK test_layout_default_grid")


def test_layout_skips_unresolved_connections():
	layout = preview.compute_preview_layout(
		{
			"inputs": 0,
			"outputs": 0,
			"submodels": [{"label": "A", "inputs": 1, "outputs": 1}],
			"connections": [
				{
					"source": "A",
					"source_port": 5,
					"target": "Missing",
					"target_port": 0,
				}
			],
		}
	)

	assert layout["connections"] == []
	print("OK test_layout_skips_unresolved_connections")


def test_layout_generate_modes():
	layout = preview.compute_preview_layout(
		{
			"inputs": 0,
			"outputs": 0,
			"submodels": [
				{"label": "Lib", "generate": "existing"},
				{"label": "Ai", "generate": "behavior"},
				{"label": "Empty", "generate": "stub"},
			],
			"connections": [],
		}
	)

	assert [item["generate"] for item in layout["boxes"]] == [
		"existing",
		"behavior",
		"stub",
	]
	print("OK test_layout_generate_modes")


if __name__ == "__main__":
	print("Running Coupled Structure Preview tests...\n")

	test_layout_boxes()
	test_layout_external_ports()
	test_layout_connections()
	test_layout_ports_are_on_box_sides()
	test_layout_default_grid()
	test_layout_skips_unresolved_connections()
	test_layout_generate_modes()

	print("\nAll tests passed!")
