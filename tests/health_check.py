#!/usr/bin/env python3
"""RECON Health Check - standalone project status verification.

Usage:
    python tests/health_check.py                    # Human-readable
    python tests/health_check.py --format=json      # JSON
    python tests/health_check.py --format=critical  # Critical issues only

Exit codes:
    0 (healthy), 1 (warnings), 2 (critical)
"""

import argparse
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_PACKAGES = ["cli", "tui", "core", "clients", "storage"]
CRITICAL_MODULES = [
    "core.models",
    "core.search",
    "core.scoring",
    "core.config",
    "clients.base",
    "clients.patent_apis",
    "storage.cache",
    "tui.app",
    "tui.screens",
]


def check_imports() -> dict:
    issues = []
    for pkg in PROJECT_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError as e:
            issues.append({"module": pkg, "error": str(e)})
    for mod in CRITICAL_MODULES:
        try:
            importlib.import_module(mod)
        except ImportError as e:
            issues.append({"module": mod, "error": str(e)})
    return {
        "status": "PASS" if not issues else "FAIL",
        "total_checked": len(PROJECT_PACKAGES) + len(CRITICAL_MODULES),
        "issues": issues,
    }


DEP_IMPORT_MAP = {
    "Pillow": "PIL",
    "fpdf2": "fpdf",
}

def check_dependencies() -> dict:
    required = ["textual", "httpx", "Pillow", "rapidfuzz", "typer", "fpdf2"]
    missing = []
    for dep in required:
        mod_name = DEP_IMPORT_MAP.get(dep, dep.replace("-", "_"))
        try:
            importlib.import_module(mod_name)
        except ModuleNotFoundError:
            try:
                importlib.import_module(dep)
            except ModuleNotFoundError:
                missing.append(dep)
    return {
        "status": "PASS" if not missing else "FAIL",
        "missing": missing,
    }


def run_tests() -> dict:
    tests_dir = Path(__file__).parent
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "--tb=short", "-q"],
        capture_output=True, text=True, timeout=120,
    )
    stdout = result.stdout
    stderr = result.stderr
    passed = failed = skipped = 0
    for line in stdout.splitlines():
        if "passed" in line and "failed" in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if p == "passed":
                    passed = int(parts[i - 1])
                elif p == "failed":
                    failed = int(parts[i - 1])
                elif p == "skipped":
                    skipped = int(parts[i - 1])
        elif "passed" in line and "=" in line:
            pass
    if failed == 0 and "failed" in stdout:
        for line in stdout.splitlines():
            if "failed" in line:
                for i, p in enumerate(line.split()):
                    if p == "failed":
                        failed = int(line.split()[i - 1])
    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "output": stdout.strip().splitlines()[-3:] if stdout else [],
    }


def get_coverage() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--cov=cli,tui,core,clients,storage",
         "--cov-report=term-missing", "-q", str(Path(__file__).parent)],
        capture_output=True, text=True, timeout=120,
    )
    coverage_pct = None
    for line in result.stdout.splitlines():
        if "TOTAL" in line:
            parts = line.rsplit(None, 1)
            if parts:
                try:
                    coverage_pct = float(parts[-1].rstrip("%"))
                except ValueError:
                    pass
    return {
        "coverage_pct": coverage_pct,
        "output": result.stdout.strip().splitlines()[-5:] if result.stdout else [],
    }


def check_config() -> dict:
    issues = []
    config_path = Path.home() / ".config" / "recon" / "config.toml"
    if not config_path.exists():
        issues.append("Config file not found at ~/.config/recon/config.toml")
    return {"status": "WARN" if issues else "PASS", "issues": issues}


def main():
    parser = argparse.ArgumentParser(description="RECON Health Check")
    parser.add_argument("--format", choices=["human", "json", "critical"],
                        default="human")
    args = parser.parse_args()

    start = time.time()
    imports = check_imports()
    deps = check_dependencies()
    tests = run_tests()
    config = check_config()

    critical_issues = []
    warnings = []
    if imports["issues"]:
        critical_issues.append(f"Import failures: {len(imports['issues'])} modules")
    if deps["missing"]:
        critical_issues.append(f"Missing dependencies: {', '.join(deps['missing'])}")
    if tests["failed"] and tests["failed"] > 0:
        critical_issues.append(f"Test failures: {tests['failed']} failed")
    if config["issues"]:
        warnings.append(f"Config: {', '.join(config['issues'])}")

    result = {
        "status": "healthy" if not critical_issues else "degraded",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_sec": round(time.time() - start, 2),
        "imports": imports,
        "dependencies": deps,
        "tests": tests,
        "config": config,
        "critical_issues": critical_issues,
        "warnings": warnings,
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "critical":
        if critical_issues:
            for issue in critical_issues:
                print(f"CRITICAL: {issue}")
        if not critical_issues and not warnings:
            print("HEALTHY: No critical issues")
        if warnings:
            for w in warnings:
                print(f"WARN: {w}")
    else:
        print("=" * 50)
        print("RECON Health Check")
        print("=" * 50)
        print(f"Status: {result['status'].upper()}")
        print(f"Duration: {result['duration_sec']}s")
        print()
        print(f"Imports: {imports['status']} ({imports['total_checked']} checked)")
        if imports["issues"]:
            for iss in imports["issues"]:
                print(f"  FAIL: {iss['module']}: {iss['error']}")
        print(f"Dependencies: {deps['status']}")
        if deps["missing"]:
            for m in deps["missing"]:
                print(f"  MISSING: {m}")
        print(f"Tests: {tests['passed']} passed, {tests['failed']} failed, "
              f"{tests['skipped']} skipped")
        if tests["output"]:
            print(f"  Last lines: {' | '.join(tests['output'])}")
        print(f"Config: {config['status']}")
        if config["issues"]:
            for iss in config["issues"]:
                print(f"  {iss}")
        print()
        if critical_issues:
            print("CRITICAL ISSUES:")
            for ci in critical_issues:
                print(f"  - {ci}")
        if warnings:
            print("WARNINGS:")
            for w in warnings:
                print(f"  - {w}")
        if not critical_issues and not warnings:
            print("No issues found.")

    sys.exit(2 if critical_issues else (1 if warnings else 0))


if __name__ == "__main__":
    main()
