# CityWheels Help Desk Agent – Solution

A command-line AI agent that answers customer questions for CityWheels, a bike rental shop.
It uses Gemini with tool calling and three tools written in Python: `search_policies`,
`get_booking` and `calculate_refund`.

## How to install and run

Requirements: Python 3.10 or newer (I used 3.11).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your key from Google AI Studio:

```
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

All commands are run from the project root.

| What | Command |
| --- | --- |
| Agent (interactive chat, type `exit` to quit) | `python -m agent.cli` |
| Tests (no network, no API key needed) | `pytest` |
| Evaluation (calls the real model) | `python -m evaluation.run_evaluation` |

The tests also run on every push with GitHub Actions (`.github/workflows/tests.yml`).

## Model and provider

I used the **Google Gemini API free tier**, model **`gemini-3.5-flash-lite`**, called directly
with the `google-genai` SDK.

Why:
- It is free and supports tool calling.
- I tried other models first and the free-tier limits decided the choice:
  - `gemini-2.5-flash` – 404, no longer available to new users,
  - `gemini-3.8-flash` – 504 timeouts, the model was overloaded,
  - `gemini-3.6-flash` – only 20 requests per day; one evaluation run needs about 30–40,
  - `gemini-3.5-flash-lite` has 500 requests per day and 15 per minute, so the full evaluation fits.
- The model name is read from `GEMINI_MODEL`, so it can be changed without touching the code.

**No framework.** I wrote the agent loop myself instead of using LangChain or Google ADK.
The loop is short, I can explain every step, and it is easy to replace the model with a fake one
in tests.

## How the agent works

### Project structure

```
agent/
  config.py        current date, model name (from .env)
  prompt.py        system prompt
  model.py         GeminiModel: thin wrapper around the Gemini API
  agent_loop.py    run_agent(question, model): the tool-calling loop
  cli.py           interactive command line
  tools/
    bookings.py    get_booking
    policies.py    search_policies
    refunds.py     calculate_refund
tests/             unit tests and agent loop tests with a fake model
evaluation/        questions, evaluation script and results
data/              policies and bookings (given)
```

### The loop (`agent/agent_loop.py`)

1. The history starts with the user's question.
2. The model gets the history, the system prompt and the three tools.
   Automatic function calling in the SDK is **disabled**, so my code runs the tools.
3. If the model asks for tools, the loop adds the model's message to the history,
   runs each tool from a `name -> function` dictionary and adds the results
   (`Part.from_function_response`) to the history. Then it calls the model again.
4. If the model answers without asking for a tool, that is the final answer.
5. The loop stops after `MAX_ITERATIONS = 6` model calls and then returns a safe message
   with the staff contact.

Errors never crash the program: an unknown tool or an exception inside a tool is returned to the
model as an error result. `run_agent` returns the answer and the list of tools called
(used by the evaluation and tests).

The model is passed to `run_agent` as a parameter, so tests can use a fake model with the same
`generate(contents)` method.

### The tools

All tools are plain Python functions that return dictionaries. They do not know about Gemini.
The model sees their names, type hints and docstrings.

- **`get_booking(booking_id)`** – reads `data/bookings.json`. Normalizes the number
  (`" cw-1001 "` → `CW-1001`). Returns `{"found": True, "booking": ...}` or
  `{"found": False, "error": ...}`.
- **`search_policies(query)`** – splits the Markdown files into sections by `##` headings
  (22 sections, the intro of `prices.md` is kept). The query and every section are turned into
  sets of words: lowercase, `e-bike`/`ebike` → `electric bike`, stop words removed, every word cut
  to its first 4 letters (simple stemming, so `opening` matches `open`). Score = matching words
  in the text + 2 × matching words in the heading. Returns the top 3 sections, or an error
  telling the model to send the customer to the staff.
- **`calculate_refund(booking_id, cancel_time=None)`** – the amounts are calculated in code:
  - only `confirmed` bookings can be cancelled,
  - 48 h or more before the start → 100% of the rental price, 24–48 h → 50%, less than 24 h → 0%,
  - the booking fee is never refunded, the deposit is always refunded,
  - card → same card within 5 working days, voucher → new voucher.

  "Now" is the fixed date from `data/README.md` (2026-06-10 09:00 +02:00). The optional `cancel_time`
  allows questions like "what if I cancel on 12 June?". The result contains all parts of the
  calculation, so the model only has to repeat them.

### Instructions to the model (`agent/prompt.py`)

