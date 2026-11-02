import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOMAIN_MODULES = ("catalog.py", "policies.py", "tools.py")
API_MODULE = "api.py"
BLOCKED_IMPORTS = (
    "import sys; sys.modules['fastapi'] = None; sys.modules['anthropic'] = None; "
    "import emporio_agent.catalog, emporio_agent.policies, emporio_agent.tools"
)
FORBIDDEN_IMPORT_PATTERN = re.compile(r"^(import|from) (fastapi|anthropic)\b", re.MULTILINE)
FASTAPI_IMPORT_PATTERN = re.compile(r"^(import|from) fastapi\b", re.MULTILINE)
AGENT_IMPORT_PATTERN = re.compile(r"^(import|from) emporio_agent\.agent\b", re.MULTILINE)


def test_domain_modules_import_without_fastapi_or_anthropic() -> None:
    completed = subprocess.run(
        [sys.executable, "-c", BLOCKED_IMPORTS],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_domain_sources_have_no_fastapi_or_anthropic_import_lines() -> None:
    for module_name in DOMAIN_MODULES:
        source = (REPO_ROOT / "emporio_agent" / module_name).read_text(encoding="utf-8")
        assert FORBIDDEN_IMPORT_PATTERN.search(source) is None, module_name


def test_tools_module_does_not_import_agent() -> None:
    source = (REPO_ROOT / "emporio_agent" / "tools.py").read_text(encoding="utf-8")
    assert AGENT_IMPORT_PATTERN.search(source) is None


def test_only_api_module_imports_fastapi() -> None:
    modules_importing_fastapi = [
        module_path.name
        for module_path in sorted((REPO_ROOT / "emporio_agent").glob("*.py"))
        if FASTAPI_IMPORT_PATTERN.search(module_path.read_text(encoding="utf-8")) is not None
    ]
    assert modules_importing_fastapi == [API_MODULE]
