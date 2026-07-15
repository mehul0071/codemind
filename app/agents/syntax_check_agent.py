import re
import os
import sys
import tempfile
import subprocess
import shutil
from typing import Dict, Any, List
from app.agents.state import AgentState


def extract_python_blocks(text: str) -> List[str]:
    pattern = re.compile(r"```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
    blocks = pattern.findall(text)
    if not blocks:
        keywords = ["def ", "class ", "import ", "from ", "print("]
        if any(kw in text for kw in keywords):
            blocks = [text]
            
    return [b.strip() for b in blocks if b.strip()]


async def syntax_check_agent(state: AgentState) -> Dict[str, Any]:
    patch = state.get("generated_patch") or ""
    if not patch:
        return {
            "lint_results": {
                "success": True,
                "errors": ["No generated patch found to check."]
            }
        }
        
    code_blocks = extract_python_blocks(patch)
    if not code_blocks:
        return {
            "lint_results": {
                "success": True,
                "errors": []
            }
        }
        
    success = True
    errors = []
    
    black_cmd = None

    if shutil.which("black"):
        black_cmd = ["black", "--check"]
    else:
        try:
            r = subprocess.run([sys.executable, "-m", "black", "--version"], capture_output=True, text=True)
            if r.returncode == 0:
                black_cmd = [sys.executable, "-m", "black", "--check"]
        except Exception:
            pass

    for idx, block in enumerate(code_blocks):
        fd, temp_file_path = tempfile.mkstemp(suffix=".py", prefix=f"temp_patch_{idx}_", dir=".")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(block)
                
            compile_cmd = [sys.executable, "-m", "py_compile", temp_file_path]
            compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
            
            if compile_res.returncode != 0:
                success = False
                err_msg = compile_res.stderr.replace(temp_file_path, f"code_block_{idx}.py")
                errors.append(f"Syntax Error in block {idx}:\n{err_msg}")
                continue
                
            if black_cmd:
                black_res = subprocess.run(black_cmd + [temp_file_path], capture_output=True, text=True)
                if black_res.returncode != 0:

                    if "Cannot parse" in black_res.stderr or "Cannot parse" in black_res.stdout:
                        success = False
                        err_msg = (black_res.stderr or black_res.stdout).replace(temp_file_path, f"code_block_{idx}.py")
                        errors.append(f"Black Formatter parsing error in block {idx}:\n{err_msg}")
                    else:
                        err_msg = (black_res.stderr or black_res.stdout).replace(temp_file_path, f"code_block_{idx}.py")
                        errors.append(f"Black Formatting warning in block {idx}:\n{err_msg}")

        except Exception as e:
            success = False
            errors.append(f"Failed to execute syntax check on block {idx}: {str(e)}")
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
                
    return {
        "lint_results": {
            "success": success,
            "errors": errors
        }
    }
