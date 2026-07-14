import ast
import os
from typing import Dict, Any, List, Optional


class DependencyVisitor(ast.NodeVisitor):

    def __init__(self):
        self.imports = []
        self.classes = []
        self.calls = []
        self._current_class = None
        self._current_function = None


    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append({
                "type": "import",
                "module": alias.name,
                "imported_name": None,
                "alias": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)


    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "type": "import_from",
                "module": module,
                "imported_name": alias.name,
                "alias": alias.asname,
                "level": node.level or 0,
                "line": node.lineno
            })
        self.generic_visit(node)


    def visit_ClassDef(self, node: ast.ClassDef):
        bases = []
        for base in node.bases:
            try:
                base_str = ast.unparse(base)
                bases.append(base_str)
            except Exception:
                pass
        
        self.classes.append({
            "name": node.name,
            "bases": bases,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })
        
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class


    def visit_FunctionDef(self, node: ast.FunctionDef):
        old_func = self._current_function
        func_name = f"{self._current_class}.{node.name}" if self._current_class else node.name
        self._current_function = func_name
        self.generic_visit(node)
        self._current_function = old_func


    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        old_func = self._current_function
        func_name = f"{self._current_class}.{node.name}" if self._current_class else node.name
        self._current_function = func_name
        self.generic_visit(node)
        self._current_function = old_func


    def visit_Call(self, node: ast.Call):
        if self._current_function:
            called_name = None
            if isinstance(node.func, ast.Name):
                called_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called_name = node.func.attr
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
                    called_name = f"self.{node.func.attr}"
            
            if called_name:
                self.calls.append({
                    "caller": self._current_function,
                    "callee": called_name,
                    "line": node.lineno
                })
        self.generic_visit(node)


