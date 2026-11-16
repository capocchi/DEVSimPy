# -*- coding: utf-8 -*-  # noqa: UP009

"""
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AICoupledSession.py ---
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  15/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

Persist the coupled-model AI assistant session inside the model archive.

The session holds everything needed to reopen the assistant later:

* the conversation (user requests and the JSON answers of the model),
* the last validated coupled structure,
* the provider and model that were used,
* the names of the documents attached to the requests.

It is stored in the ``.cmd`` (or ``.amd``) ZIP archive under ``ai_coupled/``,
next to the model code, so moving or copying the model also carries its AI
session. Code-assistant sessions live in ``session/`` (see
:mod:`Mixins.AI_SessionMixin`); the two never mix.
"""

import gettext
import json
import os
import re
import sys
import uuid
import zipfile
from datetime import datetime

_ = gettext.gettext

### Directory of the coupled-assistant sessions inside the archive
SESSION_DIR = "ai_coupled"

### Index listing the stored sessions (kept inside SESSION_DIR)
INDEX_FILE = "index.json"

### Archives that can hold a coupled assistant session
ARCHIVE_EXTENSIONS = (".amd", ".cmd")

### Number of sessions kept per archive
MAX_SESSIONS = 20

### Roles accepted in the stored conversation
_MESSAGE_ROLES = ("user", "assistant")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Helpers
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def is_archive(path):
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


def _zip_entry(*parts):
	"""Build a ZIP entry name (always forward slashes)."""
	return "/".join(str(part).strip("/") for part in parts if str(part).strip("/"))


def _entry(session_id):
	"""Return the ZIP entry name of a session file."""
	return _zip_entry(SESSION_DIR, f"{session_id}.json")


def _index_entry():
	"""Return the ZIP entry name of the session index."""
	return _zip_entry(SESSION_DIR, INDEX_FILE)


def _now():
	"""Return the current local time as an ISO-8601 string."""
	return datetime.now().astimezone().isoformat()


def _safe_id(value):
	"""Return a filename-safe session id."""
	text = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "")).strip("._")
	return text[:80]


def _new_session_id():
	"""Return a new unique session id."""
	return f"{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _clear_zip_cache(archive):
	"""Drop the zipimport cache entry so the archive is re-read."""
	try:
		import ZipManager

		ZipManager.Zip.ClearCache(archive)
	except Exception:  # noqa: S110
		### ZipManager is optional (tests / standalone usage)
		pass


def _rewrite_archive(archive, remove_entries=(), add_entries=None):
	"""Rewrite ``archive`` removing and/or adding ZIP entries.

	Every other entry (model code, diagram, generated submodels, plugins) is
	preserved. The archive is replaced atomically.
	"""
	remove_entries = set(remove_entries or ())
	add_entries = dict(add_entries or {})
	temp_archive = f"{archive}.tmp"

	try:
		seen = set()

		with (
			zipfile.ZipFile(archive, "r") as zin,
			zipfile.ZipFile(temp_archive, "w", zipfile.ZIP_DEFLATED) as zout,
		):
			for item in zin.infolist():
				if item.filename in remove_entries:
					continue

				### an entry being replaced is written from add_entries below
				if item.filename in add_entries:
					continue

				### archives can contain the same name twice
				if item.filename in seen:
					continue

				seen.add(item.filename)
				zout.writestr(item, zin.read(item.filename))

			for entry_name, data in add_entries.items():
				if entry_name in seen:
					continue

				seen.add(entry_name)
				zout.writestr(entry_name, data)

		os.replace(temp_archive, archive)

	except (OSError, zipfile.BadZipFile, ValueError) as error:
		sys.stderr.write(
			f"Cannot update the AI session of '{archive}': {error}\n"
		)

		try:
			if os.path.exists(temp_archive):
				os.remove(temp_archive)
		except OSError:
			pass

		return False

	_clear_zip_cache(archive)

	return True


def _read_index(archive):
	"""Return the session index of ``archive`` (empty when missing)."""
	try:
		with zipfile.ZipFile(archive, "r") as zf:
			names = set(zf.namelist())

			if _index_entry() in names:
				data = json.loads(zf.read(_index_entry()).decode("utf-8"))

				if isinstance(data, dict):
					data.setdefault("sessions", [])
					return data
	except (OSError, zipfile.BadZipFile, ValueError) as error:
		sys.stderr.write(f"Cannot read the AI session index: {error}\n")

	return {"sessions": []}


def _sorted_records(records):
	"""Return session records, most recent first."""
	return sorted(
		[record for record in records if isinstance(record, dict)],
		key=lambda record: record.get("updated_at") or record.get("created_at") or "",
		reverse=True,
	)


def _clean_messages(messages):
	"""Return a JSON-serializable, bounded conversation."""
	cleaned = []

	for message in messages or []:
		if not isinstance(message, dict):
			continue

		role = message.get("role")
		content = message.get("content")

		if role not in _MESSAGE_ROLES or not isinstance(content, str):
			continue

		if not content.strip():
			continue

		cleaned.append({"role": role, "content": content})

	return cleaned


