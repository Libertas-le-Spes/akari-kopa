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

REACHING_OUTSIDE = {"subprocess", "urllib.request", "urllib.error", "http", "socket", "os", "shutil", "threading", "pathlib", "json", "gi"}


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


def reaches_outside(imported: str) -> bool:
    for module in REACHING_OUTSIDE:
        if imported == module or imported.startswith(module + "."):
            return True
    return False


def modules() -> list[tuple[Path, str]]:
    found = [(path, ".".join(path.relative_to(PACKAGE.parent).with_suffix("").parts)) for path in sorted(PACKAGE.rglob("*.py"))]
    inside = []
    for path, module in found:
        if module.count(".") > 0 and not module.endswith(("__main__", "__init__")):
            inside.append((path, module))
    return inside


class DependenciesPointInward(unittest.TestCase):
    def test_no_ring_imports_a_ring_outside_it(self):
        breaches = []
        for path, module, line, imported in every_import():
            if imported.startswith("akari_kopa.") and ring_of(imported) not in MAY_IMPORT[ring_of(module)]:
                breaches.append(f"{path.relative_to(PACKAGE.parent)}:{line} ({ring_of(module)}) imports {imported}")
        self.assertEqual(breaches, [])

    def test_the_rules_reach_nothing_outside_the_program(self):
        reaching = []
        for path, module, line, imported in every_import():
            if ring_of(module) == "attention" and reaches_outside(imported):
                reaching.append(f"{path.relative_to(PACKAGE.parent)}:{line} imports {imported}")
        self.assertEqual(reaching, [])


def every_import() -> list[tuple[Path, str, int, str]]:
    found = []
    for path, module in modules():
        for line, imported in imports_of(path):
            found.append((path, module, line, imported))
    return found


if __name__ == "__main__":
    unittest.main()
