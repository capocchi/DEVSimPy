# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_ai_sessionmixin.py --- Tests for AI session storage mixin.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.1                                      last modified:  09/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import importlib.util
import json
import os
import shutil
import tempfile
import time
import zipfile
from unittest.mock import Mock

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")
MIXIN_FILE = os.path.join(PACKAGE_DIR, "Mixins", "AI_SessionMixin.py")


def load_mixin_class():
	"""Load AI_SessionMixin directly (avoids importing the whole package)."""
	spec = importlib.util.spec_from_file_location("AI_SessionMixin", MIXIN_FILE)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module.AI_SessionMixin


AI_SessionMixin = load_mixin_class()


### Helpers -------------------------------------------------------------
class FakeHost:
	"""Minimal editor host exposing a 'cb' model."""

	def __init__(self, model):
		self.cb = model


class FakeBlockModel:
	"""Minimal canvas Block: model_path points to the archive."""

	label = "TestModel"

	def __init__(self, archive):
		self.model_path = archive


class FakeDEVSComponent:
	"""Minimal DEVSComponent: python_path points inside the archive."""

	def __init__(self, archive):
		self.python_path = os.path.join(archive, "TestModel.py")


def create_archive(extension):
	"""Create a fake .amd/.cmd archive and return its path and temp dir."""
	temp_dir = tempfile.mkdtemp()
	archive = os.path.join(temp_dir, "TestModel" + extension)

	with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
		zf.writestr("DEVSimPyModel.dat", b"payload")
		zf.writestr("TestModel.py", "class TestModel: pass\n")

	return archive, temp_dir


def create_mixin(archive, model=None):
	mixin = AI_SessionMixin()
	mixin.model_name = "TestModel"
	mixin.editor_host = FakeHost(model or FakeBlockModel(archive))
	return mixin


def read_archive(archive):
	with zipfile.ZipFile(archive, "r") as zf:
		names = zf.namelist()
		contents = {name: zf.read(name) for name in names}
	return names, contents


### Tests ---------------------------------------------------------------
def test_store_and_load_session():
	"""Store then load a session from both .amd and .cmd archives."""
	for extension in (".amd", ".cmd"):
		archive, temp_dir = create_archive(extension)

		try:
			mixin = create_mixin(archive)

			session = {
				"mode": 0,
				"prompt": "Create an atomic model",
				"messages": [{"role": "user", "content": "Hello"}],
			}

			assert mixin.store_session(session) is True

			names, contents = read_archive(archive)
			assert "session/session_index.json" in names
			assert "DEVSimPyModel.dat" in names
			assert "TestModel.py" in names
			assert all("\\" not in name for name in names)

			metadata = json.loads(contents["session/session_index.json"])
			assert len(metadata["sessions"]) == 1
			record = metadata["sessions"][0]
			assert record["model_name"] == "TestModel"
			assert "session/" + record["filename"] in names

			loaded = mixin.load_session()
			assert loaded == session

			### A second session becomes the most recent one
			time.sleep(0.01)
			session2 = {"mode": 1, "prompt": "Second", "messages": []}
			assert mixin.store_session(session2) is True
			assert mixin.load_session()["prompt"] == "Second"

			### The session index metadata is not duplicated
			names, _contents = read_archive(archive)
			assert names.count("session/session_index.json") == 1

		finally:
			shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_store_and_load_session")


def test_devs_component_archive_resolution():
	"""Sessions must also work when the editor host holds a DEVSComponent."""
	archive, temp_dir = create_archive(".amd")

	try:
		mixin = create_mixin(archive, model=FakeDEVSComponent(archive))

		assert mixin.get_model_extension() == ".amd"
		assert mixin.is_zip_model() is True
		assert mixin.store_session({"prompt": "x"}) is True
		assert mixin.load_session()["prompt"] == "x"

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_devs_component_archive_resolution")


