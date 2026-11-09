# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AI_SessionMixin.py --- Mixin for storing AI assistant session in .amd files.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.2                                      last modified:  09/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
# This mixin adds session storage capabilities to AI assistant panels.
# Sessions are stored as JSON files inside the .amd or .cmd zip archive.
# The structure follows the existing Savable.py pattern for consistency.
# Each session gets a unique filename with timestamp and UUID.
#
# All zip entry names use forward slashes ('/') because this is what the
# ZIP specification requires, even on Windows.
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import json
import os
import re
import sys
import uuid
import zipfile
from datetime import datetime


class AI_SessionMixin:
    """Mixin class to add AI session storage capabilities to AI assistant panels.

    This mixin provides methods to store, load, and remove AI assistant sessions.
    Sessions are stored as JSON files inside the .amd or .cmd zip archive under a
    'session' subdirectory. Each session gets a unique filename with timestamp
    and UUID to allow multiple sessions per model.

    Attributes:
        model_name (str): Name of the model associated with this session.

    Example usage:
        class MyAIPanel(AIEditorAssistantPanel, AI_SessionMixin):
            def __init__(self, parent, editor_host=None):
                # Call parent init first
                super().__init__(parent, editor_host)

                # Initialize mixin attributes
                self.model_name = None

    Methods:
        store_session(): Store current session to the model archive.
        load_session(model_name): Load the most recent session for a model.
        list_sessions(model_name): List all sessions for a model.
        remove_session(session_id): Remove a specific session.
        clear_sessions(model_name): Remove all sessions for a model.
        on_panel_load(): Auto-load the last session when the panel is shown.
        on_panel_close(): Auto-save the session when the panel is closed.
    """

    ### Session storage directory within the model archive
    SESSION_DIR = "session"

    ### Metadata file name (kept inside SESSION_DIR)
    METADATA_FILE = "session_index.json"

    ### Legacy single-session filename template (pre-1.2 archives)
    DEFAULT_SESSION_FILE = "{model_name}.json"

    ### Model archives that can contain AI sessions
    ARCHIVE_EXTENSIONS = (".amd", ".cmd")

    ### Maximum number of sessions kept per model in an archive
    MAX_SESSIONS_PER_MODEL = 20

    def __init__(self):
        """Initialize AI session mixin."""
        self.model_name = None

        # Flag to control automatic session storage (default: enabled)
        self._enable_session_storage = True

        # Flag set once a session has been restored into the panel
        self._session_loaded = False

        # Archive matching the currently loaded conversation
        self._session_archive = None

    # ==================================================================
    # Model / archive resolution
    # ==================================================================
    @property
    def session_file(self):
        """Get the path to the metadata file within the model archive.

        Returns:
            str: Path like 'session/session_index.json' or None if model_name
                is not set.
        """
        if self.model_name:
            return self._zip_entry(self.SESSION_DIR, self.METADATA_FILE)
        return None

    @staticmethod
    def _zip_entry(*parts):
        """Build a ZIP entry name (always forward slashes)."""
        return "/".join(str(part).strip("/") for part in parts if str(part).strip("/"))

    @staticmethod
    def _safe_name(name):
        """Return a filename-safe version of ``name``."""
        return re.sub(r'[\\/:*?"<>|]+', "_", str(name)).strip() or "model"

    @staticmethod
    def _as_str(value):
        """Return ``value`` only when it is a non-empty string."""
        return value if isinstance(value, str) and value else None

    def _get_model(self):
        """Return the model currently edited by the editor host, if any."""
        editor_host = getattr(self, "editor_host", None)
        return getattr(editor_host, "cb", None)

    def _get_candidate_paths(self):
        """Yield all paths that may point to the model archive."""
        model = self._get_model()

        if model is None:
            return

        ### Canvas Block: model_path is the .amd/.cmd archive
        model_path = self._as_str(getattr(model, "model_path", None))
        if model_path:
            yield model_path

        ### DEVSComponent: python_path is <archive>.amd/<module>.py
        python_path = self._as_str(getattr(model, "python_path", None))
        if python_path:
            yield os.path.dirname(python_path)
            yield python_path

        ### Fall back to the Block attached to a DEVSComponent
        get_block = getattr(model, "getBlock", None)
        if callable(get_block):
            try:
                block = get_block()
            except Exception:
                block = None

            block_model_path = self._as_str(getattr(block, "model_path", None))
            if block_model_path:
                yield block_model_path

    def _get_archive_path(self):
        """Return the .amd/.cmd archive path containing AI sessions.

        Returns:
            str or None: Absolute path of the model archive, or None when the
                edited model is not backed by an .amd/.cmd archive.
        """
        try:
            for candidate in self._get_candidate_paths() or []:
                path = os.path.normpath(candidate)

                if not path.lower().endswith(self.ARCHIVE_EXTENSIONS):
                    continue

                if os.path.isfile(path) and zipfile.is_zipfile(path):
                    return path
        except Exception as error:
            sys.stderr.write(f"Error resolving model archive: {error}\n")

        return None

    def get_model_extension(self):
        """Get the file extension of the current model archive.

        Returns:
            str or None: File extension (e.g. '.amd', '.cmd') or None if not
                available.
        """
        archive = self._get_archive_path()

        if archive:
            return os.path.splitext(archive)[1].lower()

        ### Fallback for models that are not zip archives (e.g. '.py')
        model = self._get_model()

        if model is None:
            return None

        python_path = self._as_str(getattr(model, "python_path", None))

        if python_path:
            return os.path.splitext(python_path)[1].lower()

        return None

    def is_amd_model(self):
        """Return True when the current model is stored in an .amd archive."""
        return self.get_model_extension() == ".amd"

    def is_cmd_model(self):
        """Return True when the current model is stored in a .cmd archive."""
        return self.get_model_extension() == ".cmd"

    def is_zip_model(self):
        """Return True when the current model is an .amd or .cmd archive."""
        return self.get_model_extension() in self.ARCHIVE_EXTENSIONS

    # ==================================================================
    # Low level archive helpers
    # ==================================================================
    def _generate_session_id(self):
        """Generate a unique session ID with timestamp and UUID."""
        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{self._safe_name(self.model_name)}_{timestamp}_{unique_id}"

    def _metadata_entries(self):
        """Return the possible metadata entry names (current + legacy)."""
        return (
            self._zip_entry(self.SESSION_DIR, self.METADATA_FILE),
            os.path.join(self.SESSION_DIR, self.METADATA_FILE),
        )

    def _get_session_metadata(self, archive):
        """Read the session index metadata from the model archive."""
        try:
            with zipfile.ZipFile(archive, "r") as zf:
                names = set(zf.namelist())

                for meta_path in self._metadata_entries():
                    if meta_path in names:
                        data = zf.read(meta_path).decode("utf-8")
                        metadata = json.loads(data)

                        if isinstance(metadata, dict):
                            metadata.setdefault("sessions", [])
                            return metadata
        except (OSError, zipfile.BadZipFile, ValueError) as error:
            sys.stderr.write(f"Error reading session metadata: {error}\n")

        return {"sessions": []}

    def _rewrite_archive(self, archive, remove_entries=(), add_entries=None):
        """Rewrite ``archive`` removing and/or adding entries.

        Args:
            archive (str): Path of the .amd/.cmd archive.
            remove_entries (iterable): ZIP entry names to delete.
            add_entries (dict): Mapping ``{entry_name: data}`` to add/replace.

        Returns:
            bool: True when the archive was rewritten successfully.
        """
        remove_entries = set(remove_entries or ())
        add_entries = dict(add_entries or {})

        temp_archive = f"{archive}.tmp"

        try:
            with (
                zipfile.ZipFile(archive, "r") as zin,
                zipfile.ZipFile(temp_archive, "w", zipfile.ZIP_DEFLATED) as zout,
            ):
                for item in zin.infolist():
                    if item.filename in remove_entries:
                        continue

                    ### Do not duplicate an entry that is being replaced
                    if item.filename in add_entries:
                        continue

                    zout.writestr(item, zin.read(item.filename))

                for entry_name, data in add_entries.items():
                    zout.writestr(entry_name, data)

            os.replace(temp_archive, archive)

        except (OSError, zipfile.BadZipFile, ValueError) as error:
            sys.stderr.write(f"Error updating model archive '{archive}': {error}\n")

            try:
                if os.path.exists(temp_archive):
                    os.remove(temp_archive)
            except OSError:
                pass

            return False

        ### Invalidate the zipimport cache so the archive is re-read
        self._clear_zip_cache(archive)

        return True

    @staticmethod
    def _clear_zip_cache(archive):
        """Clear the zipimport cache entry for ``archive``."""
        try:
            import ZipManager

            ZipManager.Zip.ClearCache(archive)
        except Exception:  # noqa: S110
            # ZipManager is optional here (standalone/tests usage)
            pass

    def _legacy_entry(self, model_name):
        """Return the legacy (single session) ZIP entry name for ``model_name``."""
        return self._zip_entry(
            self.SESSION_DIR,
            self.DEFAULT_SESSION_FILE.format(model_name=self._safe_name(model_name)),
        )

    def _session_records(self, metadata, model_name=None):
        """Return session records, most recent first."""
        records = [
            record
            for record in metadata.get("sessions", [])
            if isinstance(record, dict)
            and (model_name is None or record.get("model_name") == model_name)
        ]

        return sorted(
            records,
            key=lambda record: record.get("timestamp", ""),
            reverse=True,
        )

    # ==================================================================
    # Public API
    # ==================================================================
    def store_session(self, session_data=None, archive=None):
        """Store an AI assistant session in the .amd/.cmd model archive.

        Args:
            session_data (dict, optional): Session data to store. If None, uses
                self._get_current_session() to get the current session state.
            archive (str, optional): Archive to write to. Defaults to the
                archive matching the current conversation.

        Returns:
            bool: True if the session was stored successfully, False otherwise.

        Example:
            panel.store_session({
                "prompt": "Create a new atomic model",
                "messages": [...],
                "mode": 1
            })
        """
        ### Get or create session data
        if session_data is None:
            session_data = self._get_current_session()

        if session_data is None:
            return False

        if not self.model_name:
            sys.stderr.write("Cannot store session: model_name not set.\n")
            return False

        ### Prefer the archive matching the conversation being saved
        archive = archive or self._session_archive or self._get_archive_path()

        if not archive:
            sys.stderr.write(
                "Cannot store session: no .amd or .cmd model archive available.\n"
            )
            return False

        if not os.path.isfile(archive) or not zipfile.is_zipfile(archive):
            sys.stderr.write(f"Cannot store session: invalid archive {archive}\n")
            return False

        try:
            metadata = self._get_session_metadata(archive)
            records = list(metadata.get("sessions", []))

            session_id = self._generate_session_id()
            session_filename = f"{session_id}.json"
            session_entry = self._zip_entry(self.SESSION_DIR, session_filename)
            timestamp = datetime.now().astimezone().isoformat()

            session_data_with_meta = {
                "session_id": session_id,
                "model_name": self.model_name,
                "timestamp": timestamp,
                "data": session_data,
            }

            ### Keep only the last MAX_SESSIONS_PER_MODEL sessions for this model
            model_records = self._session_records(metadata, self.model_name)
            records_to_remove = model_records[self.MAX_SESSIONS_PER_MODEL - 1 :]

            for record in records_to_remove:
                if record in records:
                    records.remove(record)

            ### Build the new metadata index
            records.append(
                {
                    "session_id": session_id,
                    "filename": session_filename,
                    "model_name": self.model_name,
                    "timestamp": timestamp,
                }
            )
            metadata["sessions"] = records

            remove_entries = [
                self._zip_entry(self.SESSION_DIR, record.get("filename", ""))
                for record in records_to_remove
                if record.get("filename")
            ]
            remove_entries.extend(self._metadata_entries())

            success = self._rewrite_archive(
                archive,
                remove_entries=remove_entries,
                add_entries={
                    session_entry: json.dumps(
                        session_data_with_meta, indent=2, ensure_ascii=False
                    ),
                    self._zip_entry(
                        self.SESSION_DIR, self.METADATA_FILE
                    ): json.dumps(metadata, indent=2, ensure_ascii=False),
                },
            )

            if success:
                sys.stdout.write(
                    f"Session stored to: {archive} (session: {session_id})\n"
                )

            return success

        except Exception as error:
            tb = __import__("traceback").format_exc()
            sys.stderr.write(f"Error storing session: {error}\n{tb}")
            return False

    def load_session(self, model_name=None):
        """Load the most recent AI assistant session from the model archive.

        Args:
            model_name (str, optional): Model name to load the session for.
                If None, uses self.model_name.

        Returns:
            dict or None: Session data if loaded successfully, None otherwise.

        Example:
            session = panel.load_session("MyModel")
            if session:
                print(f"Loaded prompt: {session.get('prompt')}")
        """
        target_model_name = model_name if model_name else self.model_name

        archive = self._get_archive_path()

        if not archive:
            sys.stderr.write(
                "Cannot load session: no .amd or .cmd model archive available.\n"
            )
            return None

        self._session_archive = archive

        try:
            metadata = self._get_session_metadata(archive)
            model_sessions = self._session_records(metadata, target_model_name)

            with zipfile.ZipFile(archive, "r") as zf:
                names = set(zf.namelist())

                if model_sessions:
                    latest_session = model_sessions[0]
                    session_filename = latest_session.get("filename", "")
                    session_entry = self._zip_entry(
                        self.SESSION_DIR, session_filename
                    )

                    if session_entry not in names:
                        sys.stderr.write(
                            f"No session file found for model: {target_model_name}\n"
                        )
                        return None

                    session_data = json.loads(
                        zf.read(session_entry).decode("utf-8")
                    )

                    self.model_name = (
                        target_model_name
                        or session_data.get("model_name")
                        or self.model_name
                    )

                    sys.stdout.write(
                        f"Session loaded from: {archive} for model: "
                        f"{self.model_name} "
                        f"(session: {latest_session.get('session_id', '?')})\n"
                    )

                    return session_data.get("data", session_data)

                ### Backward compatibility: legacy '<model_name>.json' entry
                if target_model_name:
                    legacy_entry = self._legacy_entry(target_model_name)

                    if legacy_entry in names:
                        session_data = json.loads(
                            zf.read(legacy_entry).decode("utf-8")
                        )

                        self.model_name = target_model_name

                        sys.stdout.write(
                            f"Legacy session loaded from: {archive} "
                            f"for model: {target_model_name}\n"
                        )

                        return session_data.get("data", session_data)

            sys.stderr.write(f"No session found for model: {target_model_name}\n")
            return None

        except Exception as error:
            tb = __import__("traceback").format_exc()
            sys.stderr.write(f"Error loading session: {error}\n{tb}")
            return None

    def list_sessions(self, model_name=None):
        """List all sessions for a given model.

        Args:
            model_name (str, optional): Model name to list the sessions for.
                If None, uses self.model_name.

        Returns:
            list: Session metadata dicts (most recent first).
        """
        target_model_name = model_name if model_name else self.model_name

        archive = self._get_archive_path()

        if not archive:
            return []

        try:
            metadata = self._get_session_metadata(archive)
            return self._session_records(metadata, target_model_name)

        except Exception as error:
            sys.stderr.write(f"Error listing sessions: {error}\n")
            return []

    def remove_session(self, session_id=None):
        """Remove a specific AI assistant session from the model archive.

        Args:
            session_id (str, optional): Specific session ID (or session
                filename) to remove. If None, removes the most recent session
                for the current model.

        Returns:
            bool: True if the session was removed successfully, False otherwise.
        """
        if not session_id and not self.model_name:
            sys.stderr.write(
                "Cannot remove session: session_id or model_name not set.\n"
            )
            return False

        archive = self._get_archive_path()

        if not archive:
            return False

        try:
            metadata = self._get_session_metadata(archive)
            records = list(metadata.get("sessions", []))
            target_session = None

            if session_id:
                for record in records:
                    if session_id in (
                        record.get("session_id"),
                        record.get("filename"),
                    ):
                        target_session = record
                        break
            else:
                model_sessions = self._session_records(metadata, self.model_name)
                if model_sessions:
                    target_session = model_sessions[0]

            remove_entries = []
            legacy_entry = (
                self._legacy_entry(self.model_name) if self.model_name else None
            )

            if target_session:
                records.remove(target_session)
                metadata["sessions"] = records
                remove_entries.append(
                    self._zip_entry(
                        self.SESSION_DIR, target_session.get("filename", "")
                    )
                )
                remove_entries.extend(self._metadata_entries())

                success = self._rewrite_archive(
                    archive,
                    remove_entries=remove_entries,
                    add_entries={
                        self._zip_entry(
                            self.SESSION_DIR, self.METADATA_FILE
                        ): json.dumps(metadata, indent=2, ensure_ascii=False)
                    },
                )
            elif legacy_entry and self._zip_contains(archive, legacy_entry):
                ### Legacy session file
                metadata["sessions"] = records
                success = self._rewrite_archive(
                    archive,
                    remove_entries=[legacy_entry],
                    add_entries=None,
                )
            else:
                return False

            if success:
                sys.stdout.write(f"Session removed from: {archive}\n")

            return success

        except Exception as error:
            tb = __import__("traceback").format_exc()
            sys.stderr.write(f"Error removing session: {error}\n{tb}")
            return False

    def clear_sessions(self, model_name=None):
        """Remove all sessions for a given model from the model archive.

        Args:
            model_name (str, optional): Model name to clear the sessions for.
                If None, uses self.model_name.

        Returns:
            bool: True if the sessions were cleared successfully, False otherwise.
        """
        target_model_name = model_name if model_name else self.model_name

        if not target_model_name:
            return False

        archive = self._get_archive_path()

        if not archive:
            return False

        try:
            metadata = self._get_session_metadata(archive)
            model_sessions = self._session_records(metadata, target_model_name)

            remove_entries = [
                self._zip_entry(self.SESSION_DIR, record.get("filename", ""))
                for record in model_sessions
                if record.get("filename")
            ]

            ### Also remove the legacy single-session file
            remove_entries.append(self._legacy_entry(target_model_name))

            metadata["sessions"] = [
                record
                for record in metadata.get("sessions", [])
                if record.get("model_name") != target_model_name
            ]

            remove_entries.extend(self._metadata_entries())

            return self._rewrite_archive(
                archive,
                remove_entries=remove_entries,
                add_entries={
                    self._zip_entry(
                        self.SESSION_DIR, self.METADATA_FILE
                    ): json.dumps(metadata, indent=2, ensure_ascii=False)
                },
            )

        except Exception as error:
            sys.stderr.write(f"Error clearing sessions: {error}\n")
            return False

    # ==================================================================
    # Panel lifecycle
    # ==================================================================
    def _should_auto_save(self):
        """Return True when automatic session save is enabled and supported."""
        return bool(
            getattr(self, "_enable_session_storage", True)
            and (self._session_archive or self._get_archive_path())
        )

    def _should_auto_load(self):
        """Return True when automatic session load is enabled and supported."""
        return self._should_auto_save()

    def on_panel_load(self, force=False):
        """Load the most recent session when the panel is shown.

        The session is restored only once per panel (or per model change) unless
        ``force`` is True. Only .amd and .cmd models are supported.
        """
        if getattr(self, "_session_loaded", False) and not force:
            return False

        if not self._should_auto_load():
            return False

        ### Mark as loaded before restoring so this cannot recurse
        self._session_loaded = True

        session_data = self.load_session()

        if not session_data:
            return False

        self._restore_session_to_ui(session_data)

        sys.stdout.write(
            f"Session auto-loaded for model: {self.model_name}\n"
        )

        return True

    def on_panel_close(self, event=None):
        """Save the current session when the panel is closed.

        Only .amd and .cmd models are supported.
        """
        result = False

        if self._should_auto_save():
            session_data = self._get_current_session()

            if session_data:
                result = self.store_session(session_data)

                if result:
                    sys.stdout.write(
                        f"Session auto-saved for model: {self.model_name}\n"
                    )

        if event is not None and hasattr(event, "Skip"):
            event.Skip()

        return result

    def reset_session_ui(self):
        """Clear the AI panel conversation and detach the loaded session."""
        self._ask_messages = []
        self._ask_context_signature = None
        self._session_loaded = True

        if hasattr(self, "prompt_input"):
            self.prompt_input.Clear()

        if hasattr(self, "output"):
            self.output.Clear()

    @staticmethod
    def _zip_contains(archive, entry):
        """Return True when ``archive`` contains ``entry``."""
        try:
            with zipfile.ZipFile(archive, "r") as zf:
                return entry in zf.namelist()
        except (OSError, zipfile.BadZipFile):
            return False

    # ==================================================================
    # Current session capture / restore
    # ==================================================================
    def _get_current_session(self):
        """Get the current session state from the panel.

        Returns:
            dict or None: Current session data or None if not available.
        """
        try:
            ### Get mode selection (0=Ask, 1=Build)
            mode = 0
            if hasattr(self, "mode_choice"):
                mode = self.mode_choice.GetSelection()

            ### Get prompt text
            prompt = ""
            if hasattr(self, "prompt_input"):
                prompt = self.prompt_input.GetValue()

            ### Get whether the code context is included in Ask mode
            include_context = False
            if hasattr(self, "include_code_context"):
                include_context = bool(self.include_code_context.GetValue())

            ### Get conversation messages
            messages = getattr(self, "_ask_messages", [])

            ### Get context signature if present
            context_signature = getattr(self, "_ask_context_signature", None)

            return {
                "mode": mode,
                "prompt": prompt,
                "include_context": include_context,
                "messages": messages,
                "context_signature": context_signature,
            }

        except Exception as error:
            tb = __import__("traceback").format_exc()
            sys.stderr.write(f"Error getting current session state: {error}\n{tb}")
            return None

    def _restore_session_to_ui(self, session_data):
        """Restore session data to the panel UI components.

        Args:
            session_data (dict): Session data containing mode, prompt, messages.

        Returns:
            bool: True when the session was restored.
        """
        if not isinstance(session_data, dict):
            return False

        try:
            ### Restore mode selection (sync derived widgets)
            if hasattr(self, "mode_choice") and "mode" in session_data:
                try:
                    mode = int(session_data["mode"])
                except (TypeError, ValueError):
                    mode = 0

                if 0 <= mode < self.mode_choice.GetCount():
                    self.mode_choice.SetSelection(mode)

                on_mode_changed = getattr(self, "_on_mode_changed", None)
                if callable(on_mode_changed):
                    on_mode_changed(None)

            ### Restore prompt text
            if hasattr(self, "prompt_input") and "prompt" in session_data:
                self.prompt_input.SetValue(session_data.get("prompt") or "")

            ### Restore code context option
            if hasattr(self, "include_code_context") and "include_context" in session_data:
                self.include_code_context.SetValue(
                    bool(session_data.get("include_context"))
                )

            ### Restore conversation messages
            messages = session_data.get("messages")
            if isinstance(messages, list):
                self._ask_messages = messages

            ### Restore context signature (JSON serializes tuples as lists)
            if "context_signature" in session_data:
                signature = session_data.get("context_signature")
                self._ask_context_signature = (
                    tuple(signature) if isinstance(signature, list) else signature
                )

            return True

        except Exception as error:
            tb = __import__("traceback").format_exc()
            sys.stderr.write(f"Error restoring session to UI: {error}\n{tb}")
            return False
