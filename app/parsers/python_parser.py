import ast
import os
from typing import List, Dict
from pathlib import Path

class PythonParser:

    def __init__(self):
        self.skip_dirs = {
            '.git', 'venv','myenv', 'env', '__pycache__', 
            'node_modules', 'build', 'dist', '.venv', 
            '.idea', '.vscode'
        }
        self.skip_files = {'__init__.py'}

    def parse_file(self, file_path:str) -> List[Dict]:
        try:
            with open(file_path, 'r',encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=file_path)
            elements = []

            elements.append({
                "name": os.path.basename(file_path),
                "type": "module",
                "code_snippet": source_code[:600],
                "docstring": ast.get_docstring(tree) or "",
                "line_start": 1,
                "line_end": len(source_code.splitlines()),
                "file_path": file_path,
                "metadata": {
                    "language": "python",
                    "file_size": len(source_code)
                }
            })

            visitor = CodeElementVisitor(file_path, source_code)
            visitor.visit(tree)
            elements.extend(visitor.elements)

            return elements

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def parse_directory(self, repo_path: str) -> List[Dict]:
        all_elements = []
        repo_path = Path(repo_path)

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for file in files:
                if file.endswith('.py') and file not in self.skip_files:
                    file_path = os.path.join(root, file)
                    elements = self.parse_file(file_path)
                    all_elements.extend(elements)

        return all_elements


class CodeElementVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.elements = []

    def visit_FunctionDef(self, node):
        self._extract_function(node, "function")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._extract_function(node, "async_function")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._extract_class(node)
        self.generic_visit(node)

    def _extract_function(self, node: ast.AST, node_type: str):
        try:
            code_snippet = ast.get_source_segment(self.source_code, node) or ""
            docstring = ast.get_docstring(node) or ""

            self.elements.append({
                "name": node.name,
                "type": node_type,
                "code_snippet": code_snippet,
                "docstring": docstring,
                "line_start": node.lineno,
                "line_end": getattr(node, 'end_lineno', node.lineno),
                "file_path": self.file_path,
                "metadata": {
                    # "args": [arg.arg for arg in node.args.args],
                    "args": ", ".join(arg.arg for arg in node.args.args),
                    "language": "python"
                }
            })
        except:
            pass

    def _extract_class(self, node: ast.ClassDef):
        try:
            code_snippet = ast.get_source_segment(self.source_code, node) or ""
            docstring = ast.get_docstring(node) or ""

            self.elements.append({
                "name": node.name,
                "type": "class",
                "code_snippet": code_snippet,
                "docstring": docstring,
                "line_start": node.lineno,
                "line_end": getattr(node, 'end_lineno', node.lineno),
                "file_path": self.file_path,
                "metadata": {
                    # "bases": [ast.unparse(base) for base in node.bases],
                    "bases": ", ".join(ast.unparse(base) for base in node.bases),
                    "language": "python"
                }
            })
        except:
            pass