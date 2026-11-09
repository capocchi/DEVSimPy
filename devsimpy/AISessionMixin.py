"""AI Session Storage/Load/Remove Mixin for AI Editor Assistant.

This module provides a mixin class to add session management capabilities
to the AIEditorAssistantPanel, allowing users to store, load, and remove
AI assistant sessions in JSON files within the .amd zip file structure.
"""

import os
import json
from pathlib import Path


class AISessionMixin:
	"""Mixin to add session storage capabilities to AI editor components.

	This mixin provides methods to store, load, and remove AI assistant sessions
	in JSON files. Sessions are stored per model within the .amd zip structure.

	Usage:
	    class MyAIPanel(AIEditorAssistantPanel, AISessionMixin):
	        def __init__(self, *args, **kwargs):
	            AIEditorAssistantPanel.__init__(self, *args, **kwargs)
	            AISessionMixin.__init__(self)
	"""

	# Default session storage directory relative to package root
	DEFAULT_SESSION_DIR = "sessions"

	def __init__(self):
		"""Initialize session manager with default configuration."""
		self.session_dir = None
		self._current_session_file = None

	def _get_session_path(self, model_path: str) -> Path | None:
		"""Get the path to store/load session for a given model.

		Args:
		    model_path: Path to the .amd zip file (str or Path)

		Returns:
		    Path object pointing to the session directory, or None if invalid
		"""
		try:
			# Handle both string and Path inputs
			if isinstance(model_path, str):
				model_path = Path(model_path)

			# Extract base name from .amd path (e.g., "AtomicModel_mylabel")
			base_name = model_path.stem

			# Create session directory structure within the model's zip
			session_dir = Path(self.session_dir) / base_name if self.session_dir else None

			return session_dir

		except Exception:
			return None

	def store_session(self, data: dict, model_path: str) -> bool:
		"""Store AI assistant session to JSON file.

		Args:
		    data: Session data dictionary containing messages, context, etc.
		    model_path: Path to the .amd zip file

		Returns:
		    True if successful, False otherwise
		"""
		try:
			path = self._get_session_path(model_path)

			if not path or not path.exists():
				return False

			# Ensure directory exists
			path.parent.mkdir(parents=True, exist_ok=True)

			# Write session data with timestamp for versioning
			session_file = path / f"session_{int(os.path.getctime(path))}.json"

			with open(session_file, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=2, ensure_ascii=False)

			return True

		except Exception as e:
			print(f"[AISessionMixin] Error storing session: {e}")
			return False

	def load_session(self, model_path: str) -> dict | None:
		"""Load AI assistant session from JSON file.

		Args:
		    model_path: Path to the .amd zip file

		Returns:
		    Session data dictionary (most recent session) or None if not found/invalid
		"""
		try:
			path = self._get_session_path(model_path)

			if not path or not path.exists():
				return None

			# Get all JSON files and sort by creation time
			session_files = sorted(
				path.glob("*.json"), key=lambda f: os.path.getctime(f), reverse=True
			)

			if not session_files:
				return None

			# Load the most recent session
			with open(session_files[0], "r", encoding="utf-8") as f:
				return json.load(f)

		except Exception as e:
			print(f"[AISessionMixin] Error loading session: {e}")
			return None

	def remove_session(self, model_path: str) -> bool:
		"""Remove the most recent AI assistant session file.

		Args:
		    model_path: Path to the .amd zip file

		Returns:
		    True if successful (file removed), False otherwise
		"""
		try:
			path = self._get_session_path(model_path)

			if not path or not path.exists():
				return False

			# Remove all session files
			for session_file in path.glob("*.json"):
				session_file.unlink()

			return True

		except Exception as e:
			print(f"[AISessionMixin] Error removing session: {e}")
			return False

	def clear_all_sessions(self, model_path: str) -> bool:
		"""Clear all sessions for a given model.

		Args:
		    model_path: Path to the .amd zip file

		Returns:
		    True if successful, False otherwise
		"""
		try:
			path = self._get_session_path(model_path)

			if not path or not path.exists():
				return False

			# Remove all session files in directory
			for session_file in path.glob("*.json"):
				session_file.unlink()

			return True

		except Exception as e:
			print(f"[AISessionMixin] Error clearing sessions: {e}")
			return False

	def get_session_files(self, model_path: str) -> list[str]:
		"""Get list of available session files for a model.

		Args:
		    model_path: Path to the .amd zip file

		Returns:
		    List of session filenames (without path) or empty list if none exist
		"""
		try:
			path = self._get_session_path(model_path)

			if not path or not path.exists():
				return []

			return [f.name for f in sorted(path.glob("*.json"))]

		except Exception as e:
			print(f"[AISessionMixin] Error getting session files: {e}")
			return []


# Convenience functions for standalone use


def get_session_path(model_path: str, session_dir: str = None) -> Path | None:
	"""Get session path for a model (standalone function).

	Args:
	    model_path: Path to the .amd zip file
	    session_dir: Optional custom session directory

	Returns:
	    Path object or None if invalid
	"""
	base_name = os.path.splitext(os.path.basename(model_path))[0]
	return Path(session_dir) / base_name if session_dir else None


def store_session_standalone(data: dict, model_path: str, session_dir: str = "sessions") -> bool:
	"""Store session using standalone function (no mixin required).

	Args:
	    data: Session data dictionary
	    model_path: Path to the .amd zip file
	    session_dir: Directory for sessions

	Returns:
	    True if successful, False otherwise
	"""
	try:
		path = get_session_path(model_path, session_dir)

		if not path or not path.exists():
			return False

		path.parent.mkdir(parents=True, exist_ok=True)

		session_file = path / f"session_{int(os.path.getctime(path))}.json"

		with open(session_file, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)

		return True

	except Exception as e:
		print(f"[AISessionMixin] Error storing session (standalone): {e}")
		return False


def load_session_standalone(model_path: str, session_dir: str = "sessions") -> dict | None:
	"""Load session using standalone function (no mixin required).

	Args:
	    model_path: Path to the .amd zip file
	    session_dir: Directory for sessions

	Returns:
	    Session data dictionary or None if not found/invalid
	"""
	try:
		path = get_session_path(model_path, session_dir)

		if not path or not path.exists():
			return None

		session_files = sorted(path.glob("*.json"), key=lambda f: os.path.getctime(f), reverse=True)

		if not session_files:
			return None

		with open(session_files[0], "r", encoding="utf-8") as f:
			return json.load(f)

	except Exception as e:
		print(f"[AISessionMixin] Error loading session (standalone): {e}")
		return None


def remove_session_standalone(model_path: str, session_dir: str = "sessions") -> bool:
	"""Remove sessions using standalone function (no mixin required).

	Args:
	    model_path: Path to the .amd zip file
	    session_dir: Directory for sessions

	Returns:
	    True if successful, False otherwise
	"""
	try:
		path = get_session_path(model_path, session_dir)

		if not path or not path.exists():
			return False

		for session_file in path.glob("*.json"):
			session_file.unlink()

		return True

	except Exception as e:
		print(f"[AISessionMixin] Error removing session (standalone): {e}")
		return False