The system prompt tells the model to:
- answer only from tool results, never from its own knowledge,
- use `search_policies` with short English keywords, and `get_booking` for bookings,
- always use `calculate_refund` for amounts and never calculate them itself,
- say when a booking is not found,
- not change or cancel bookings and not promise what the staff decide,
- refuse unrelated questions and give the staff contact,
- answer in the customer's language,
- use the current date, and pass `cancel_time` for questions about another moment.

## Tests

`pytest` runs 43 tests in under a second, without network or API key:
- `test_bookings.py` – found, not first in the file, normalization, not found, empty number,
- `test_policies.py` – splitting into sections, word normalization, the right section for
  four queries, no match, at most 3 results,
- `test_refunds.py` – every booking, every status, every rule, both sides of the 48 h and 24 h
  thresholds (exactly 48 h → 100%, one minute less → 50%), invalid `cancel_time`,
- `test_agent.py` – the agent loop with a **fake model** that returns prepared Gemini responses:
  tool call then answer, answer without tools, unknown tool, unknown booking, iteration limit.

## Evaluation

`evaluation/questions.json` has 14 questions: 5 refund questions (each threshold, exactly 48 h,
another cancel time, a question in Polish), 2 booking edge cases, 3 policy questions,
2 questions where the staff decide and 2 off-topic questions.
Each question lists the tools that must be called, text the answer must contain and text it
must not contain. `evaluation/run_evaluation.py` runs the agent on all of them and writes `evaluation/results.md`.

**Last result: 13/14 with `gemini-3.5-flash-lite`.**

What failed and why:
- **First run: 12/14** – two questions failed with 429 (15 requests per minute limit), not
  because of the agent. I fixed the pause between questions.
- **`refund_exactly_48h` failed** – the model called `calculate_refund`, got the correct
  186 EUR, but answered with garbage text ("js"). I checked it manually: the same question gave
  "Db" once and a correct answer twice. The bad answer was a single text part with finish reason
  STOP and, unlike correct answers, without a thought signature. So it is a problem of the model,
  not of the loop. `refund_polish` passed, but had a stray "0" at the beginning.
- **What the evaluation does not catch** – checks are based on keywords. A few answers had the
  correct amount but a wrong explanation ("100% because more than 24 hours before", the rule is
  48 hours or more). Earlier, the agent said "booking fee €0" because the tool returned only the
  refunded fee; I fixed this by adding `booking_fee_eur` to the tool result.

## How I used AI coding assistants

I used Claude as a tutor: it explained concepts, proposed a task list and reviewed my code.
It also pointed me to documentation and learning resources I needed to build the app.
I wrote most of the tools myself. Writing tests is time-consuming and repetitive,
so I asked the assistant to help with them. Tests are separate from the application code and
do not change it, so a mistake in a generated test cannot break the agent.
At worst a test fails, and then I check whether the problem is in the test itself or in the code.
This saved me time on a repetitive task, while I still reviewed every test and ran them myself.
I also used it to help me with the evaluation script and the test questions. I ran the evaluation,
reviewed every answer and investigated the failures myself (e.g. rate limits and garbage answers from the model).

Examples where the output was wrong or needed changes:
- **Retired model.** It recommended `gemini-2.5-flash`; the API returned 404 "no longer
  available to new users". I noticed it from the error and changed the model in `.env`.
- **Wrong role for tool results.** Its loop sent tool results with `role="tool"`, as in the SDK
  docs; the API returned 400 "Role 'tool' is not supported". I changed it to `role="user"`.
- **`temperature=0`.** It suggested it for stable answers, but for Gemini 3 models Google
  recommends the default; with it the requests hung. I removed it and added a 60s timeout.

My own bugs found while testing (useful to show how I checked the code):
`else` inside the loop in `get_booking` (only the first booking was found),
`load_dotenv("MODEL_NAME")` (it loads a file, not a variable), string methods without
assignment (`header.strip()`), a typo in the tool name `calculated_refund`.

## Limitations

- No conversation memory: every question in the CLI is independent.
- The agent is read-only: it cannot change or cancel bookings.
- Keyword search: no understanding of meaning; the model must send English keywords.
- The free tier allows only a limited number of requests per minute and per day.
- Flash Lite sometimes returns garbage text or explains a rule wrongly, even with correct data.
- The evaluation checks keywords, not the full correctness of an answer.
- The current date is fixed, as required by `data/README.md`.

## What I would do next

- Retry when the final answer is suspiciously short (garbage text).
- Return the rule text (`refund_rule`) from `calculate_refund`, so the model does not guess it.
- Add a check for wrong explanations to the evaluation, or use a second model as a judge.
- Compare `gemini-3.5-flash-lite` with a stronger Flash model on the same questions.
- Conversation memory for follow-up questions.
- Better search (embeddings) and tools for changing bookings with staff approval.
