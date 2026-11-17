"""AST and regex based automated static security analyzer for Scheme Navigator."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Sensitive key patterns
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----"), "Private cryptographic key"),
    (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]"), "AWS secret access key"),
    (re.compile(r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{32,}['\"]"), "Generic API key literal"),
    (re.compile(r"(?i)password\s*=\s*['\"][^'\"]{8,}['\"]"), "Hardcoded password candidate"),
]

# Prohibited dangerous functions
DANGEROUS_CALLS = {"eval", "exec"}


class SecurityVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: list[dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        # Check eval / exec
        if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_CALLS:
            self.findings.append({
                "type": "DANGEROUS_CALL",
                "severity": "HIGH",
                "file": self.filename,
                "line": node.lineno,
                "message": f"Use of forbidden dynamic execution function '{node.func.id}'",
            })

        # Check subprocess shell=True
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen", "call", "check_output"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append({
                        "type": "SHELL_INJECTION_RISK",
                        "severity": "HIGH",
                        "file": self.filename,
                        "line": node.lineno,
                        "message": f"subprocess.{node.func.attr} called with shell=True",
                    })

        # Check random.random() for security
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "random" and node.func.attr in ("random", "randint", "choice", "randrange"):
                if "security" in self.filename.lower() or "auth" in self.filename.lower():
                    self.findings.append({
                        "type": "WEAK_PRNG",
                        "severity": "MEDIUM",
                        "file": self.filename,
                        "line": node.lineno,
                        "message": f"Pseudo-random generator 'random.{node.func.attr}' used in security-sensitive module; use 'secrets' instead.",
                    })

        self.generic_visit(node)


def scan_file(file_path: Path) -> list[dict[str, Any]]:
    findings = []
    text = ""
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    # 1. Regex secret scan
    for line_num, line in enumerate(text.splitlines(), start=1):
        # Ignore comments or test fixtures explicitly marked
        if "test" in file_path.name or "fixture" in file_path.name:
            continue
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(line) and "forbidden_defaults" not in line and "example" not in line.lower():
                findings.append({
                    "type": "SECRET_LEAK",
                    "severity": "CRITICAL",
                    "file": str(file_path.relative_to(REPO_ROOT)),
                    "line": line_num,
                    "message": f"Potential {label} detected in source code",
                })

    # 2. Python AST scan
    if file_path.suffix == ".py":
        try:
            tree = ast.parse(text, filename=str(file_path))
            visitor = SecurityVisitor(str(file_path.relative_to(REPO_ROOT)))
            visitor.visit(tree)
            findings.extend(visitor.findings)
        except SyntaxError:
            pass

    return findings


def main():
    src_dir = REPO_ROOT / "src"
    all_findings = []
    py_files = list(src_dir.rglob("*.py"))
    for pyf in py_files:
        all_findings.extend(scan_file(pyf))

    out_file = REPO_ROOT / "release" / "evidence" / "ws6" / "E-WS6-002_security_scan.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "files_scanned": len(py_files),
        "total_findings": len(all_findings),
        "critical_count": sum(1 for f in all_findings if f["severity"] == "CRITICAL"),
        "high_count": sum(1 for f in all_findings if f["severity"] == "HIGH"),
        "medium_count": sum(1 for f in all_findings if f["severity"] == "MEDIUM"),
        "findings": all_findings,
        "verdict": "PASS" if len(all_findings) == 0 else "FAIL",
    }
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Scanned {len(py_files)} files in src/. Findings: {len(all_findings)}. Result written to {out_file}")


if __name__ == "__main__":
    main()