def build_session(
	session,
	session_id=None,
	model_name=None,
	provider=None,
	ai_model=None,
	structure=None,
	messages=None,
	prompt=None,
	title=None,
	attachments=None,
):
	"""Return a normalized session payload ready to be stored.

	``session`` is the previous payload (when reopening an existing session);
	every field can be overridden by the keyword arguments.
	"""
	session = dict(session or {})
	now = _now()

	payload = {
		"session_id": _safe_id(session_id or session.get("session_id")) or None,
		"model_name": model_name or session.get("model_name") or "",
		"provider": provider if provider is not None else session.get("provider", ""),
		"ai_model": ai_model if ai_model is not None else session.get("ai_model", ""),
		"prompt": prompt if prompt is not None else session.get("prompt", ""),
		"structure": structure if structure is not None else session.get("structure"),
		"messages": _clean_messages(
			messages if messages is not None else session.get("messages")
		),
		"attachments": list(
			attachments
			if attachments is not None
			else session.get("attachments") or []
		),
		"created_at": session.get("created_at") or now,
		"updated_at": now,
	}

	payload["title"] = (
		title
		or session.get("title")
		or _derive_title(payload)
	)

	return payload


def _derive_title(session):
	"""Build a short human-readable title from the session content."""
	title = session.get("title")

	if isinstance(title, str) and title.strip():
		return title.strip()[:80]

	prompt = session.get("prompt")

	if isinstance(prompt, str) and prompt.strip():
		return prompt.strip().splitlines()[0][:80]

	for message in session.get("messages") or []:
		if message.get("role") == "user" and message.get("content", "").strip():
			return message["content"].strip().splitlines()[0][:80]

	return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# Public API
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


def save_session(archive, session, session_id=None):
	"""Store ``session`` in the AI session directory of ``archive``.

	Args:
		archive (str): Path of the ``.cmd``/``.amd`` model archive.
		session (dict): Session payload (see :func:`build_session`).
		session_id (str, optional): Session to update. A new id is generated
			when omitted and the session has no id yet.

	Returns:
		str or None: The session id when the session was stored, else ``None``.
	"""
	if not is_archive(archive):
		sys.stderr.write(
			f"Cannot store the AI session: '{archive}' is not a model archive.\n"
		)
		return None

	### an update keeps the creation date, title and attachments of the
	### stored session unless the caller overrides them
	if session_id:
		previous = load_session(archive, session_id)

		if previous:
			base = dict(previous)
			base.update(session or {})
			session = base

	payload = build_session(session, session_id=session_id)

	if not payload["session_id"]:
		payload["session_id"] = _new_session_id()

	session_id = payload["session_id"]

	metadata = _read_index(archive)
	records = [
		record
		for record in metadata.get("sessions", [])
		if record.get("session_id") != session_id
	]

	records.append(
		{
			"session_id": session_id,
			"filename": f"{session_id}.json",
			"model_name": payload.get("model_name", ""),
			"title": payload.get("title", ""),
			"created_at": payload.get("created_at"),
			"updated_at": payload.get("updated_at"),
			"message_count": len(payload.get("messages") or []),
		}
	)

	records = _sorted_records(records)

	### Keep only the most recent sessions and drop the files of the others
	dropped = records[MAX_SESSIONS:]
	records = records[:MAX_SESSIONS]

	metadata["sessions"] = records

	remove_entries = [_entry(record.get("session_id")) for record in dropped]
	remove_entries.append(_index_entry())

	success = _rewrite_archive(
		archive,
		remove_entries=remove_entries,
		add_entries={
			_entry(session_id): json.dumps(payload, indent=2, ensure_ascii=False),
			_index_entry(): json.dumps(metadata, indent=2, ensure_ascii=False),
		},
	)

	if not success:
		return None

	sys.stdout.write(f"AI coupled session stored to: {archive} ({session_id})\n")

	return session_id


def list_sessions(archive):
	"""Return the session records of ``archive``, most recent first."""
	if not is_archive(archive):
		return []

	return _sorted_records(_read_index(archive).get("sessions", []))


def load_session(archive, session_id=None):
	"""Return a stored session payload.

	When ``session_id`` is omitted the most recent session is returned.
	"""
	if not is_archive(archive):
		return None

	records = list_sessions(archive)

	if session_id:
		records = [
			record
			for record in records
			if session_id in (record.get("session_id"), record.get("filename"))
		]

	if not records:
		return None

	target = records[0].get("session_id")

	if not target:
		return None

	try:
		with zipfile.ZipFile(archive, "r") as zf:
			names = set(zf.namelist())
			entry = _entry(target)

			if entry not in names:
				return None

			payload = json.loads(zf.read(entry).decode("utf-8"))

	except (OSError, zipfile.BadZipFile, ValueError) as error:
		sys.stderr.write(f"Cannot load the AI session: {error}\n")
		return None

	if not isinstance(payload, dict):
		return None

	payload.setdefault("session_id", target)

	return payload


def load_latest_session(archive):
	"""Return the most recent session payload of ``archive``, if any."""
	return load_session(archive)


def delete_session(archive, session_id):
	"""Remove one session from ``archive``.

	Returns:
		bool: True when the session was removed.
	"""
	if not is_archive(archive) or not session_id:
		return False

	metadata = _read_index(archive)
	records = list(metadata.get("sessions", []))
	kept = [
		record for record in records if record.get("session_id") != session_id
	]

	if len(kept) == len(records):
		return False

	metadata["sessions"] = kept

	return _rewrite_archive(
		archive,
		remove_entries=[_entry(session_id), _index_entry()],
		add_entries={
			_index_entry(): json.dumps(metadata, indent=2, ensure_ascii=False),
		},
	)


def clear_sessions(archive):
	"""Remove every coupled AI session from ``archive``."""
	if not is_archive(archive):
		return False

	metadata = _read_index(archive)
	remove_entries = [
		_entry(record.get("session_id"))
		for record in metadata.get("sessions", [])
		if record.get("session_id")
	]
	remove_entries.append(_index_entry())

	success = _rewrite_archive(archive, remove_entries=remove_entries)

	if success:
		sys.stdout.write(f"AI coupled sessions cleared from: {archive}\n")

	return success
