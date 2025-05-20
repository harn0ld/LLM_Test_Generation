from code_analyzer import CodeAnalyzer
from clone_github_repo import clone_github_repo
from doc_reader import DocReader
from prompt_generator import PromptGenerator
from coverage_analyzer import CoverageAnalyzer
from fuzz_test_generator import FuzzTestGenerator
import shutil
import os
import stat
import argparse
from ollama_client import OllamaClient
import re
import ast
def extract_code_block(response: str) -> str:
    match = re.search(r"```(?:python)?(.*?)```", response, re.DOTALL)
    return match.group(1).strip() if match else response.strip()
def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
def handle_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)
def ensure_pytest_import(code: str) -> str:
    if "pytest." in code or "@pytest." in code:
        if "import pytest" not in code:
            return "import pytest\n\n" + code
    return code
def fix_hypothesis_settings(code: str) -> str:
    pattern = r"with\s+hypothesis\.settings\((.*?)\):"
    return re.sub(pattern, r"@hypothesis.settings(\1)\n", code)
def ensure_hypothesis_imports(code: str) -> str:
    lines = code.strip().splitlines()
    needed_imports = []

    if "@given" in code or "st." in code:
        if "from hypothesis import given" not in code:
            needed_imports.append("from hypothesis import given, strategies as st")

    if "@hypothesis.settings" in code or "hypothesis.settings" in code:
        if "import hypothesis" not in code:
            needed_imports.append("import hypothesis")

    if "pytest." in code or "pytest.raises" in code:
        if "import pytest" not in code:
            needed_imports.append("import pytest")

    return "\n".join(needed_imports + [""] + lines)
def fix_common_import_mistakes(code: str) -> str:
    # LLM często myli lokalne moduły z `sklearn` lub `spin`
    fixed = code
    fixed = fixed.replace("from sklearn import util", "from . import util")
    fixed = fixed.replace("from spin import util", "from . import util")
    return fixed
def auto_add_function_import(code: str, function_name: str, file_path: str) -> str:
    """
    Dodaje brakujący import do funkcji, jeśli nie występuje.
    Zakłada, że testy i kod źródłowy są w tym samym repozytorium.
    """
    base_module = os.path.basename(file_path).replace(".py", "")
    import_line = f"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from {base_module} import {function_name}
"""

    lines = code.splitlines()
    lines = [l for l in lines if not (
        l.strip().startswith("from ") and function_name in l and "import" in l
    )]

    if function_name in code and import_line not in code:
        lines.insert(0, import_line)

    return "\n".join(lines)
def split_into_test_functions(code: str) -> list[str]:
    """
    Splits a code block into multiple test functions (or top-level code blocks).
    """
    blocks = []
    current = []
    lines = code.splitlines()
    for line in lines:
        if line.strip().startswith("def test_") and current:
            blocks.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks
def analyze_github_repo(repo_url, test_type="unit"):
    global test_file_name
    repo_path = clone_github_repo(repo_url)
    if not repo_path:
        return

    analyzer = CodeAnalyzer(repo_path)
    code_results = analyzer.analyze()

    doc_reader = DocReader(repo_path)
    docs = doc_reader.read_docs()

    print("\n --- Generated test prompts ---\n")
    os.makedirs(os.path.join(repo_path, "tests"), exist_ok=True)

    if test_type == "fuzz":
        llm_client = OllamaClient(model_name="codellama:latest")
        generator = FuzzTestGenerator(analyzer.extract_function_code, llm_client)
        prompts = generator.generate_tests_for_functions(code_results, max_files=1)
        use_response_directly = True
    else:
        generator = PromptGenerator(analyzer.extract_function_code)
        prompts = generator.generate_batch_prompts(code_results, docs, test_type)
        use_response_directly = False

    for i, p in enumerate(prompts):
        if i >= 1:
            break
        print(f"File: {p['file']} - Function: {p['function']}")
        print(f"Prompt:\n{p['prompt']}")
        print("=" * 60)

        response = p["response"] if use_response_directly else send_prompt_to_ollama(p["prompt"])
        if test_type =='fuzz':
            print_prompt_and_response(response)

        code = extract_code_block(response)
        if test_type == 'fuzz':
            for j, snippet in enumerate(split_into_test_functions(code)):
                test_file_name = f"test_{p['function']}_{i}_{j}.py"
                test_file_path = os.path.join(repo_path, "tests", test_file_name)
                code1 = extract_code_block(snippet)
                code1 = ensure_pytest_import(code1)
                code1 = fix_common_import_mistakes(code1)
                code1 = ensure_hypothesis_imports(code1)
                code1 = auto_add_function_import(code1, p['function'], p['file'])
                snippet = fix_hypothesis_settings(code1)
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(snippet)

        else:

            code = ensure_pytest_import(code)
            code = fix_common_import_mistakes(code)
            code = auto_add_function_import(code, p['function'], p['file'])
            test_file_name = f"test_{p['function']}_{i}.py"
            test_file_path = os.path.join(repo_path, "tests", test_file_name)

            if is_valid_python(code):
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(code)
            else:
                print("Syntax error in generated code. Not saving.")
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write("# Syntax error in generated code\n" + code)

    # --- Coverage analysis ---
    coverage_analyzer = CoverageAnalyzer(test_dir=os.path.join(repo_path, "tests"), source_dir=repo_path)
    coverage_analyzer.run_coverage()
    coverage_results = coverage_analyzer.parse_coverage()

    print("\n --- Coverage Results ---")
    for file, funcs in coverage_results.items():
        print(f"File: {file}")
        for func, cov in funcs.items():
            print(f"  {func}: {cov}%")
        print("-" * 40)

    shutil.rmtree(repo_path, onerror=handle_remove_readonly)

def print_prompt_and_response(model_response,prompt_text=" "):
    print(f"Prompt length: {len(prompt_text)}")
    print("=== Model Response ===")
    if model_response:
        print(model_response)
    else:
        print("No response generated.")
    print("=" * 60)


def send_prompt_to_ollama(prompt_text):
    """Send the prompt to Ollama model and display the response."""
    client = OllamaClient(model_name="codellama:latest")
    result = client.generate(prompt_text)
    print_prompt_and_response(result, prompt_text=prompt_text)
    return result


def main():
    parser = argparse.ArgumentParser(description="Code Test Prompt Generator")
    parser.add_argument("repo", help="GitHub repo URL to analyze")
    parser.add_argument("--test", choices=["unit", "integration", "fuzz", "mutation", "property"], default="unit",
                        help="Choose type of tests to generate")
    args = parser.parse_args()

    print(f"\nCloning and analyzing repository: {args.repo}")
    print(f"Test type selected: {args.test}")
    analyze_github_repo(args.repo, args.test)


if __name__ == "__main__":
    # main()
    test_repo = "https://github.com/proatik/sorting-algorithms.git"
    #analyze_github_repo(test_repo)
    analyze_github_repo(test_repo,test_type = 'fuzz')
