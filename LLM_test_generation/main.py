from code_analyzer import CodeAnalyzer
from clone_github_repo import clone_github_repo
from doc_reader import DocReader
from prompt_generator import PromptGenerator
import shutil
import os
import stat
import argparse


def handle_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def analyze_github_repo(repo_url, test_type="unit"):
    repo_path = clone_github_repo(repo_url)
    if not repo_path:
        return
    analyzer = CodeAnalyzer(repo_path)
    code_results = analyzer.analyze()

    doc_reader = DocReader(repo_path)
    docs = doc_reader.read_docs()

    print("\n --- Documentation Analysis Results ---\n")
    for doc_file, doc_data in docs.items():
        print(f"Document: {doc_file}")
        print("Headings:", doc_data.get("headings", []))
        print("Number of examples:", len(doc_data.get("examples", [])))
        print("-" * 50)

    prompt_generator = PromptGenerator(analyzer.extract_function_code)
    prompts = prompt_generator.generate_batch_prompts(code_results, docs, test_type)

    print("\n --- Generated test prompts ---\n")
    for p in prompts:
        print(f"File: {p['file']} - Function: {p['function']}")
        print(p['prompt'])
        print("=" * 60)

    shutil.rmtree(repo_path, onerror=handle_remove_readonly)


def main():
    parser = argparse.ArgumentParser(description="Code Test Prompt Generator")
    parser.add_argument("repo", help="GitHub repo URL to analyze")
    parser.add_argument("--test", choices=["unit", "integration", "fuzz", "mutation", "property"], default="unit",
                        help="Choose type of tests to generate")
    args = parser.parse_args()

    print(f"\n Cloning and analyzing repository: {args.repo}")
    print(f" Test type selected: {args.test}")
    analyze_github_repo(args.repo, args.test)


if __name__ == "__main__":
    # main()
    test_repo = "https://github.com/scikit-learn/scikit-learn.git"
    analyze_github_repo(test_repo)
