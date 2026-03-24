from __future__ import annotations

import html
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    Qt,
    QVBoxLayout,
    qconnect,
)
from aqt.utils import showInfo, showWarning


_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

_SUCCESS_ATTRIBUTION = (
    "\n\nCreated by Kyle Bringhurst | Founder of SyncSOAP"
)

_MAX_USER_DETAIL_LEN = 450

_USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".nbome_gemini_usage.json")
_DEFAULT_DAILY_CAP = 250
_PLACEHOLDER_API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"
# Direct link to create/copy keys (AI Studio); see https://aistudio.google.com/app/apikey
_GEMINI_API_KEY_HELP_URL = "https://aistudio.google.com/app/apikey"

# AnKing hierarchical UWorld tags, e.g. tag:#AK_Step2_v12::#UWorld::Step::2857
_UWORLD_TAG_PRESETS: dict[str, str] = {
    "step1_v11": "#AK_Step1_v11::#UWorld::Step::",
    "step1_v12": "#AK_Step1_v12::#UWorld::Step::",
    "step2_v11": "#AK_Step2_v11::#UWorld::Step::",
    "step2_v12": "#AK_Step2_v12::#UWorld::Step::",
}

_INJECT_TRACK_CHOICES: tuple[tuple[str, str], ...] = (
    ("step1_v11", "Step_1_v11"),
    ("step1_v12", "Step_1_v12"),
    ("step2_v11", "Step_2_v11"),
    ("step2_v12", "Step_2_v12"),
    ("custom", "Custom prefix (from Add-on Config)"),
    ("legacy_wildcard", "Legacy: tag contains ID (any deck)"),
)


def _addon_config() -> dict[str, Any]:
    cfg = mw.addonManager.getConfig(__name__)
    return cfg if isinstance(cfg, dict) else {}


def _merged_ui_config() -> dict[str, Any]:
    """Values for the settings dialog (sensible defaults + user meta.json)."""
    raw = _addon_config()
    api = (raw.get("api_key") or "").strip()
    if api == _PLACEHOLDER_API_KEY:
        api = ""
    tf = (raw.get("target_field") or "Extra").strip() or "Extra"
    limit = _coerce_bool(raw.get("limit_daily_gemini_requests"), True)
    try:
        cap = int(raw.get("daily_gemini_request_cap", _DEFAULT_DAILY_CAP))
    except (TypeError, ValueError):
        cap = _DEFAULT_DAILY_CAP
    if cap < 1:
        cap = _DEFAULT_DAILY_CAP
    custom_pf = (raw.get("custom_uworld_tag_prefix") or "").strip()
    mode = (raw.get("anking_uworld_tag_mode") or "step2_v12").strip()
    valid_modes = {k for k, _ in _INJECT_TRACK_CHOICES}
    if mode not in valid_modes:
        mode = "step2_v12"
    return {
        "api_key": api,
        "target_field": tf,
        "limit_daily_gemini_requests": limit,
        "daily_gemini_request_cap": cap,
        "custom_uworld_tag_prefix": custom_pf,
        "anking_uworld_tag_mode": mode,
    }


