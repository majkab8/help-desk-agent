# CityWheels Help Desk Agent

A command-line AI agent that answers customer questions for CityWheels, a made-up bike rental shop.
It uses Gemini with tool calling and answers only from the shop's policies and booking data.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Gemini API key. Then, from the project root:

| What | Command |
| --- | --- |
| Agent (interactive chat) | `python -m agent.cli` |
| Tests (no API key needed) | `pytest` |
| Evaluation | `python -m evaluation.run_evaluation` |

## More

- [SOLUTION.md](SOLUTION.md) – how the agent works, model choice, tests, evaluation results and limitations.
- [data/README.md](data/README.md) – the original description of the data and the fixed current date.

## Contact

Maja Bednarek

- GitHub: [majkab8](https://github.com/majkab8)
- Email: [bednarekmaja02@gmail.com]
- LinkedIn: [https://www.linkedin.com/in/maja-bednarek-599119324/]
