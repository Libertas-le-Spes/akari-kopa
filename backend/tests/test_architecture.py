import ast
import unittest
from pathlib import Path

PACKAGE = Path(__file__).parent.parent / "akari_kopa"

MAY_IMPORT = {
    "attention": {"attention"},
    "use_cases": {"attention", "use_cases"},
    "presenters": {"attention", "use_cases", "presenters"},
    "adapters": {"attention", "use_cases", "adapters"},
    "entrypoints": {"attention", "use_cases", "presenters", "entrypoints", "wiring"},
    "wiring": {"attention", "use_cases", "adapters", "wiring"},
}

STANDARD_LIBRARY_ONLY_OUTSIDE = {"subprocess", "urllib", "http", "socket", "os", "shutil", "threading", "pathlib", "json", "gi"}


def ring_of(module: str) -> str:
    return module.split(".")[1]


def imports_of(path: Path) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
        if isinstance(node, ast.Import):
            found += [(node.lineno, alias.name) for alias in node.names]
    return found


def modules() -> list[tuple[Path, str]]:
    found = [(path, ".".join(path.relative_to(PACKAGE.parent).with_suffix("").parts)) for path in sorted(PACKAGE.rglob("*.py"))]
    return [(path, module) for path, module in found if module.count(".") > 0 and not module.endswith(("__main__", "__init__"))]


class DependenciesPointInward(unittest.TestCase):
    def test_no_ring_imports_a_ring_outside_it(self):
        breaches = [
            f"{path.relative_to(PACKAGE.parent)}:{line} ({ring_of(module)}) imports {imported}"
            for path, module in modules()
            for line, imported in imports_of(path)
            if imported.startswith("akari_kopa.") and ring_of(imported) not in MAY_IMPORT[ring_of(module)]
        ]
        self.assertEqual(breaches, [])

    def test_the_rules_reach_nothing_outside_the_program(self):
        reaching = [
            f"{path.relative_to(PACKAGE.parent)}:{line} imports {imported}"
            for path, module in modules() if ring_of(module) == "attention"
            for line, imported in imports_of(path)
            if imported.split(".")[0] in STANDARD_LIBRARY_ONLY_OUTSIDE
        ]
        self.assertEqual(reaching, [])


if __name__ == "__main__":
    unittest.main()