def _show_config_dialog() -> None:
    initial = _merged_ui_config()
    dlg = QDialog(mw)
    dlg.setWindowTitle("NBOME Pearl Injector — Settings")
    dlg.setMinimumWidth(500)

    api_header = QLabel(
        "<b>Gemini API key (required)</b><br>"
        "This add-on uses <i>your</i> key (Bring Your Own Key). If you have not created one before:"
    )
    api_header.setWordWrap(True)
    api_header.setTextFormat(Qt.TextFormat.RichText)

    api_steps = QLabel(
        "• Open the blue link below and sign in with your Google account.<br>"
        "• Click <b>Create API key</b> in Google AI Studio (or copy an existing key).<br>"
        "• Paste the full key into the field under “Gemini API key”.<br>"
        "• The key is saved only on this computer; the add-on author never receives it."
    )
    api_steps.setWordWrap(True)
    api_steps.setTextFormat(Qt.TextFormat.RichText)

    api_link = QLabel(
        f'<a href="{_GEMINI_API_KEY_HELP_URL}">'
        "→ Open Google AI Studio (API keys)</a>"
    )
    api_link.setOpenExternalLinks(True)
    api_link.setWordWrap(True)
    api_link.setTextInteractionFlags(
        Qt.TextInteractionFlag.LinksAccessibleByMouse
        | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
    )

    api_edit = QLineEdit(dlg)
    api_edit.setText(initial["api_key"])
    api_edit.setPlaceholderText("Paste your API key here after creating it in AI Studio")

    field_edit = QLineEdit(dlg)
    field_edit.setText(initial["target_field"])

    limit_cb = QCheckBox("Limit daily Gemini requests (recommended)")
    limit_cb.setChecked(initial["limit_daily_gemini_requests"])

    cap_spin = QSpinBox(dlg)
    cap_spin.setRange(1, 99_999)
    cap_spin.setValue(int(initial["daily_gemini_request_cap"]))

    def _sync_cap_enabled(checked: bool) -> None:
        cap_spin.setEnabled(checked)

    qconnect(limit_cb.toggled, _sync_cap_enabled)
    _sync_cap_enabled(limit_cb.isChecked())

    hint = QLabel(
        "The daily cap counts only successful pearl injections from this add-on on "
        f"this computer (default {_DEFAULT_DAILY_CAP} ≈ typical Gemini 2.5 Flash free tier). "
        "It is not read from Google’s servers—see the README."
    )
    hint.setWordWrap(True)

    custom_prefix_edit = QLineEdit(dlg)
    custom_prefix_edit.setText(initial["custom_uworld_tag_prefix"])
    custom_prefix_edit.setPlaceholderText(
        "e.g. #AK_Step2_v12::#UWorld::Step::   (no ID at the end)"
    )
    prefix_hint = QLabel(
        "Used when the inject dialog is set to “Custom prefix”. Must match your deck’s "
        "hierarchical tag up to (but not including) the numeric UWorld ID."
    )
    prefix_hint.setWordWrap(True)

    form = QFormLayout()
    form.addRow("Gemini API key:", api_edit)
    form.addRow("Target field:", field_edit)
    form.addRow(limit_cb)
    form.addRow("Max requests per day:", cap_spin)
    form.addRow("Custom UWorld tag prefix:", custom_prefix_edit)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    qconnect(buttons.accepted, dlg.accept)
    qconnect(buttons.rejected, dlg.reject)

    root = QVBoxLayout(dlg)
    root.addWidget(api_header)
    root.addWidget(api_steps)
    root.addWidget(api_link)
    root.addLayout(form)
    root.addWidget(prefix_hint)
    root.addWidget(hint)
    root.addWidget(buttons)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return

    key = api_edit.text().strip()
    new_cfg = dict(_addon_config())
    new_cfg.update(
        {
            "api_key": key if key else _PLACEHOLDER_API_KEY,
            "target_field": field_edit.text().strip() or "Extra",
            "limit_daily_gemini_requests": bool(limit_cb.isChecked()),
            "daily_gemini_request_cap": int(cap_spin.value()),
            "custom_uworld_tag_prefix": custom_prefix_edit.text().strip(),
        }
    )
    mw.addonManager.writeConfig(__name__, new_cfg)


def _sanitize_user_detail(text: str) -> str:
    """Single-line, length-limited text safe to show in dialogs (not a traceback)."""
    t = " ".join(str(text).replace("\r", " ").split())
    if len(t) > _MAX_USER_DETAIL_LEN:
        t = t[: _MAX_USER_DETAIL_LEN - 3].rstrip() + "..."
    return t


def _friendly_api_one_line(exc: BaseException) -> str:
    """Short, single-line reason for a failed Gemini call (for batch error lists)."""
    detail = _sanitize_user_detail(str(exc)) if exc else ""
    if not detail:
        return "Gemini request failed (check API key and internet)."
    return f"Gemini request failed: {detail}"


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return default


def _usage_state_for_today() -> tuple[str, int]:
    """Return (iso_date, successful_request_count_today)."""
    today = date.today().isoformat()
    count = 0
    try:
        with open(_USAGE_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return today, 0
    if not isinstance(raw, dict):
        return today, 0
    if raw.get("date") != today:
        return today, 0
    try:
        count = int(raw.get("successful_requests", 0))
    except (TypeError, ValueError):
        count = 0
    return today, max(0, count)


def _persist_usage(today: str, total_successful_today: int) -> None:
    try:
        with open(_USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"date": today, "successful_requests": total_successful_today},
                f,
                indent=2,
            )
    except OSError:
        pass


def _daily_limit_settings(cfg: dict[str, Any]) -> tuple[bool, int]:
    enforce = _coerce_bool(cfg.get("limit_daily_gemini_requests"), True)
    try:
        cap = int(cfg.get("daily_gemini_request_cap", _DEFAULT_DAILY_CAP))
    except (TypeError, ValueError):
        cap = _DEFAULT_DAILY_CAP
    if enforce and cap < 1:
        cap = _DEFAULT_DAILY_CAP
    return enforce, cap


