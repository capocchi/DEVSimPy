# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_aicoupledadapter.py --- Tests for the coupled-model request building.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  16/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

"""Pure (non-GUI) tests for the coupled-model conversation of the adapter.

Run with:
    python tests/test_aicoupledadapter.py
"""

import os
import sys

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")

if PACKAGE_DIR not in sys.path:
	sys.path.append(PACKAGE_DIR)

### ApplicationController sets sys.path and the builtins used by DEVSimPy.
from ApplicationController import TestApp  # noqa: F401

from AIAdapter import DevsAIAdapter


### Helpers -------------------------------------------------------------
class RecordingAdapter(DevsAIAdapter):
	"""Adapter that records the request instead of calling a provider."""

	def __init__(self):
		super().__init__(None)
		self.captured = None

	def generate_output(
		self,
		prompt="",
		system_prompt="",
		messages_history=None,
		on_token=None,
		stop_event=None,
	):
		self.captured = {
			"prompt": prompt,
			"system_prompt": system_prompt,
			"messages_history": messages_history,
		}
		return '{"name": "Coupled"}'

	def generate_model_json(self, prompt, on_token=None, stop_event=None):
		return {}


PREVIOUS = {
	"name": "Coupled",
	"inputs": 1,
	"outputs": 1,
	"submodels": [
		{
			"label": "Gen",
			"generate": "existing",
			"model": "Generator",
			"inputs": 0,
			"outputs": 1,
			"x": 160,
			"y": 80,
		}
	],
	"connections": [
		{"source": "Gen", "source_port": 0, "target": "__output__", "target_port": 0}
	],
}


### Tests ---------------------------------------------------------------
def test_history_is_sent_with_the_revision_prompt():
	"""A reopened session sends its conversation before the new request."""
	adapter = RecordingAdapter()

	result = adapter.generate_coupled_model_json(
		"add a sink",
		catalog=[],
		model_name="Coupled",
		inputs=1,
		outputs=1,
		previous_structure=PREVIOUS,
		history=[
			{"role": "user", "content": "build a generator"},
			{"role": "assistant", "content": '{"name": "Coupled"}'},
		],
	)

	assert result == '{"name": "Coupled"}'

	captured = adapter.captured
	messages = captured["messages_history"]

	assert messages is not None
	assert captured["prompt"] == ""
	assert messages[0]["role"] == "system"
	assert "coupled model" in messages[0]["content"].lower()
	assert messages[1] == {"role": "user", "content": "build a generator"}
	assert messages[2] == {"role": "assistant", "content": '{"name": "Coupled"}'}
	assert messages[-1]["role"] == "user"
	assert "Update the DEVSimPy coupled model structure" in messages[-1]["content"]
	assert "Current coupled model structure (JSON)" in messages[-1]["content"]
	assert "add a sink" in messages[-1]["content"]
	assert "Gen" in messages[-1]["content"]

	print("OK test_history_is_sent_with_the_revision_prompt")


def test_without_history_a_single_prompt_is_sent():
	"""The first request keeps the single-shot system/user prompt."""
	adapter = RecordingAdapter()

	adapter.generate_coupled_model_json(
		"build a generator",
		catalog=[],
		model_name="Coupled",
		inputs=1,
		outputs=1,
	)

	captured = adapter.captured

	assert captured["messages_history"] is None
	assert "Create a DEVSimPy coupled model." in captured["prompt"]
	assert "build a generator" in captured["prompt"]

	print("OK test_without_history_a_single_prompt_is_sent")


def test_history_is_bounded_and_cleaned():
	"""Invalid turns are dropped and long turns are truncated."""
	adapter = RecordingAdapter()
	long_content = "x" * (adapter.MAX_HISTORY_MESSAGE_CHARS + 100)

	adapter.generate_coupled_model_json(
		"next",
		history=[
			{"role": "system", "content": "ignored"},
			{"role": "user", "content": "   "},
			{"role": "user", "content": long_content},
			{"role": "assistant", "content": "ok"},
		],
	)

	messages = adapter.captured["messages_history"]

	### system + user(long) + assistant + new user
	assert len(messages) == 4
	assert messages[0]["role"] == "system"
	assert messages[1]["role"] == "user"
	assert messages[1]["content"].endswith("[truncated]")
	assert len(messages[1]["content"]) <= adapter.MAX_HISTORY_MESSAGE_CHARS + 20
	assert messages[2] == {"role": "assistant", "content": "ok"}

	print("OK test_history_is_bounded_and_cleaned")


if __name__ == "__main__":
	print("Running AI Coupled Adapter tests...\n")

	test_history_is_sent_with_the_revision_prompt()
	test_without_history_a_single_prompt_is_sent()
	test_history_is_bounded_and_cleaned()

	print("\nAll tests passed!")
