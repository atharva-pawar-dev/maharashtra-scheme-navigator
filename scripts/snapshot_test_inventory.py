"""Test inventory snapshot using Python AST (Protocol C7 / Gate G23)."""

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
OUTPUT_FILE = REPO_ROOT / "release" / "evidence" / "baseline" / "test_inventory.json"


class TestVisitor(ast.NodeVisitor):
    def __init__(self):
        self.tests = []
        self.current_test = None
        self.assert_count = 0
        self.skips = []
        self.xfails = []
        self.mocks = []
        self.monkeypatches = []

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_") or any(
            (isinstance(d, ast.Name) and d.id == "test") for d in node.decorator_list
        ):
            prev_test = self.current_test
            self.current_test = node.name
            self.assert_count = 0
            
            # Check decorators for skip/xfail
            for dec in node.decorator_list:
                dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                if "skip" in dec_str:
                    self.skips.append({"test": node.name, "decorator": dec_str, "line": node.lineno})
                if "xfail" in dec_str:
                    self.xfails.append({"test": node.name, "decorator": dec_str, "line": node.lineno})

            self.generic_visit(node)
            self.tests.append({
                "name": node.name,
                "line": node.lineno,
                "assert_count": self.assert_count
            })
            self.current_test = prev_test
        else:
            self.generic_visit(node)

    def visit_Assert(self, node):
        if self.current_test:
            self.assert_count += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        call_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
        if "monkeypatch" in call_str:
            self.monkeypatches.append({"line": node.lineno, "call": call_str[:100]})
        if "mock" in call_str.lower() or "patch" in call_str.lower():
            self.mocks.append({"line": node.lineno, "call": call_str[:100]})
        if "pytest.skip" in call_str:
            self.skips.append({"line": node.lineno, "call": call_str[:100]})
        if "pytest.xfail" in call_str:
            self.xfails.append({"line": node.lineno, "call": call_str[:100]})
        self.generic_visit(node)


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    inventory = {
        "files": {},
        "summary": {
            "total_files": 0,
            "total_tests": 0,
            "total_asserts": 0,
            "total_skips": 0,
            "total_xfails": 0,
            "total_mocks": 0,
            "total_monkeypatches": 0,
        }
    }

    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    for tf in test_files:
        content = tf.read_text(encoding="utf-8")
        try:
            tree = ast.parse(content, filename=str(tf))
            visitor = TestVisitor()
            visitor.visit(tree)

            file_asserts = sum(t["assert_count"] for t in visitor.tests)
            inventory["files"][tf.name] = {
                "test_count": len(visitor.tests),
                "assert_count": file_asserts,
                "tests": visitor.tests,
                "skips": visitor.skips,
                "xfails": visitor.xfails,
                "mocks_count": len(visitor.mocks),
                "monkeypatch_count": len(visitor.monkeypatches),
            }

            inventory["summary"]["total_files"] += 1
            inventory["summary"]["total_tests"] += len(visitor.tests)
            inventory["summary"]["total_asserts"] += file_asserts
            inventory["summary"]["total_skips"] += len(visitor.skips)
            inventory["summary"]["total_xfails"] += len(visitor.xfails)
            inventory["summary"]["total_mocks"] += len(visitor.mocks)
            inventory["summary"]["total_monkeypatches"] += len(visitor.monkeypatches)
        except Exception as e:
            inventory["files"][tf.name] = {"error": str(e)}

    OUTPUT_FILE.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"Test inventory snapshot saved to {OUTPUT_FILE}")
    print(f"Summary: {inventory['summary']}")


if __name__ == "__main__":
    main()
