
from code_analyzer import CodeAnalyzer
from clone_github_repo import clone_github_repo
from doc_reader import DocReader
from prompt_generator import PromptGenerator
import shutil
import os
import stat

def handle_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def analyze_github_repo(repo_url):
    repo_path = clone_github_repo(repo_url)
    if not repo_path:
        return
    analyzer = CodeAnalyzer(repo_path)
    code_results = analyzer.analyze()
    #
    # print("\n --- Wyniki analizy kodu ---\n")
    # for file, data in code_results.items():
    #     print(f" Plik: {file}")
    #     print(data)
    #     print("-" * 50)

    doc_reader = DocReader(repo_path)
    docs = doc_reader.read_docs()

    # print("\n📚 --- Wyniki analizy dokumentacji ---\n")
    # for doc_file, doc_data in docs.items():
    #     print(f"Dokument: {doc_file}")
    #     print("Nagłówki:", doc_data.get("headings", []))
    #     print("Liczba przykładów:", len(doc_data.get("examples", [])))
    #     print("-" * 50)

    prompt_generator = PromptGenerator(analyzer.extract_function_code)
    prompts = prompt_generator.generate_batch_prompts(code_results, docs)

    print("\n --- Wygenerowane prompty testów ---\n")
    for p in prompts:
        print(f"Plik: {p['file']} - Funkcja: {p['function']}")
        print(p['prompt'])
        print("=" * 60)


    shutil.rmtree(repo_path, onerror=handle_remove_readonly)

if __name__ == "__main__":
    test_repo = "https://github.com/scikit-learn/scikit-learn.git"
    analyze_github_repo(test_repo)