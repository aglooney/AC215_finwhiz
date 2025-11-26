import json
import os
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.system

RUN_FLAG = "RUN_SYSTEM_TESTS"


def test_full_pipeline_script():
    """Execute the full pipeline bash script when system tests are enabled."""
    if os.getenv(RUN_FLAG) != "1":
        pytest.skip("Set RUN_SYSTEM_TESTS=1 to run system-level tests.")

    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "test_full_pipeline.sh"
    assert script.exists(), f"Missing system test script at {script}"

    result = subprocess.run(
        ["bash", str(script)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout
    context_match = re.search(r"Current session context.*?\n({.*?})\n", output, re.DOTALL)
    llm_match = re.search(r"LLM Response:\n({.*?})\n", output, re.DOTALL)

    assert context_match, "Full pipeline script did not print session context JSON"
    assert llm_match, "Full pipeline script did not print LLM response JSON"

    context_json = json.loads(context_match.group(1))
    response_json = json.loads(llm_match.group(1))

    assert context_json.get("w2_fields") or context_json.get("form1099_fields") or context_json.get("portfolio_fields"), (
        "Controller context did not include any extracted document fields"
    )
    assert "answer" in response_json, "LLM response JSON missing 'answer'"
    assert isinstance(response_json.get("sources"), list), "LLM response JSON missing sources list"
