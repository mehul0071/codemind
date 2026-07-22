import re
import os
import shutil
import tempfile
import subprocess
from typing import Dict, Any
from app.agents.state import AgentState
from app.config import settings


def parse_patch(patch_str: str) -> Dict[str, str]:
    pattern = re.compile(r"```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
    blocks = pattern.findall(patch_str)
    
    file_map = {}
    for block in blocks:
        block_strip = block.strip()
        lines = block_strip.splitlines()
        file_path = None
        for line in lines[:3]:
            match = re.search(r"^\s*#\s*FILE\s*:\s*([^\s#]+)", line, re.IGNORECASE)
            if match:
                file_path = match.group(1).strip()
                break
        if file_path:
            file_map[file_path] = block_strip
            
    return file_map


def copy_codebase(src_dir: str, dest_dir: str):
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "myenv", ".venv") and not d.startswith(".sandbox_")]
        
        for file in files:
            if file.endswith((".pyc", ".pyo", ".log", ".db")):
                continue
                
            src_file = os.path.join(root, file)
            rel_path = os.path.relpath(src_file, src_dir)
            dest_file = os.path.join(dest_dir, rel_path)
            
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(src_file, dest_file)


async def sandbox_agent(state: AgentState) -> Dict[str, Any]:
    lint_results = state.get("lint_results")
    if lint_results and not lint_results.get("success", True):
        return {
            "test_results": {
                "success": False,
                "output": "Skipped test execution due to previous syntax check failure."
            }
        }
        
    patch = state.get("generated_patch") or ""
    if not patch:
        return {
            "test_results": {
                "success": True,
                "output": "No generated patch found. Skipping tests."
            }
        }
        
    patch_files = parse_patch(patch)
    if not patch_files:
        pass
        
    session_id = state.get("session_id", "default")
    clean_session_id = "".join([c for c in session_id if c.isalnum() or c in ("-", "_")])
    
    sandbox_dir = tempfile.mkdtemp(prefix=f".sandbox_{clean_session_id}_", dir=".")
    sandbox_dir_abs = os.path.abspath(sandbox_dir)
    
    success = True
    output = ""
    
    try:
        copy_codebase(".", sandbox_dir_abs)
        
        for file_path, content in patch_files.items():
            dest_file = os.path.join(sandbox_dir_abs, file_path)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            with open(dest_file, "w") as f:
                f.write(content)
                
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{settings.WORKSPACE_PATH}:/workspace:ro",
            "-v", f"{sandbox_dir_abs}:/app",
            "-w", "/app",
            "-e", "PYTHONPATH=/app:/workspace/myenv/lib/python3.12/site-packages",
            "python:3.12-slim",
            "python", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        success = (res.returncode == 0)
        output = f"Stdout:\n{res.stdout}\n\nStderr:\n{res.stderr}"
        
    except Exception as e:
        success = False
        output = f"Failed to execute sandbox run: {str(e)}"
    finally:
        shutil.rmtree(sandbox_dir_abs, ignore_errors=True)
        
    return {
        "test_results": {
            "success": success,
            "output": output
        }
    }