def test_list_remove_and_clear_sessions():
	"""List, remove (by id / latest) and clear sessions."""
	for extension in (".amd", ".cmd"):
		archive, temp_dir = create_archive(extension)

		try:
			mixin = create_mixin(archive)

			for index in range(3):
				time.sleep(0.01)
				assert mixin.store_session({"prompt": f"p{index}"}) is True

			sessions = mixin.list_sessions()
			assert len(sessions) == 3
			assert sessions[0]["timestamp"] >= sessions[-1]["timestamp"]

			### Remove a specific session by its id
			assert mixin.remove_session(sessions[0]["session_id"]) is True
			assert len(mixin.list_sessions()) == 2

			### Remove the most recent session (no id)
			assert mixin.remove_session() is True
			assert len(mixin.list_sessions()) == 1

			### Clear everything
			assert mixin.clear_sessions() is True
			assert mixin.list_sessions() == []

			names, _read = read_archive(archive)
			assert "DEVSimPyModel.dat" in names
			assert "TestModel.py" in names
			assert not [name for name in names if name.startswith("session/TestModel_")]

		finally:
			shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_list_remove_and_clear_sessions")


def test_legacy_session():
	"""Legacy 'session/<model>.json' sessions can be loaded and cleared."""
	archive, temp_dir = create_archive(".amd")

	try:
		mixin = create_mixin(archive)
		legacy = {"mode": 0, "prompt": "legacy"}

		with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED) as zf:
			zf.writestr("session/TestModel.json", json.dumps(legacy))

		assert mixin.load_session("TestModel") == legacy

		assert mixin.clear_sessions() is True

		names, _read = read_archive(archive)
		assert "session/TestModel.json" not in names

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_legacy_session")


def test_non_archive_model_rejected():
	"""A plain .py model has no archive: sessions are not stored."""
	mixin = AI_SessionMixin()
	mixin.model_name = "PlainModel"
	mixin.editor_host = FakeHost(FakeBlockModel(tempfile.mkdtemp()))

	assert mixin.is_zip_model() is False
	assert mixin.store_session({"prompt": "x"}) is False
	assert mixin.load_session() is None
	assert mixin.list_sessions() == []
	assert mixin.remove_session() is False
	assert mixin.clear_sessions() is False

	print("OK test_non_archive_model_rejected")


def test_store_without_model_name():
	"""Storing/removing must fail without a model name."""
	mixin = AI_SessionMixin()
	mixin.editor_host = FakeHost(None)

	assert mixin.store_session({"mode": 0, "prompt": "Test"}) is False
	assert mixin.remove_session() is False

	print("OK test_store_without_model_name")


def test_session_file_property():
	"""session_file returns the archive entry or None."""
	mixin = AI_SessionMixin()
	mixin.model_name = "MyModel"

	assert mixin.session_file == "session/session_index.json"

	mixin.model_name = None
	assert mixin.session_file is None

	print("OK test_session_file_property")


def test_get_current_session():
	"""Current session is captured from the panel widgets."""
	mixin = AI_SessionMixin()

	mode_choice = Mock()
	mode_choice.GetSelection.return_value = 1

	prompt_input = Mock()
	prompt_input.GetValue.return_value = "Test prompt"

	include_code_context = Mock()
	include_code_context.GetValue.return_value = True

	mixin.mode_choice = mode_choice
	mixin.prompt_input = prompt_input
	mixin.include_code_context = include_code_context
	mixin._ask_messages = [{"role": "user", "content": "Hello"}]
	mixin._ask_context_signature = None

	result = mixin._get_current_session()

	assert result["mode"] == 1
	assert result["prompt"] == "Test prompt"
	assert result["include_context"] is True
	assert len(result["messages"]) == 1
	assert result["context_signature"] is None

	print("OK test_get_current_session")


if __name__ == "__main__":
	print("Running AI Session Mixin tests...\n")

	test_store_and_load_session()
	test_devs_component_archive_resolution()
	test_list_remove_and_clear_sessions()
	test_legacy_session()
	test_non_archive_model_rejected()
	test_store_without_model_name()
	test_session_file_property()
	test_get_current_session()

	print("\nAll tests passed!")
