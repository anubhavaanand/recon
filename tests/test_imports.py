import importlib

import pytest

PROJECT_PACKAGES = ["cli", "tui", "core", "clients", "storage"]
CORE_DEPENDENCIES = ["textual", "httpx", "Pillow", "rapidfuzz", "typer", "fpdf2"]


def test_core_modules_importable():
    for pkg in PROJECT_PACKAGES:
        module = importlib.import_module(pkg)
        assert module is not None


def test_submodules_importable():
    submodules = [
        "core.models",
        "core.search",
        "core.scoring",
        "core.config",
        "core.arbitrage",
        "core.intelligence",
        "core.translation",
        "clients.base",
        "clients.patent_apis",
        "clients.intelligence",
        "storage.cache",
        "cli.main",
        "cli.export",
        "cli.download",
        "tui.app",
        "tui.screens",
        "tui.widgets.result_list",
        "tui.widgets.info_tab",
        "tui.widgets.claims_tab",
        "tui.widgets.image_tab",
    ]
    for mod in submodules:
        m = importlib.import_module(mod)
        assert m is not None


def test_search_patents_import():
    from core.search import search_all, sort_and_merge_results
    assert callable(search_all)
    assert callable(sort_and_merge_results)


def test_circular_dependencies():
    for mod_name in [
        "core.models",
        "core.search",
        "core.scoring",
        "core.config",
        "clients.base",
        "clients.patent_apis",
        "clients.intelligence",
        "storage.cache",
        "tui.app",
        "tui.screens",
        "tui.widgets.result_list",
        "tui.widgets.info_tab",
        "tui.widgets.claims_tab",
        "tui.widgets.image_tab",
    ]:
        importlib.import_module(mod_name)


DEP_IMPORT_MAP = {
    "Pillow": "PIL",
    "fpdf2": "fpdf",
}

def test_external_dependencies_available():
    for dep in CORE_DEPENDENCIES:
        mod_name = DEP_IMPORT_MAP.get(dep, dep.replace("-", "_"))
        try:
            importlib.import_module(mod_name)
        except ModuleNotFoundError:
            try:
                importlib.import_module(dep)
            except ModuleNotFoundError:
                pytest.fail(f"Required dependency '{dep}' not installed")


def test_optional_dependencies_graceful():
    try:
        import httpx  # noqa: F401

        from core.intelligence import SynthesisEngine
        assert callable(SynthesisEngine)
    except ImportError:
        pass
    try:
        from tui.widgets.image_tab import detect_terminal_protocol
        assert callable(detect_terminal_protocol)
    except ImportError:
        pass
