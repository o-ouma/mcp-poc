import sys
import traceback
from typing import Any, Dict
import ast
import glob
import pathlib

def register_testgen_tools(mcp):
    """
    Register MCP tool for test generation
    """
    @mcp.tool()
    async def generate_tests() -> Dict[str, Any]:
        """Scan the repo for Python files and generate unittest stubs for each function/class in tests/ directory."""
        try:
            repo_root = pathlib.Path(__file__).parent.parent.resolve()
            tests_dir = repo_root / 'tests'
            tests_dir.mkdir(exist_ok=True)
            py_files = [
                f for f in glob.glob(str(repo_root / '**' / '*.py'), recursive=True)
                if not (str(f).startswith(str(tests_dir)) or '/venv/' in f or '/__pycache__/' in f or f.endswith('pr_analyzer.py'))
            ]
            results = []
            for py_file in py_files:
                rel_path = pathlib.Path(py_file).relative_to(repo_root)
                module_name = rel_path.stem
                test_file = tests_dir / f'test_{module_name}.py'
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                try:
                    tree = ast.parse(source)
                except Exception as e:
                    results.append({"file": str(rel_path), "error": f"Parse error: {e}"})
                    continue
                test_lines = [
                    'import unittest',
                    f'import {module_name}',
                    '',
                ]
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef):
                        test_lines.append(f'class Test{node.name.capitalize()}(unittest.TestCase):')
                        test_lines.append(f'    def test_{node.name}(self):')
                        test_lines.append(f'        # TODO: implement test for {node.name}')
                        test_lines.append(f'        self.assertTrue(True)')
                        test_lines.append('')
                    elif isinstance(node, ast.ClassDef):
                        test_lines.append(f'class Test{node.name}(unittest.TestCase):')
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and not item.name.startswith('__'):
                                test_lines.append(f'    def test_{item.name}(self):')
                                test_lines.append(f'        # TODO: implement test for {node.name}.{item.name}')
                                test_lines.append(f'        self.assertTrue(True)')
                                test_lines.append('')
                if len(test_lines) > 3:
                    with open(test_file, 'w', encoding='utf-8') as tf:
                        tf.write('\n'.join(test_lines))
                    results.append({"file": str(test_file.relative_to(repo_root)), "status": "created"})
                else:
                    results.append({"file": str(rel_path), "status": "no functions/classes found"})
            return {"status": "success", "results": results}
        except Exception as e:
            print(f"Error generating tests: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"status": "error", "error": str(e)} 