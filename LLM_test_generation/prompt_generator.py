import os
import re
import ast


class PromptGenerator:
    def __init__(self, extract_function_code_func):
        self.extract_function_code = extract_function_code_func

#     def generate_test_prompt(self, file_path, function_name, function_code, related_docs=None):
#         doc_info = f"\nDokumentacja:\n{related_docs}\n" if related_docs else ""
#         return f"""
# # Plik: {file_path}
# # Funkcja: {function_name}
#
# {function_code}
# {doc_info}
# Napisz test jednostkowy w bibliotece pytest, który pokrywa wszystkie przypadki dla tej funkcji.
# Zadbaj o dobre nazwy testów i różne przypadki wejściowe.
# """

    def _generate_prompt_by_type(self, file_path, function_name, function_code, docs, test_type):
        doc_info = f"\nDocumentation:\n{docs}\n" if docs else ""

        base = f"""
    # File: {file_path}
    # Function: {function_name}

    {function_code}
    {doc_info}
    """
        if test_type == "unit":
            return base + "Write unit tests using pytest for this function. Cover various edge cases."
        elif test_type == "integration":
            return base + "Write integration tests that verify this function works correctly with related components."
        elif test_type == "fuzz":
            return base + "Write fuzz tests using Hypothesis or a similar tool to generate random input data."
        elif test_type == "mutation":
            return base + "Write strong unit tests suitable for mutation testing. Focus on asserting key conditions."
        elif test_type == "property":
            return base + ("Write property-based tests using Hypothesis. Define properties the function should always "
                           "satisfy.")

    def generate_batch_prompts(self, code_analysis_results, doc_data=None, test_type="unit"):
        """
        Generuje wiele promptów na podstawie danych z CodeAnalyzer i DocReader.
        Zwraca listę promptów.
        """
        print(
            f"\nNumber of functions detected during code analysis: {sum(len(v['functions']) for v in code_analysis_results.values())}")
        prompts = []
        for i, (file_path, data) in enumerate(code_analysis_results.items()):
            if i >= 10:
                break
            source_code = data.get("code", "")
            for function_name in data.get("functions", []):
                function_code = self.extract_function_code(source_code, function_name)
                related_docs = self._find_related_docs(file_path, doc_data)
                if not function_code:
                    print(f"No code found for function: {function_name} in file: {file_path}")
                    function_code = f"# No extracted code available, only function name: {function_name}"
                prompt = self._generate_prompt_by_type(file_path, function_name, function_code, related_docs, test_type)
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
