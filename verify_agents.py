import asyncio
import sys
from app.agents.syntax_check_agent import extract_python_blocks, syntax_check_agent
from app.agents.sandbox_agent import parse_patch, sandbox_agent
from app.agents.graph import app_graph


def test_extract_python_blocks():
    print("--- Running test_extract_python_blocks ---")
    
    text_1 = "Here is some code:\n```python\ndef hello():\n    print('world')\n```"
    blocks_1 = extract_python_blocks(text_1)
    assert len(blocks_1) == 1
    assert "def hello():" in blocks_1[0]
    
    text_2 = "Block 1:\n```python\nx = 1\n```\nBlock 2:\n```python\ny = 2\n```"
    blocks_2 = extract_python_blocks(text_2)
    assert len(blocks_2) == 2
    assert blocks_2[0] == "x = 1"
    assert blocks_2[1] == "y = 2"
    
    text_3 = "import os\ndef my_func():\n    return os.getcwd()"
    blocks_3 = extract_python_blocks(text_3)
    assert len(blocks_3) == 1
    assert "import os" in blocks_3[0]
    
    text_4 = "This is a simple explanation response with no code whatsoever."
    blocks_4 = extract_python_blocks(text_4)
    assert len(blocks_4) == 0
    
    print("test_extract_python_blocks: PASSED")


async def test_syntax_check_agent():
    print("\n--- Running test_syntax_check_agent ---")
    
    state_valid = {
        "generated_patch": "```python\ndef test_add(a, b):\n    return a + b\n```"
    }
    result_valid = await syntax_check_agent(state_valid)
    print("Valid syntax result:", result_valid)
    assert result_valid["lint_results"]["success"] is True
    assert len(result_valid["lint_results"]["errors"]) == 0
    
    state_invalid = {
        "generated_patch": "```python\ndef test_add(a, b\n    return a + b\n```"
    }
    result_invalid = await syntax_check_agent(state_invalid)
    print("Invalid syntax result:", result_invalid)
    assert result_invalid["lint_results"]["success"] is False
    assert len(result_invalid["lint_results"]["errors"]) > 0
    assert "Syntax Error" in result_invalid["lint_results"]["errors"][0]
    
    state_plain = {
        "generated_patch": "This is a plain text patch indicating we do not need modifications."
    }
    result_plain = await syntax_check_agent(state_plain)
    print("Plain patch result:", result_plain)
    assert result_plain["lint_results"]["success"] is True
    assert len(result_plain["lint_results"]["errors"]) == 0
    
    print("test_syntax_check_agent: PASSED")


def test_parse_patch():
    print("\n--- Running test_parse_patch ---")
    
    patch_str = (
        "Here is the change:\n"
        "```python\n"
        "# FILE: app/services/test_service.py\n"
        "def test_foo():\n"
        "    return 'foo'\n"
        "```\n"
        "And another block:\n"
        "```python\n"
        "# FILE: test_another.py\n"
        "x = 5\n"
        "```\n"
        "And a block without FILE comment:\n"
        "```python\n"
        "y = 10\n"
        "```"
    )
    
    file_map = parse_patch(patch_str)
    print("Parsed patch files:", list(file_map.keys()))
    assert len(file_map) == 2
    assert "app/services/test_service.py" in file_map
    assert "test_another.py" in file_map
    assert "def test_foo():" in file_map["app/services/test_service.py"]
    
    print("test_parse_patch: PASSED")


async def test_sandbox_agent():
    print("\n--- Running test_sandbox_agent ---")
    
    state_pass = {
        "session_id": "test-session-pass",
        "generated_patch": (
            "```python\n"
            "# FILE: test_mock_success.py\n"
            "import unittest\n"
            "class MockSuccessTest(unittest.TestCase):\n"
            "    def test_success(self):\n"
            "        self.assertEqual(1 + 1, 2)\n"
            "```"
        )
    }
    
    print("Running sandbox agent with passing test patch...")
    res_pass = await sandbox_agent(state_pass)
    print("Passing test results:", res_pass)
    assert res_pass["test_results"]["success"] is True
    
    state_fail = {
        "session_id": "test-session-fail",
        "generated_patch": (
            "```python\n"
            "# FILE: test_mock_fail.py\n"
            "import unittest\n"
            "class MockFailTest(unittest.TestCase):\n"
            "    def test_fail(self):\n"
            "        self.assertEqual(1 + 1, 99)\n"
            "```"
        )
    }
    
    print("Running sandbox agent with failing test patch...")
    res_fail = await sandbox_agent(state_fail)
    print("Failing test results:", res_fail)
    assert res_fail["test_results"]["success"] is False
    assert "AssertionError" in res_fail["test_results"]["output"]
    
    state_lint_failed = {
        "lint_results": {
            "success": False,
            "errors": ["IndentationError"]
        }
    }
    res_skipped = await sandbox_agent(state_lint_failed)
    print("Skipped sandbox result:", res_skipped)
    assert res_skipped["test_results"]["success"] is False
    assert "Skipped" in res_skipped["test_results"]["output"]

    print("test_sandbox_agent: PASSED")


def test_graph_structure():
    print("\n--- Running test_graph_structure ---")
    nodes = app_graph.nodes
    print("Graph Nodes:", list(nodes.keys()))
    assert "syntax_checker" in nodes
    assert "sandbox_runner" in nodes
    assert "reviewer" in nodes
    assert "generator" in nodes
    print("test_graph_structure: PASSED")


async def main():
    test_extract_python_blocks()
    await test_syntax_check_agent()
    test_parse_patch()
    await test_sandbox_agent()
    test_graph_structure()
    print("\nALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
