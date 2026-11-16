# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_lmstudioadapter.py --- Tests for the LM Studio AI adapter.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  14/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

"""Pure (non-GUI) tests for ``LMStudioDevsAdapter``.

They run without an LM Studio server: the OpenAI client is replaced by a fake
that records the request payload and returns a canned answer.

Run with:
    python tests/test_lmstudioadapter.py
"""

import json
import os
import sys

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")

if PACKAGE_DIR not in sys.path:
	sys.path.append(PACKAGE_DIR)

### ApplicationController sets sys.path and the builtins used by DEVSimPy.
from ApplicationController import TestApp  # noqa: F401

from AIAdapter import AIRequestError, AtomicModel, LMStudioDevsAdapter


### Helpers -------------------------------------------------------------
def sample_payload():
	"""Return a valid ``AtomicModel`` JSON document."""
	return AtomicModel(
		specifications={
			"input_port": 0,
			"output_port": 1,
			"model_name": "Gen",
			"model_type": "Generator",
			"states": [{"name": "active", "time": "active"}],
			"model_description": "Generator emitting a job every second.",
			"initial_state": {"name": "active", "time": "active"},
			"model_properties": [],
		},
		init_function={"description": "", "parameters": ""},
		ext_transition={"description": "", "parameters": ""},
		int_transition={"description": "", "parameters": ""},
		output_function={"description": "", "parameters": ""},
		time_advance={"description": "", "parameters": ""},
	).model_dump_json()


class FakeMessage:
	def __init__(self, content=None, reasoning_content=None):
		self.content = content
		self.reasoning_content = reasoning_content
		self.model_extra = {}


class FakeChoice:
	def __init__(self, message):
		self.message = message


class FakeResponse:
	def __init__(self, content=None, reasoning_content=None):
		self.choices = [
			FakeChoice(FakeMessage(content, reasoning_content))
		]


class FakeDelta:
	def __init__(self, content=None, reasoning_content=None):
		self.content = content
		self.reasoning_content = reasoning_content
		self.model_extra = {}


class FakeChunk:
	def __init__(self, content=None, reasoning_content=None):
		self.choices = [type("Choice", (), {"delta": FakeDelta(content, reasoning_content)})()]


class FakeCompletions:
	def __init__(self, owner):
		self.owner = owner

	def create(self, **kwargs):
		self.owner.calls.append(kwargs)
		if self.owner.reject_first and len(self.owner.calls) == 1:
			raise RuntimeError("'response_format.type' must be 'json_schema' or 'text'")
		if kwargs.get("stream"):
			return iter(self.owner.chunks)
		return self.owner.response


class FakeClient:
	def __init__(self, response=None, chunks=None, reject_first=False):
		self.response = response
		self.chunks = chunks or []
		self.reject_first = reject_first
		self.calls = []
		self.chat = type("Chat", (), {"completions": FakeCompletions(self)})()


def make_adapter(client):
	adapter = LMStudioDevsAdapter("http://localhost:1234/v1", "qwen3.5-9b")
	adapter.api_client = client
	return adapter


### Tests ---------------------------------------------------------------
def test_request_uses_json_schema():
	payload = sample_payload()
	client = FakeClient(FakeResponse(payload))
	adapter = make_adapter(client)

	result = adapter.generate_model_json("A generator")

	assert result["specifications"]["model_name"] == "Gen"
	response_format = client.calls[0]["response_format"]
	assert response_format["type"] == "json_schema", response_format
	assert response_format["json_schema"]["strict"] is True
	assert response_format["json_schema"]["schema"] == AtomicModel.model_json_schema()
	### LM Studio rejects json_object: make sure it is never sent
	assert "json_object" not in json.dumps(response_format)
	print("OK test_request_uses_json_schema")


def test_fallback_to_text_when_schema_rejected():
	payload = sample_payload()
	client = FakeClient(FakeResponse("```json\n" + payload + "\n```"), reject_first=True)
	adapter = make_adapter(client)

	result = adapter.generate_model_json("A generator")

	assert result["specifications"]["model_name"] == "Gen"
	formats = [call["response_format"]["type"] for call in client.calls]
	assert formats == ["json_schema", "text"], formats
	print("OK test_fallback_to_text_when_schema_rejected")


def test_reasoning_content_is_used_as_fallback():
	payload = sample_payload()
	client = FakeClient(FakeResponse(content=None, reasoning_content=payload))
	adapter = make_adapter(client)

	result = adapter.generate_model_json("A generator")

	assert result["specifications"]["model_name"] == "Gen"
	print("OK test_reasoning_content_is_used_as_fallback")


def test_streamed_reasoning_content_is_used_as_fallback():
	payload = sample_payload()
	chunks = [
		FakeChunk(reasoning_content=payload[: len(payload) // 2]),
		FakeChunk(reasoning_content=payload[len(payload) // 2 :]),
	]
	client = FakeClient(chunks=chunks)
	adapter = make_adapter(client)
	tokens = []

	result = adapter.generate_model_json("A generator", on_token=tokens.append)

	assert result["specifications"]["model_name"] == "Gen"
	assert "".join(tokens) == payload
	print("OK test_streamed_reasoning_content_is_used_as_fallback")


def test_extract_json_text():
	assert LMStudioDevsAdapter._extract_json_text('  {"a": 1}  ') == '{"a": 1}'
	assert LMStudioDevsAdapter._extract_json_text('```\n{"a": 1}\n```') == '{"a": 1}'
	assert LMStudioDevsAdapter._extract_json_text('Thinking...\n{"a": 1}\nDone') == '{"a": 1}'
	assert LMStudioDevsAdapter._extract_json_text("") == ""
	print("OK test_extract_json_text")


def test_validation_error_is_reported():
	client = FakeClient(FakeResponse("not json"))
	adapter = make_adapter(client)

	try:
		adapter.generate_model_json("A generator")
	except AIRequestError as error:
		assert "Validation error" in str(error), error
	else:
		raise AssertionError("AIRequestError was not raised")

	print("OK test_validation_error_is_reported")


def test_file_attachments_supported():
	adapter = make_adapter(FakeClient(FakeResponse(sample_payload())))
	assert adapter.supports_file_attachments() is True
	print("OK test_file_attachments_supported")


### Main ----------------------------------------------------------------
if __name__ == "__main__":
	test_request_uses_json_schema()
	test_fallback_to_text_when_schema_rejected()
	test_reasoning_content_is_used_as_fallback()
	test_streamed_reasoning_content_is_used_as_fallback()
	test_extract_json_text()
	test_validation_error_is_reported()
	test_file_attachments_supported()

	print("\nAll tests passed!")