class DependencyParser:

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = os.path.abspath(repo_path) if repo_path else None
        self.skip_dirs = {
            '.git', 'venv', 'myenv', 'env', '__pycache__',
            'node_modules', 'build', 'dist', '.venv',
            '.idea', '.vscode'
        }
        self.skip_files = {'__init__.py'}


    def resolve_import(
        self,
        current_file_path: str,
        module: Optional[str],
        level: int,
        imported_name: Optional[str] = None
    ) -> Optional[str]:

        if not self.repo_path:
            return None

        current_file_abs = os.path.abspath(current_file_path)

        if level > 0:
            current_dir = os.path.dirname(current_file_abs)
            for _ in range(level - 1):
                parent_dir = os.path.dirname(current_dir)
                if len(parent_dir) < len(self.repo_path):
                    break
                current_dir = parent_dir

            if module:
                module_parts = module.split('.')
                target_path = os.path.join(current_dir, *module_parts)
                
                if os.path.exists(target_path + ".py"):
                    return os.path.abspath(target_path + ".py")
                if os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, "__init__.py")):
                    return os.path.abspath(os.path.join(target_path, "__init__.py"))

                if imported_name:
                    sub_target = os.path.join(target_path, imported_name)
                    if os.path.exists(sub_target + ".py"):
                        return os.path.abspath(sub_target + ".py")
                    if os.path.isdir(sub_target) and os.path.exists(os.path.join(sub_target, "__init__.py")):
                        return os.path.abspath(os.path.join(sub_target, "__init__.py"))

            elif imported_name:
                target_path = os.path.join(current_dir, imported_name)
                if os.path.exists(target_path + ".py"):
                    return os.path.abspath(target_path + ".py")
                if os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, "__init__.py")):
                    return os.path.abspath(os.path.join(target_path, "__init__.py"))

        else:
            if not module:
                return None
            
            module_parts = module.split('.')
            target_path = os.path.join(self.repo_path, *module_parts)
            
            if os.path.exists(target_path + ".py"):
                return os.path.abspath(target_path + ".py")
            if os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, "__init__.py")):
                return os.path.abspath(os.path.join(target_path, "__init__.py"))

            if imported_name:
                sub_target = os.path.join(target_path, imported_name)
                if os.path.exists(sub_target + ".py"):
                    return os.path.abspath(sub_target + ".py")
                if os.path.isdir(sub_target) and os.path.exists(os.path.join(sub_target, "__init__.py")):
                    return os.path.abspath(os.path.join(sub_target, "__init__.py"))

        return None


    def resolve_base_class(self, base_name: str, imports: List[Dict[str, Any]]) -> str:
        parts = base_name.split('.')
        first_part = parts[0]

        for imp in imports:
            name_to_match = imp["alias"] if imp["alias"] else imp["imported_name"]
            
            if name_to_match == first_part:
                prefix = imp["module"]
                if imp["imported_name"]:
                    if prefix:
                        prefix = f"{prefix}.{imp['imported_name']}"
                    else:
                        prefix = imp["imported_name"]
                
                remaining = parts[1:]
                if remaining:
                    return f"{prefix}.{'.'.join(remaining)}"
                else:
                    return prefix

            if imp["module"] and not imp["imported_name"] and not imp["alias"]:
                mod_parts = imp["module"].split('.')
                if parts[:len(mod_parts)] == mod_parts:
                    return base_name

        return base_name


    def parse_file(self, file_path: str) -> Dict[str, Any]:
        file_path_abs = os.path.abspath(file_path)
        
        try:
            with open(file_path_abs, 'r', encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=file_path_abs)
            visitor = DependencyVisitor()
            visitor.visit(tree)

            resolved_imports = []
            for imp in visitor.imports:
                resolved_path = self.resolve_import(
                    current_file_path=file_path_abs,
                    module=imp["module"],
                    level=imp.get("level", 0),
                    imported_name=imp["imported_name"]
                )
                
                is_local = False
                resolved_rel = None
                if resolved_path and self.repo_path:
                    is_local = resolved_path.startswith(self.repo_path)
                    resolved_rel = os.path.relpath(resolved_path, self.repo_path)

                resolved_imports.append({
                    "type": imp["type"],
                    "module": imp["module"],
                    "imported_name": imp["imported_name"],
                    "alias": imp["alias"],
                    "line": imp["line"],
                    "resolved_path": resolved_path,
                    "resolved_project_relative_path": resolved_rel,
                    "is_local": is_local
                })

            resolved_classes = []
            for cls in visitor.classes:
                resolved_bases = [
                    self.resolve_base_class(base, resolved_imports)
                    for base in cls["bases"]
                ]
                resolved_classes.append({
                    "name": cls["name"],
                    "bases": cls["bases"],
                    "resolved_bases": resolved_bases,
                    "line": cls["line"],
                    "end_line": cls["end_line"]
                })

            file_rel = os.path.relpath(file_path_abs, self.repo_path) if self.repo_path else None

            return {
                "file_path": file_path_abs,
                "project_relative_path": file_rel,
                "imports": resolved_imports,
                "classes": resolved_classes,
                "calls": visitor.calls
            }

        except Exception as e:
            print(f"Error parsing file {file_path_abs}: {e}")
            return {
                "file_path": file_path_abs,
                "project_relative_path": os.path.relpath(file_path_abs, self.repo_path) if self.repo_path and os.path.isabs(file_path_abs) else None,
                "imports": [],
                "classes": [],
                "calls": [],
                "error": str(e)
            }


    def parse_directory(self, repo_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:

        if repo_path:
            self.repo_path = os.path.abspath(repo_path)
            
        if not self.repo_path:
            raise ValueError("Repository path (repo_path) must be set to parse a directory.")

        results = {}
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for file in files:
                if file.endswith('.py') and file not in self.skip_files:
                    file_path = os.path.join(root, file)
                    parse_result = self.parse_file(file_path)
                    
                    key = parse_result["project_relative_path"] or file_path
                    results[key] = parse_result

        return results