def _usage_footer(
    *,
    enforce_limit: bool,
    cap: int,
    count_before: int,
    updated_this_run: int,
) -> str:
    total = count_before + updated_this_run
    if enforce_limit and cap >= 1:
        return (
            f"\n\nTracked Gemini calls today (this add-on, this device): "
            f"{total} of {cap}. Resets at local midnight."
        )
    return (
        "\n\nDaily limit is off in Config; this add-on does not cap calls. "
        "Watch usage and billing in Google AI Studio if you are not on free-only terms."
    )


def _parse_uworld_ids(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    normalized = raw.replace("\n", ",")
    parts = re.split(r"[,]+", normalized)
    return [p.strip() for p in parts if p.strip()]


def _format_quoted_tag_search(full_tag: str) -> str:
    """Exact hierarchical tag search; quoted so #, ::, etc. are literal."""
    escaped = full_tag.replace("\\", "\\\\").replace('"', '\\"')
    return f'tag:"{escaped}"'


def _build_uworld_search_query(uw_id: str, mode: str, custom_prefix: str) -> str:
    if mode == "legacy_wildcard":
        return f"tag:*{uw_id}*"
    if mode == "custom":
        p = (custom_prefix or "").strip()
        full = f"{p}{uw_id}"
        return _format_quoted_tag_search(full)
    prefix = _UWORLD_TAG_PRESETS.get(mode) or _UWORLD_TAG_PRESETS["step2_v12"]
    full = f"{prefix}{uw_id}"
    return _format_quoted_tag_search(full)


def _comlex_level_from_track(mode: str, custom_prefix: str) -> int:
    """1 = COMLEX Level 1 (Step 1 deck), 2 = COMLEX Level 2 (Step 2 deck)."""
    if mode.startswith("step1_"):
        return 1
    if mode.startswith("step2_"):
        return 2
    if mode == "custom":
        p = custom_prefix or ""
        if re.search(r"#AK_Step1|_Step1_|Step1_v", p, re.IGNORECASE):
            return 1
        if re.search(r"#AK_Step2|_Step2_|Step2_v", p, re.IGNORECASE):
            return 2
        return 2
    return 2


def _show_inject_dialog() -> tuple[list[str], str] | None:
    merged = _merged_ui_config()
    dlg = QDialog(mw)
    dlg.setWindowTitle("NBOME Pearl Injector")
    dlg.setMinimumWidth(500)
    dlg.setMinimumHeight(320)

    intro = QLabel(
        "Pick the AnKing track that matches your card tags (same deck/version as in "
        "UWorld Batch Unsuspend). Only notes under that tag path are included."
    )
    intro.setWordWrap(True)

    track = QComboBox(dlg)
    for key, label in _INJECT_TRACK_CHOICES:
        track.addItem(label, key)
    cur = merged["anking_uworld_tag_mode"]
    ix = track.findData(cur)
    if ix < 0:
        ix = track.findData("step2_v12")
    track.setCurrentIndex(max(0, ix))

    ids_box = QPlainTextEdit(dlg)
    ids_box.setPlaceholderText("UWorld IDs — comma or line separated")

    form = QFormLayout()
    form.addRow("Deck / version:", track)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    qconnect(buttons.rejected, dlg.reject)

    payload: dict[str, Any] = {}

    def _on_ok() -> None:
        uw_ids = _parse_uworld_ids(ids_box.toPlainText())
        if not uw_ids:
            showWarning("Enter at least one UWorld question ID.")
            return
        mode = str(track.currentData())
        payload["ids"] = uw_ids
        payload["mode"] = mode
        new_c = dict(_addon_config())
        new_c["anking_uworld_tag_mode"] = mode
        mw.addonManager.writeConfig(__name__, new_c)
        dlg.accept()

    qconnect(buttons.accepted, _on_ok)

    root = QVBoxLayout(dlg)
    root.addWidget(intro)
    root.addLayout(form)
    root.addWidget(QLabel("UWorld question IDs:"))
    root.addWidget(ids_box)
    root.addWidget(buttons)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    return payload["ids"], str(payload["mode"])


def _field_text(note: Any, *names: str) -> str:
    for name in names:
        try:
            val = note[name]
        except (KeyError, TypeError):
            continue
        if val is None:
            continue
        s = str(val).strip()
        if s:
            return s
    return ""


def _call_gemini(
    api_key: str, front: str, back: str, *, comlex_level: int
) -> str:
    if comlex_level == 1:
        nuances = (
            "Provide 1-2 highly tested NBOME nuances appropriate for COMLEX Level 1 "
            "(foundational integration, OMM principles, viscerosomatic/Chapman-style facts where relevant).\n"
        )
    else:
        nuances = (
            "Provide 1-2 highly tested NBOME nuances appropriate for COMLEX Level 2 "
            "(e.g., viscerosomatic levels, Chapman points, classic OMM next best steps).\n"
        )
    prompt = (
        f"Act as an expert COMLEX Level {comlex_level} tutor.\n"
        "Read the following medical flashcard.\n"
        f"{nuances}"
        "Output ONLY the raw text to be added to the flashcard. "
        "Do not include formatting, introductions, or pleasantries. "
        "Make it concise and high-yield.\n\n"
        f"Flashcard Front: {front}\n"
        f"Flashcard Back: {back}\n"
    )
    url = f"{_GEMINI_URL}?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}],
            }
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", err_body)
        except json.JSONDecodeError:
            msg = err_body or f"HTTP {e.code}"
        raise RuntimeError(_sanitize_user_detail(str(msg))) from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        raise RuntimeError(_sanitize_user_detail(str(reason))) from e
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "The API returned a response that could not be read. Please try again."
        ) from e

    if "error" in body:
        err = body["error"]
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(_sanitize_user_detail(str(msg)))

    candidates = body.get("candidates") or []
    if not candidates:
        raise RuntimeError(
            "The model returned no text (the response may have been blocked). "
            "Try again or shorten the card content."
        )

    parts_out = candidates[0].get("content", {}).get("parts") or []
    texts: list[str] = []
    for part in parts_out:
        t = part.get("text")
        if t:
            texts.append(t)
    out = "".join(texts).strip()
    if not out:
        raise RuntimeError("The model returned an empty answer. Please try again.")
    return out


