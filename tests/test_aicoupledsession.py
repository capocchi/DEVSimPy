# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_aicoupledsession.py --- Tests for the coupled-model AI session store.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  16/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import importlib.util
import json
import os
import shutil
import tempfile
import time
import zipfile

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")
SESSION_FILE = os.path.join(PACKAGE_DIR, "AICoupledSession.py")


def load_session_module():
	"""Load AICoupledSession directly (avoids importing the whole package)."""
	spec = importlib.util.spec_from_file_location("AICoupledSession", SESSION_FILE)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


AICoupledSession = load_session_module()


### Helpers -------------------------------------------------------------
def create_archive(extension=".cmd"):
	"""Create a fake model archive and return its path and temp dir."""
	temp_dir = tempfile.mkdtemp()
	archive = os.path.join(temp_dir, "TestModel" + extension)

	with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
		zf.writestr("DEVSimPyModel.dat", b"payload")
		zf.writestr("TestModel.py", "class TestModel: pass\n")

	return archive, temp_dir


def read_archive(archive):
	with zipfile.ZipFile(archive, "r") as zf:
		return zf.namelist(), {name: zf.read(name) for name in zf.namelist()}


def sample_session(prompt="Build a coupled model", structure=None):
	return {
		"model_name": "TestModel",
		"prompt": prompt,
		"provider": "Ollama",
		"ai_model": "mistral",
		"structure": structure
		or {
			"name": "TestModel",
			"inputs": 1,
			"outputs": 1,
			"submodels": [],
			"connections": [],
		},
		"messages": [
			{"role": "user", "content": prompt},
			{"role": "assistant", "content": '{"name": "TestModel"}'},
		],
	}


### Tests ---------------------------------------------------------------
def test_save_and_load_session():
	"""Store then load a coupled session from both .amd and .cmd archives."""
	for extension in (".amd", ".cmd"):
		archive, temp_dir = create_archive(extension)

		try:
			session_id = AICoupledSession.save_session(
				archive, sample_session()
			)

			assert session_id

			names, contents = read_archive(archive)
			assert "ai_coupled/index.json" in names
			assert f"ai_coupled/{session_id}.json" in names
			assert "DEVSimPyModel.dat" in names
			assert "TestModel.py" in names
			assert all("\\" not in name for name in names)

			metadata = json.loads(contents["ai_coupled/index.json"])
			assert len(metadata["sessions"]) == 1
			assert metadata["sessions"][0]["session_id"] == session_id
			assert metadata["sessions"][0]["message_count"] == 2

			loaded = AICoupledSession.load_session(archive)
			assert loaded["session_id"] == session_id
			assert loaded["provider"] == "Ollama"
			assert loaded["ai_model"] == "mistral"
			assert loaded["structure"]["name"] == "TestModel"
			assert loaded["messages"][0]["role"] == "user"
			assert loaded["created_at"]
			assert loaded["updated_at"]

			assert AICoupledSession.load_latest_session(archive) == loaded

		finally:
			shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_save_and_load_session")


def test_update_session_in_place():
	"""Storing twice with the same id updates a single archive entry."""
	archive, temp_dir = create_archive()

	try:
		first_id = AICoupledSession.save_session(archive, sample_session("first"))
		first = AICoupledSession.load_session(archive)

		time.sleep(0.01)

		second = sample_session("second")
		second["messages"].append({"role": "assistant", "content": "done"})

		second_id = AICoupledSession.save_session(
			archive, second, session_id=first_id
		)

		assert second_id == first_id

		sessions = AICoupledSession.list_sessions(archive)
		assert len(sessions) == 1
		assert sessions[0]["session_id"] == first_id
		assert sessions[0]["created_at"] == first["created_at"]
		assert sessions[0]["updated_at"] >= first["updated_at"]
		assert sessions[0]["message_count"] == 3

		names, _contents = read_archive(archive)
		assert names.count("ai_coupled/index.json") == 1

		stored_files = [
			name
			for name in names
			if name.startswith("ai_coupled/")
			and name.endswith(".json")
			and name != "ai_coupled/index.json"
		]
		assert stored_files == [f"ai_coupled/{first_id}.json"]

		loaded = AICoupledSession.load_session(archive)
		assert loaded["prompt"] == "second"
		assert loaded["messages"][-1]["content"] == "done"

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_update_session_in_place")


