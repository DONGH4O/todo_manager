"""QtWebEngine rendering configuration tests."""

from __future__ import annotations

import os

from todo_manager.gui import react_shell


def test_qtwebengine_direct_composition_flags_are_merged_without_duplicates():
    merged = react_shell._merge_chromium_flags(
        "--enable-logging --disable-direct-composition",
        react_shell.DIRECT_COMPOSITION_FLAGS,
    )

    assert merged.split() == [
        "--enable-logging",
        "--disable-direct-composition",
        "--disable-direct-composition-video-overlays",
    ]


def test_qtwebengine_rendering_mode_maps_to_direct_composition_flags():
    assert (
        react_shell._qtwebengine_flags_for_rendering_mode("dcomp")
        == react_shell.DIRECT_COMPOSITION_FLAGS
    )
    assert react_shell._qtwebengine_flags_for_rendering_mode("hardware") == ()
    assert react_shell._qtwebengine_flags_for_rendering_mode("unknown") is None


def test_qtwebengine_rendering_configuration_updates_chromium_flags(monkeypatch):
    monkeypatch.delenv(react_shell.QTWEBENGINE_CHROMIUM_FLAGS_ENV, raising=False)
    monkeypatch.setenv(react_shell.QTWEBENGINE_RENDERING_ENV, "direct-composition")

    react_shell._configure_qtwebengine_rendering()

    assert os.environ[react_shell.QTWEBENGINE_CHROMIUM_FLAGS_ENV].split() == list(
        react_shell.DIRECT_COMPOSITION_FLAGS
    )