def _inject_nbome_pearls() -> None:
    try:
        _inject_nbome_pearls_impl()
    except Exception:
        try:
            mw.progress.finish()
        except Exception:
            pass
        showWarning(
            "NBOME Pearl Injector ran into an unexpected problem.\n\n"
            "Please restart Anki and try again. If it keeps happening, "
            "report the issue with your Anki version and add-on version."
        )


def _inject_nbome_pearls_impl() -> None:
    if mw.col is None:
        showWarning(
            "Please open a collection before using NBOME Pearl Injector."
        )
        return

    cfg = _addon_config()
    api_key = (cfg.get("api_key") or "").strip()
    if not api_key or api_key == _PLACEHOLDER_API_KEY:
        showWarning(
            "Add your own Gemini API key first.\n\n"
            "Tools → Add-ons → NBOME Pearl Injector → Config → paste your key.\n\n"
            "Get a free key at Google AI Studio. Your key stays on your computer; "
            "the author does not provide or pay for API usage."
        )
        return

    target_field = (cfg.get("target_field") or "Extra").strip() or "Extra"

    inject = _show_inject_dialog()
    if inject is None:
        return
    uw_ids, tag_mode = inject
    cfg = _addon_config()
    custom_prefix = (cfg.get("custom_uworld_tag_prefix") or "").strip()

    if tag_mode == "custom" and not custom_prefix:
        showWarning(
            "Custom tag prefix is empty.\n\n"
            "Open Add-on Config and set “Custom UWorld tag prefix” "
            "(everything before the numeric ID, e.g. #AK_Step2_v12::#UWorld::Step::), "
            "or choose Step_1 / Step_2 and v11 / v12 above."
        )
        return

    comlex_level = _comlex_level_from_track(tag_mode, custom_prefix)

    tasks: list[tuple[int, str]] = []
    seen: set[int] = set()
    for uw_id in uw_ids:
        try:
            q = _build_uworld_search_query(uw_id, tag_mode, custom_prefix)
            nids = mw.col.find_notes(q)
        except Exception:
            showWarning(
                f"Anki could not search your collection for UWorld ID “{uw_id}”.\n\n"
                "Make sure a deck is open and try again."
            )
            return
        for nid in nids:
            if nid not in seen:
                seen.add(nid)
                tasks.append((nid, uw_id))

    if not tasks:
        showInfo(
            "No matching notes were found for the selected deck/version and those IDs.\n\n"
            "Try another track in the dropdown, use Legacy mode if your tags differ, "
            "or set a Custom prefix in Add-on Config to match your hierarchy "
            "(Browse → copy a full tag from one card)."
        )
        return

    today, count_before = _usage_state_for_today()
    enforce_limit, daily_cap = _daily_limit_settings(cfg)

    if enforce_limit and daily_cap >= 1:
        remaining = daily_cap - count_before
        if remaining <= 0:
            showWarning(
                f"You have reached today’s local safety cap ({daily_cap} successful "
                f"Gemini calls tracked by this add-on).\n\n"
                "It resets at midnight on this computer’s local date, or you can change "
                "Add-on Config: set `limit_daily_gemini_requests` to false if you accept "
                "possible Google charges, or raise `daily_gemini_request_cap`.\n\n"
                "Google’s real free tier and billing are shown only in Google AI Studio—"
                "this add-on cannot read your remaining Google quota."
            )
            return
        if remaining < len(tasks):
            original_n = len(tasks)
            tasks = tasks[:remaining]
            showInfo(
                f"Daily safety cap: you have {remaining} Gemini call(s) left today "
                f"({count_before} of {daily_cap} already used by this add-on).\n\n"
                f"This batch had {original_n} note(s); only the first {remaining} will be processed.\n\n"
                "To process more today, raise `daily_gemini_request_cap` or set "
                "`limit_daily_gemini_requests` to false (see README)."
            )

    mw.progress.start(
        max=len(tasks),
        min=0,
        label="Injecting NBOME pearls…",
        parent=mw,
        immediate=True,
    )
    updated = 0
    errors: list[str] = []
    try:
        for i, (nid, uw_id) in enumerate(tasks):
            mw.progress.update(
                value=i + 1,
                label=f"NBOME pearls ({i + 1}/{len(tasks)}) — UW {uw_id}",
            )
            QApplication.processEvents()
            try:
                note = mw.col.get_note(nid)
            except Exception:
                errors.append(
                    f"UWorld {uw_id}: could not open a matching note (internal error). Skipped."
                )
                continue

            try:
                note[target_field]
            except Exception:
                errors.append(
                    f"UWorld {uw_id}: this note has no “{target_field}” field. "
                    f"Set “target_field” in Add-on Config or fix the note type. Skipped."
                )
                continue

            front = _field_text(note, "Text", "Front")
            back = _field_text(note, "Back Extra", "Back")
            if not (front or back):
                errors.append(
                    f"UWorld {uw_id}: no Text/Front or Back Extra/Back content found. Skipped."
                )
                continue

            try:
                pearl = _call_gemini(
                    api_key, front, back, comlex_level=comlex_level
                )
            except Exception as exc:
                errors.append(f"UWorld {uw_id}: {_friendly_api_one_line(exc)}")
                continue

            safe_pearl = html.escape(pearl, quote=False).replace("\n", "<br>")
            suffix = (
                "<br><br><b style='color:#007BFF;'>NBOME Pearl:</b><br>"
                f"{safe_pearl}"
            )
            current = note[target_field] or ""
            note[target_field] = current + suffix
            try:
                mw.col.update_note(note)
            except Exception:
                errors.append(
                    f"UWorld {uw_id}: could not save changes to this note. Skipped."
                )
                continue
            updated += 1
    finally:
        mw.progress.finish()

    if updated > 0:
        _persist_usage(today, count_before + updated)

    footer_usage = _usage_footer(
        enforce_limit=enforce_limit,
        cap=daily_cap,
        count_before=count_before,
        updated_this_run=updated,
    )

    if errors:
        preview = "\n".join(errors[:6])
        extra = f"\n\n… and {len(errors) - 6} more issue(s)." if len(errors) > 6 else ""
        api_hint = ""
        if any("Gemini" in line for line in errors):
            api_hint = (
                "\n\nIf you see Gemini or network messages, confirm your API key under "
                "Tools → Add-ons → Config, and check quota and billing in Google AI Studio."
            )
        if updated == 0:
            showWarning(
                "No notes were updated.\n\n"
                f"{preview}{extra}"
                f"{api_hint}"
                f"{footer_usage}"
            )
        else:
            showWarning(
                f"Finished with {updated} note(s) updated. "
                f"Some items were skipped ({len(errors)}).\n\n"
                f"{preview}{extra}"
                f"{api_hint}"
                f"{footer_usage}"
            )
        return

    showInfo(
        f"Success: injected NBOME pearls into the “{target_field}” field "
        f"for {updated} note(s)."
        f"{footer_usage}"
        + _SUCCESS_ATTRIBUTION
    )


def _on_main_window_init() -> None:
    mw.addonManager.setConfigAction(__name__, _show_config_dialog)
    action = QAction("Inject NBOME Pearls (UWorld IDs)", mw)
    qconnect(action.triggered, _inject_nbome_pearls)
    mw.form.menuTools.addAction(action)


gui_hooks.main_window_did_init.append(_on_main_window_init)
