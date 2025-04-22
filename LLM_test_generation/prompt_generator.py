import os
import re
import ast

class PromptGenerator:
    def __init__(self, extract_function_code_func):
        self.extract_function_code = extract_function_code_func

    def generate_test_prompt(self, file_path, function_name, function_code, related_docs=None):
        doc_info = f"\nDokumentacja:\n{related_docs}\n" if related_docs else ""
        return f"""
# Plik: {file_path}
# Funkcja: {function_name}

{function_code}
{doc_info}
Napisz test jednostkowy w bibliotece pytest, który pokrywa wszystkie przypadki dla tej funkcji.
Zadbaj o dobre nazwy testów i różne przypadki wejściowe.
"""

    def generate_batch_prompts(self, code_analysis_results, doc_data=None):
        """
        Generuje wiele promptów na podstawie danych z CodeAnalyzer i DocReader.
        Zwraca listę promptów.
        """
        print(
            f"\nLiczba funkcji wykrytych w analizie kodu: {sum(len(v['functions']) for v in code_analysis_results.values())}")
        prompts = []
        for i, (file_path, data) in enumerate(code_analysis_results.items()):
            if i >= 10:
                break  # tylko 10 plików
            source_code = data.get("code", "")
            for function_name in data.get("functions", []):
                function_code = self.extract_function_code(source_code, function_name)
                related_docs = self._find_related_docs(file_path, doc_data)
                if not function_code:
                    print(f"Nie znaleziono kodu dla funkcji: {function_name} w pliku: {file_path}")
                    function_code = f"# Brak wyciągniętego kodu, tylko nazwa funkcji: {function_name}"
                prompt = self.generate_test_prompt(file_path, function_name, function_code, related_docs)
                prompts.append({
                    "file": file_path,
                    "function": function_name,
                    "prompt": prompt
                })
        return prompts

    def _find_related_docs(self, file_path, doc_data, function_name=None):
        if not doc_data:
            return None

        keywords = []
        if function_name:
            keywords = function_name.lower().split('_')

        for doc_path, doc_info in doc_data.items():
            try:
                if os.path.commonpath([file_path, doc_path]) in file_path:
                    sections = doc_info.get("sections", {})
                    matched_sections = []
                    for heading, content in sections.items():
                        heading_lower = heading.lower()
                        if any(k in heading_lower for k in keywords):
                            matched_sections.append((heading, content))

                    if matched_sections:
                        return "\n\n".join(f"### {h}\n{c[:500]}" for h, c in matched_sections)
                    else:
                        return doc_info.get("raw", "")[:1000]
            except ValueError:
                continue

        return None
