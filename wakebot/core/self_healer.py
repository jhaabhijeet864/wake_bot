"""
WakeBot Self-Healer — Agentic Error Auto-Fixer (v2.1.0)
Detects on-screen errors, queries LLM for structured patches, and applies
fixes directly to source files after user confirmation via TTS + hotkey.

Pipeline:
  ERROR_DETECTED event → enrich context → LLM query → TTS announce →
  hotkey confirm (F9/Escape) → backup file → apply patch → emit ERROR_HEALED

Respects local_only mode and privacy settings.
"""

import os
import re
import json
import time
import shutil
import threading
import subprocess
from typing import Optional, Dict, Any

from wakebot.core.logger import WakeBotLogger
from wakebot.core.event_bus import EventBus
from wakebot.core.workspace_state import WorkspaceState
from wakebot.triggers.tts.tts_engine import TTSEngine

try:
    import keyboard  # For global hotkey listening
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


# ---------------------------------------------------------------------------
# VS Code window title parsing patterns
# ---------------------------------------------------------------------------
# Typical VS Code title: "filename.py — FolderName — Visual Studio Code"
# Or with path: "filename.py - D:\path\to\project - Visual Studio Code"
_VSCODE_TITLE_RE = re.compile(
    r"^(.+?)\s*[-—]+\s*(.+?)\s*[-—]+\s*Visual Studio Code",
    re.IGNORECASE,
)

# Traceback line number patterns
_PYTHON_LINE_RE = re.compile(r'File "(.+?)", line (\d+)', re.IGNORECASE)
_TS_LINE_RE = re.compile(r"(\S+\.tsx?)\((\d+),\s*\d+\)", re.IGNORECASE)
_GENERIC_LINE_RE = re.compile(r"line\s+(\d+)", re.IGNORECASE)

# LLM system prompt for structured fix generation
_HEALER_SYSTEM_PROMPT = """You are a code repair assistant. Given an error traceback and the surrounding source code, produce a SINGLE JSON object with these exact keys:

{
  "file": "absolute path to the file that needs fixing",
  "line": <integer line number of the error>,
  "diagnosis": "one-sentence plain-English explanation of the bug",
  "original": "the exact lines of code that are broken (verbatim from source)",
  "replacement": "the corrected lines of code that fix the bug"
}

Rules:
- The "original" field MUST be an exact substring of the provided source code.
- The "replacement" field must be a drop-in replacement — same indentation level.
- Keep the fix minimal. Do NOT rewrite unrelated code.
- If you cannot determine a fix, set "diagnosis" to "Unable to determine fix" and leave "original" and "replacement" empty.
- Return ONLY the JSON object. No markdown fences, no explanation outside the JSON."""


