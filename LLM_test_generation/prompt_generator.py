import os
import re
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
            if i > 10: break
            code_lines = data.get("code", "").splitlines()

            for function_name in data.get("functions", []):
                # Znajdź kod funkcji (uproszczone podejście)
                function_code = self.extract_function_code(data["code"], function_name)
                related_docs = self._find_related_docs(file_path, doc_data)
                if not function_code:
                    print(f"Nie znaleziono kodu dla funkcji: {function_name} w pliku: {file_path}")
                    function_code = f"# Brak wyciągniętego kodu, tylko nazwa funkcji: {function_name}"
                if function_code:
                    prompt = self.generate_test_prompt(file_path, function_name, function_code, related_docs)
                    prompts.append({
                        "file": file_path,
                        "function": function_name,
                        "prompt": prompt
                    })
        return prompts



    def _extract_function_code(self, code_lines, function_name):
        """
        Szuka kodu funkcji przez analizę linii od def ...: aż do końca ciała.
        Obsługuje też funkcje wewnątrz klas.
        """
        start_idx = None
        indent_level = None
        func_pattern = re.compile(rf'^\s*def\s+{re.escape(function_name)}\s*\(.*')

        for i, line in enumerate(code_lines):
            if func_pattern.match(line):
                start_idx = i
                indent_level = len(line) - len(line.lstrip())
                break

        if start_idx is None:
            return None  # nie znaleziono

        # Zbierz linie aż do końca ciała funkcji (na podstawie wcięcia)
        function_code_lines = [code_lines[start_idx]]
        for line in code_lines[start_idx + 1:]:
            stripped = line.lstrip()
            if not stripped:  # pusta linia
                function_code_lines.append(line)
                continue
            current_indent = len(line) - len(stripped)
            if current_indent <= indent_level:
                break
            function_code_lines.append(line)

        return "\n".join(function_code_lines)

    def _find_related_docs(self, file_path, doc_data):
        """
        Szuka dokumentacji związanej z plikiem lub folderem, w którym znajduje się kod.
        """
        for doc_path, doc_info in doc_data.items():
            if os.path.commonpath([file_path, doc_path]) in file_path:
                return doc_info.get("raw", "")[:1000]  # ograniczamy długość
        return None
