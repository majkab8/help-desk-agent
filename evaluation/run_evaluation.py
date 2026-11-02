import json
import time
from datetime import datetime
from pathlib import Path

from agent.agent_loop import run_agent
from agent.config import GEMINI_MODEL
from agent.model import GeminiModel

EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = EVAL_DIR / "questions.json"
RESULTS_PATH = EVAL_DIR / "results.md"
PAUSE_SECONDS = 20


def check_answer(case, answer, tools_called):
    """Return a list of problems. An empty list means the case passed."""
    problems = []
    answer_lower = answer.lower()

    for tool in case["expected_tools"]:
        if tool not in tools_called:
            problems.append(f"tool {tool} was not called")

    for text in case["must_contain"]:
        if text.lower() not in answer_lower:
            problems.append(f"missing '{text}'")

    for text in case["must_not_contain"]:
        if text.lower() in answer_lower:
            problems.append(f"contains '{text}'")

    return problems


def run_case(case, model):
    try:
        result = run_agent(case["question"], model)
        answer = result["answer"]
        tools_called = result["tools_called"]
        problems = check_answer(case, answer, tools_called)
    except Exception as error:
        answer = ""
        tools_called = []
        problems = [f"agent error: {error}"]

    return {
        "case": case,
        "answer": answer,
        "tools_called": tools_called,
        "problems": problems,
        "passed": not problems,
    }


def for_table(text):
    """Make text safe for one cell of a Markdown table."""
    return text.replace("|", "\\|").replace("\n", " ")


def write_report(results):
    passed = sum(1 for result in results if result["passed"])
    total = len(results)

    lines = [
        "# Evaluation results",
        "",
        f"Model: {GEMINI_MODEL}",
        f"Passed: {passed}/{total}",
        "",
    ]

    for result in results:
        case = result["case"]
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"## {case['id']}: {status}")
        lines.append(f"Question: {case['question']}")
        lines.append(f"Expected: {case['note']}")
        lines.append(f"Tools: {', '.join(result['tools_called']) or '-'}")
        if result["problems"]:
            lines.append(f"Problems: {'; '.join(result['problems'])}")
        lines.append(f"Answer: {result['answer']}")
        lines.append("")

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    return passed, total


def main():
    cases = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    model = GeminiModel()
    results = []

    for number, case in enumerate(cases, start=1):
        print(f"[{number}/{len(cases)}] {case['id']} ... ", end="", flush=True)
        result = run_case(case, model)
        results.append(result)
        print("PASS" if result["passed"] else f"FAIL ({'; '.join(result['problems'])})")

        if number < len(cases):
            time.sleep(PAUSE_SECONDS)

    passed, total = write_report(results)
    print(f"\nPassed {passed}/{total}. Report saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()