def test_list_delete_and_clear_sessions():
	"""List sessions (most recent first), delete one and clear all."""
	archive, temp_dir = create_archive()

	try:
		ids = []

		for index in range(3):
			time.sleep(0.01)
			ids.append(
				AICoupledSession.save_session(
					archive, sample_session(f"p{index}")
				)
			)

		sessions = AICoupledSession.list_sessions(archive)
		assert len(sessions) == 3
		assert sessions[0]["session_id"] == ids[-1]
		assert sessions[-1]["session_id"] == ids[0]

		assert AICoupledSession.delete_session(archive, ids[1]) is True
		assert len(AICoupledSession.list_sessions(archive)) == 2

		### deleting an unknown id is a no-op
		assert AICoupledSession.delete_session(archive, "missing") is False

		assert AICoupledSession.clear_sessions(archive) is True
		assert AICoupledSession.list_sessions(archive) == []

		names, _contents = read_archive(archive)
		assert "DEVSimPyModel.dat" in names
		assert "TestModel.py" in names
		assert not [name for name in names if name.startswith("ai_coupled/")]

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_list_delete_and_clear_sessions")


def test_non_archive_rejected():
	"""A plain file is not a model archive: nothing is stored."""
	temp_dir = tempfile.mkdtemp()

	try:
		plain = os.path.join(temp_dir, "PlainModel.py")

		with open(plain, "w", encoding="utf-8") as stream:
			stream.write("class PlainModel: pass\n")

		assert AICoupledSession.is_archive(plain) is False
		assert AICoupledSession.save_session(plain, sample_session()) is None
		assert AICoupledSession.load_session(plain) is None
		assert AICoupledSession.list_sessions(plain) == []
		assert AICoupledSession.delete_session(plain, "x") is False
		assert AICoupledSession.clear_sessions(plain) is False

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_non_archive_rejected")


def test_archive_entries_are_preserved():
	"""Rewriting the archive keeps every other entry and removes temp files."""
	archive, temp_dir = create_archive()

	try:
		with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED) as zf:
			zf.writestr("Generated_Sub.amd", b"submodel")
			zf.writestr("ai_coupled/", b"")
			zf.writestr("ai_coupled/", b"")

		session_id = AICoupledSession.save_session(archive, sample_session())
		assert session_id

		names, contents = read_archive(archive)
		assert "Generated_Sub.amd" in names
		assert contents["Generated_Sub.amd"] == b"submodel"
		assert names.count("ai_coupled/") <= 1
		assert names.count("ai_coupled/index.json") == 1
		assert not [name for name in names if name.endswith(".tmp")]
		assert not os.path.exists(archive + ".tmp")

	finally:
		shutil.rmtree(temp_dir, ignore_errors=True)

	print("OK test_archive_entries_are_preserved")


def test_build_session_normalizes_payload():
	"""build_session derives a title and drops invalid conversation turns."""
	session = AICoupledSession.build_session(
		{},
		model_name="TestModel",
		prompt="  First line\nsecond line  ",
		messages=[
			{"role": "system", "content": "ignored"},
			{"role": "user", "content": "hello"},
			{"role": "assistant", "content": ""},
			{"role": "assistant", "content": "world"},
			"not a dict",
		],
	)

	assert session["model_name"] == "TestModel"
	assert session["title"] == "First line"
	assert session["messages"] == [
		{"role": "user", "content": "hello"},
		{"role": "assistant", "content": "world"},
	]
	assert session["created_at"] == session["updated_at"]
	assert session["structure_only"] is False

	print("OK test_build_session_normalizes_payload")


def test_build_session_keeps_structure_only():
	"""The structure-only flag is stored and preserved across updates."""
	session = AICoupledSession.build_session(
		{}, model_name="TestModel", structure_only=True
	)

	assert session["structure_only"] is True

	updated = AICoupledSession.build_session(session, prompt="next request")

	assert updated["structure_only"] is True

	cleared = AICoupledSession.build_session(session, structure_only=False)

	assert cleared["structure_only"] is False

	print("OK test_build_session_keeps_structure_only")


def test_build_session_keeps_attachment_names():
	"""Attachment names are stored and preserved across updates."""
	session = AICoupledSession.build_session(
		{}, model_name="TestModel", attachments=["spec.txt", "doc.pdf"]
	)

	assert session["attachments"] == ["spec.txt", "doc.pdf"]

	updated = AICoupledSession.build_session(session, prompt="new request")

	assert updated["attachments"] == ["spec.txt", "doc.pdf"]

	cleared = AICoupledSession.build_session(session, attachments=[])

	assert cleared["attachments"] == []

	print("OK test_build_session_keeps_attachment_names")


if __name__ == "__main__":
	print("Running AI Coupled Session tests...\n")

	test_save_and_load_session()
	test_update_session_in_place()
	test_list_delete_and_clear_sessions()
	test_non_archive_rejected()
	test_archive_entries_are_preserved()
	test_build_session_normalizes_payload()
	test_build_session_keeps_structure_only()
	test_build_session_keeps_attachment_names()

	print("\nAll tests passed!")