class SelfHealer:
    """
    Agentic error auto-fixer. Subscribes to ERROR_DETECTED events,
    queries an LLM for a fix, and applies it with user confirmation.
    """

    def __init__(
        self,
        workspace_state: WorkspaceState,
        vlm_provider: str = "ollama",
        logger: Optional[WakeBotLogger] = None,
        cooldown_s: float = 15.0,
        confirm_hotkey: str = "F9",
        auto_backup: bool = True,
        llm_model: str = "llama3",
    ):
        self._workspace_state = workspace_state
        self._vlm_provider = vlm_provider
        self._logger = logger or WakeBotLogger()
        self._cooldown_s = cooldown_s
        self._confirm_hotkey = confirm_hotkey.lower()
        self._auto_backup = auto_backup
        self._llm_model = llm_model

        self._event_bus = EventBus()
        self._tts = TTSEngine()

        # State
        self._last_heal_time = 0.0
        self._enabled = True
        self._pending_fix: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

        # Subscribe to error events
        self._event_bus.subscribe("ERROR_DETECTED", self.on_error_detected)
        self._logger.info("Self-Healer initialized and subscribed to ERROR_DETECTED.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enable(self):
        """Enable the self-healer."""
        self._enabled = True
        self._logger.info("Self-Healer ENABLED.")

    def disable(self):
        """Disable the self-healer."""
        self._enabled = False
        self._logger.info("Self-Healer DISABLED.")

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    # Event Handler — Entry Point
    # ------------------------------------------------------------------

    def on_error_detected(self, data: Optional[Dict] = None):
        """
        Entry point: fired by EventBus when ScreenMonitor detects an error.
        Runs the full heal pipeline on a dedicated thread.
        """
        if not self._enabled:
            return

        if not data:
            return

        # Debounce: skip if we just healed
        now = time.time()
        if now - self._last_heal_time < self._cooldown_s:
            self._logger.info(
                f"Self-Healer: cooldown active ({self._cooldown_s}s). Skipping."
            )
            return

        # Run the full pipeline on a background thread
        threading.Thread(
            target=self._heal_pipeline,
            args=(data,),
            name="SelfHealer-Pipeline",
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    # Core Pipeline
    # ------------------------------------------------------------------

    def _heal_pipeline(self, data: Dict[str, Any]):
        """Full agentic loop: enrich → query → announce → confirm → patch."""
        try:
            self._last_heal_time = time.time()
            self._workspace_state.set("healer_active", True)

            # Step 1: Enrich the error context
            context = self._enrich_error_context(data)
            if not context.get("error_context"):
                self._logger.warning("Self-Healer: no usable error context. Aborting.")
                return

            self._logger.info(
                f"Self-Healer: processing {context.get('error_type', 'unknown')} "
                f"error in '{context.get('source_file', 'unknown')}'"
            )

            # Step 2: Query LLM for a fix
            fix = self._query_llm_for_fix(context)
            if not fix or not fix.get("original") or not fix.get("replacement"):
                self._logger.warning("Self-Healer: LLM could not produce a fix.")
                self._tts.say(
                    "I detected an error on your screen, but I couldn't determine "
                    "a reliable fix. You may want to check it manually."
                )
                return

            # Step 3: Announce via TTS and wait for confirmation
            approved = self._announce_and_confirm(fix)
            if not approved:
                self._logger.info("Self-Healer: fix REJECTED by user.")
                self._tts.say("Understood. I won't apply the fix.")
                return

            # Step 4: Apply the patch
            success = self._apply_patch(fix)
            if success:
                self._logger.action(
                    f"Self-Healer: ✅ patched {fix.get('file', '?')} "
                    f"(line {fix.get('line', '?')})"
                )
                self._tts.say("Fix applied successfully!")

                # Update workspace state
                self._workspace_state.update({
                    "healer_last_diagnosis": fix.get("diagnosis", ""),
                    "healer_last_file": fix.get("file", ""),
                    "healer_last_timestamp": time.time(),
                    "healer_patches_applied": (
                        self._workspace_state.get("healer_patches_applied", 0) + 1
                    ),
                })

                # Emit success event
                self._event_bus.emit("ERROR_HEALED", {
                    "file": fix.get("file", ""),
                    "line": fix.get("line", 0),
                    "diagnosis": fix.get("diagnosis", ""),
                })
            else:
                self._logger.error("Self-Healer: patch application FAILED.")
                self._tts.say(
                    "I wasn't able to apply the fix. "
                    "The backup file is preserved if one was created."
                )

        except Exception as e:
            self._logger.error(f"Self-Healer pipeline error: {e}")
        finally:
            self._workspace_state.set("healer_active", False)

    # ------------------------------------------------------------------
    # Step 1: Context Enrichment
    # ------------------------------------------------------------------

    def _enrich_error_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich the raw ERROR_DETECTED payload with:
        - Parsed source file path (from VS Code window title)
        - Source file content (±30 lines around the error)
        - Error classification
        """
        context = {
            "error_context": data.get("error_context", ""),
            "error_type": data.get("error_type", "unknown"),
            "full_text": data.get("full_text", ""),
            "active_window": data.get("active_window", ""),
            "source_file": "",
            "source_snippet": "",
            "error_line": 0,
        }

        # Try to extract file path from the traceback text itself
        file_path, line_num = self._parse_error_location(context["error_context"])

        # Fallback: parse VS Code window title
        if not file_path:
            file_path = self._parse_vscode_title(context["active_window"])

        if file_path and os.path.isfile(file_path):
            context["source_file"] = file_path
            context["error_line"] = line_num or 0

            # Read source file and extract snippet
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                if line_num and line_num > 0:
                    start = max(0, line_num - 31)
                    end = min(len(lines), line_num + 30)
                    snippet_lines = lines[start:end]
                    # Add line numbers for LLM context
                    numbered = [
                        f"{start + i + 1:4d} | {line}"
                        for i, line in enumerate(snippet_lines)
                    ]
                    context["source_snippet"] = "".join(numbered)
                else:
                    # No line number — send first 80 lines
                    context["source_snippet"] = "".join(lines[:80])
            except Exception as e:
                self._logger.error(f"Self-Healer: failed to read source file: {e}")

        return context

    def _parse_error_location(self, text: str) -> tuple:
        """Extract file path and line number from a traceback string."""
        # Python: File "path/to/file.py", line 42
        match = _PYTHON_LINE_RE.search(text)
        if match:
            return match.group(1), int(match.group(2))

        # TypeScript: src/file.ts(42, 5)
        match = _TS_LINE_RE.search(text)
        if match:
            return match.group(1), int(match.group(2))

        # Generic: "line 42"
        match = _GENERIC_LINE_RE.search(text)
        if match:
            return None, int(match.group(1))

        return None, 0

    @staticmethod
    def _parse_vscode_title(title: str) -> Optional[str]:
        """
        Extract file path from a VS Code window title.
        Typical formats:
          "main.py — WakeBot — Visual Studio Code"
          "main.py - D:\\Projects\\WakeBot - Visual Studio Code"
        """
        if not title or "Visual Studio Code" not in title:
            return None

        match = _VSCODE_TITLE_RE.match(title)
        if not match:
            return None

        filename = match.group(1).strip()
        workspace_or_path = match.group(2).strip()

        # If the workspace part looks like an absolute path, join
        if os.path.isabs(workspace_or_path):
            candidate = os.path.join(workspace_or_path, filename)
            if os.path.isfile(candidate):
                return candidate

        # Try the filename as an absolute path (sometimes VS Code shows full path)
        if os.path.isfile(filename):
            return filename

        # Walk common project locations
        for root_candidate in [
            workspace_or_path,
            os.path.join("D:\\Coding\\Projects", workspace_or_path),
        ]:
            if os.path.isdir(root_candidate):
                for dirpath, _, filenames in os.walk(root_candidate):
                    if filename in filenames:
                        return os.path.join(dirpath, filename)

        return None

    # ------------------------------------------------------------------
    # Step 2: LLM Query
    # ------------------------------------------------------------------

    def _query_llm_for_fix(self, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Send a structured prompt to the LLM and parse the JSON fix response.
        Uses text-only model (llama3) for pure tracebacks.
        """
        # Build the user prompt
        parts = [
            f"## Error Type: {context.get('error_type', 'unknown')}",
            f"## Active Window: {context.get('active_window', 'unknown')}",
            "",
            "## Error Traceback (from screen OCR):",
            "```",
            context.get("error_context", "No traceback available"),
            "```",
        ]

        if context.get("source_file"):
            parts.extend([
                "",
                f"## Source File: {context['source_file']}",
                f"## Error Line: {context.get('error_line', 'unknown')}",
                "",
                "## Source Code:",
                "```",
                context.get("source_snippet", "No source available"),
                "```",
            ])

        user_prompt = "\n".join(parts)

        # Determine provider (respect local_only)
        effective_provider = self._vlm_provider
        is_local_only = self._workspace_state.get("local_only", False)
        if is_local_only and effective_provider == "gemini":
            self._logger.info(
                "Self-Healer: local-only mode active, falling back to Ollama."
            )
            effective_provider = "ollama"

        # Query
        raw_response = None
        if effective_provider == "ollama":
            raw_response = self._query_ollama(user_prompt)
        elif effective_provider == "gemini":
            raw_response = self._query_gemini(user_prompt)

        if not raw_response:
            return None

        # Parse JSON from response
        return self._parse_fix_json(raw_response, context)

    def _query_ollama(self, prompt: str) -> Optional[str]:
        """Query local Ollama with a text-only model."""
        try:
            import requests

            payload = {
                "model": self._llm_model,
                "system": _HEALER_SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            self._logger.error(f"Self-Healer: Ollama query failed: {e}")
            return None

    def _query_gemini(self, prompt: str) -> Optional[str]:
        """Query Google Gemini for a text-only fix."""
        try:
            import google.generativeai as genai
            from wakebot.core.credentials import get_credential

            api_key = get_credential("GEMINI_API_KEY")
            if not api_key:
                self._logger.error(
                    "Self-Healer: GEMINI_API_KEY not found."
                )
                return None

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-pro")

            full_prompt = f"{_HEALER_SYSTEM_PROMPT}\n\n{prompt}"
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            self._logger.error(f"Self-Healer: Gemini query failed: {e}")
            return None

    def _parse_fix_json(
        self, raw: str, context: Dict[str, Any]
    ) -> Optional[Dict]:
        """Extract and validate the JSON fix object from LLM output."""
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                # Remove opening fence (```json or ```)
                cleaned = re.sub(r"^```\w*\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)

            fix = json.loads(cleaned)

            # Validate required fields
            required = ["diagnosis", "original", "replacement"]
            for key in required:
                if key not in fix:
                    self._logger.warning(
                        f"Self-Healer: LLM response missing '{key}' field."
                    )
                    return None

            # Fill in file path if LLM didn't provide one
            if not fix.get("file") and context.get("source_file"):
                fix["file"] = context["source_file"]

            # Fill in line number
            if not fix.get("line") and context.get("error_line"):
                fix["line"] = context["error_line"]

            return fix

        except json.JSONDecodeError as e:
            self._logger.error(
                f"Self-Healer: failed to parse LLM JSON response: {e}"
            )
            self._logger.error(f"Self-Healer: raw response: {raw[:300]}")
            return None

    # ------------------------------------------------------------------
    # Step 3: TTS Announcement & User Confirmation
    # ------------------------------------------------------------------

    def _announce_and_confirm(self, fix: Dict[str, Any]) -> bool:
        """
        Speak the diagnosis via TTS and wait for hotkey confirmation.
        Returns True if user approves (F9), False if rejected (Escape/timeout).
        """
        filename = os.path.basename(fix.get("file", "unknown"))
        line = fix.get("line", "?")
        diagnosis = fix.get("diagnosis", "an unknown issue")

        announcement = (
            f"Hey! I noticed an error on line {line} of {filename}. "
            f"{diagnosis}. "
            f"Press {self._confirm_hotkey.upper()} to apply the fix, "
            f"or Escape to skip."
        )

        self._logger.info(f"Self-Healer: 🔊 {announcement}")
        self._tts.say(announcement)

        # Wait for hotkey confirmation
        if not HAS_KEYBOARD:
            self._logger.warning(
                "Self-Healer: 'keyboard' module not installed. "
                "Auto-rejecting fix (install with: pip install keyboard)."
            )
            return False

        # Use threading.Event for the confirmation wait
        confirmed = threading.Event()
        rejected = threading.Event()

        def on_confirm():
            confirmed.set()

        def on_reject():
            rejected.set()

        try:
            keyboard.on_press_key(self._confirm_hotkey, lambda _: on_confirm(), suppress=False)
            keyboard.on_press_key("escape", lambda _: on_reject(), suppress=False)

            # Wait up to 30 seconds for user response
            start = time.monotonic()
            while time.monotonic() - start < 30.0:
                if confirmed.is_set():
                    return True
                if rejected.is_set():
                    return False
                time.sleep(0.1)

            # Timeout — auto-reject
            self._logger.info("Self-Healer: confirmation timed out (30s). Auto-rejecting.")
            self._tts.say("No response received. Skipping the fix.")
            return False

        except Exception as e:
            self._logger.error(f"Self-Healer: hotkey listener error: {e}")
            return False
        finally:
            try:
                keyboard.unhook_all()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Step 4: Patch Application
    # ------------------------------------------------------------------

    def _apply_patch(self, fix: Dict[str, Any]) -> bool:
        """
        Apply the fix to the source file:
        1. Create a .bak backup
        2. Find the exact 'original' block in the file
        3. Replace with 'replacement' block
        4. Signal VS Code to reload
        """
        file_path = fix.get("file", "")
        original = fix.get("original", "")
        replacement = fix.get("replacement", "")

        if not file_path or not os.path.isfile(file_path):
            self._logger.error(
                f"Self-Healer: target file not found: {file_path}"
            )
            return False

        if not original:
            self._logger.error("Self-Healer: no 'original' block to replace.")
            return False

        try:
            # Read current file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Verify the original block exists
            if original not in content:
                # Try with normalized whitespace (LLM sometimes changes indent)
                self._logger.warning(
                    "Self-Healer: exact match not found. "
                    "Trying whitespace-normalized match..."
                )
                # Normalize both for comparison
                norm_original = re.sub(r"[ \t]+", " ", original.strip())
                norm_content = re.sub(r"[ \t]+", " ", content)

                if norm_original not in norm_content:
                    self._logger.error(
                        "Self-Healer: 'original' block not found in file "
                        "(even after whitespace normalization). Aborting patch."
                    )
                    return False

                # Find the actual original text using line-by-line matching
                original_lines = original.strip().splitlines()
                content_lines = content.splitlines(True)
                match_start = None

                for i in range(len(content_lines) - len(original_lines) + 1):
                    window = content_lines[i:i + len(original_lines)]
                    window_stripped = [l.strip() for l in window]
                    orig_stripped = [l.strip() for l in original_lines]
                    if window_stripped == orig_stripped:
                        match_start = i
                        break

                if match_start is not None:
                    # Use the actual lines from the file for replacement
                    actual_original = "".join(
                        content_lines[match_start:match_start + len(original_lines)]
                    )
                    original = actual_original
                else:
                    self._logger.error(
                        "Self-Healer: could not locate original block by line matching."
                    )
                    return False

            # Step 1: Create backup
            if self._auto_backup:
                backup_path = file_path + ".bak"
                shutil.copy2(file_path, backup_path)
                self._logger.info(f"Self-Healer: backup created → {backup_path}")

            # Step 2: Apply replacement
            new_content = content.replace(original, replacement, 1)

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)

            self._logger.action(f"Self-Healer: ✅ patch written to {file_path}")

            # Step 3: Open the file in VS Code at the error line
            line = fix.get("line", 1)
            try:
                subprocess.Popen(
                    ["code", "--goto", f"{file_path}:{line}"],
                    shell=True,
                )
            except Exception as e:
                self._logger.warning(
                    f"Self-Healer: VS Code open failed (non-critical): {e}"
                )

            return True

        except PermissionError:
            self._logger.error(
                f"Self-Healer: permission denied writing to {file_path}"
            )
            return False
        except Exception as e:
            self._logger.error(f"Self-Healer: patch application error: {e}")
            return False
