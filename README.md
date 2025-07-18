# 🤖 LLM Test Generation

**LLM_Test_Generation** is a developer-assist tool that uses Large Language Models (LLMs) to automatically generate software tests for existing Python codebases. This tool reduces manual effort, increases test coverage, and helps identify edge cases and bugs more effectively through both unit and fuzz testing techniques.
The implementation is functional, albeit not yet fully optimized.
---

## 🚀 Key Features

- 🔍 **Static Code Analysis** – Parses Python code using AST to extract functions, classes, and imports.
- 🧠 **LLM-Powered Test Generation** – Prompts LLM ( CodeLlama) to write unit or fuzz tests based on extracted code.
- 🧪 **Supports Unit & Fuzz Tests** – Generates classic unit tests as well as property-based fuzz tests using `hypothesis`.
- 📈 **Coverage Integration** – Uses `coverage.py` to analyze current test coverage and prioritize uncovered areas.
- 🔁 **Multi-test Generation** – Capable of generating multiple test variants per function/module.


---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Core Libraries**:
  - `ast` – Abstract Syntax Tree for parsing code
  - `openai` or local LLM wrappers
  - `coverage.py` – For test coverage analysis
  - `hypothesis` – For fuzz testing
  - `pytest` – For running generated tests

---

## 🧠 How It Works

1. **Code Analysis**: Parses the source code to identify functions and classes.
2. **Prompt Construction**: Dynamically builds prompts describing the code to the LLM.
3. **Test Generation**: Sends prompts to an LLM ( local CodeLlama) and receives test code.
4. **Saving Tests**: Stores generated test cases in structured directories.
5. **Coverage Reporting**: Optionally runs coverage analysis to report uncovered lines.

---

