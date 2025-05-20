import os
import ast


class PromptGenerator:
    def __init__(self, extract_function_code_func):
        self.extract_function_code = extract_function_code_func

    def _find_function_class(self, code, function_name):
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == function_name:
                            return node  # Zwróć węzeł klasy
            return None
        except Exception as e:
            print(f"AST parsing error while locating class for {function_name}: {e}")
            return None

    def _generate_prompt(self, file_path, imports, function_code, class_code, doc_snippet, function_name, test_type):
        import_info = f"\n# Imports:\n{chr(10).join(imports)}\n" if imports else ""
        doc_info = f"\nDocumentation:\n{doc_snippet}\n" if doc_snippet else ""

        if class_code:
            code_context = class_code
        else:
            code_context = function_code

        prompt = f"""
# File: {file_path}
# Function: {function_name}

{code_context}
{doc_info}
"""

        if test_type == "unit":
            prompt += (f"\nWrite unit tests using pytest for this function/method: {function_name}. Cover edge cases "
                       f"and important behaviors.")
        elif test_type == "fuzz":
            prompt += f"\nWrite fuzz tests for this function/method: {function_name} using Hypothesis for diverse inputs."
        elif test_type == "mutation":
            prompt += (f"\nWrite mutation-robust tests for this function/method: {function_name} ensuring key logic "
                       f"correctness.")
        elif test_type == "property":
            prompt += f"\nWrite property-based tests for this function/method: {function_name} describing invariants."

        return prompt

    def generate_batch_prompts(self, code_analysis_results, doc_data=None, test_type="unit"):
        print(
            f"\nNumber of functions detected during code analysis: {sum(len(v['functions']) for v in code_analysis_results.values())}")
        prompts = []

        for i, (file_path, data) in enumerate(code_analysis_results.items()):
            if i >= 10:
                break
            source_code = data.get("code", "")
            imports = data.get("imports", [])

            for function_name in data.get("functions", []):
                function_code = self.extract_function_code(source_code, function_name)
                related_docs = self._find_related_docs(file_path, doc_data, function_name)

                class_node = self._find_function_class(source_code, function_name)
                class_code = None
                if class_node:
                    class_code = ast.get_source_segment(source_code, class_node)

                prompt = self._generate_prompt(
                    file_path=file_path,
                    imports=imports,
                    function_code=function_code or f"# Function {function_name} code not found",
                    class_code=class_code,
                    doc_snippet=related_docs,
                    function_name=function_name,
                    test_type=test_type
                )

                prompts.append({
                    "file": file_path,
                    "function": function_name,
                    "prompt": prompt
                })

        return prompts

    def _find_related_docs(self, file_path, doc_data, function_name=None):
        if not doc_data or not function_name:
            return None

        target_function = function_name.lower()

        # Szukaj dopasowań, ale filtruj zbyt ogólne dokumenty jak "Changelog" czy "Performance"
        def is_valid_section(title):
            forbidden = ["changelog", "performance", "installation", "license", "contributing"]
            return not any(word in title.lower() for word in forbidden)

        best_match = None
        best_score = 0

        for doc_path, doc_info in doc_data.items():
            sections = doc_info.get("sections", {})

            for heading, content in sections.items():
                heading_lower = heading.lower()
                content_lower = content.lower()

                # Ignoruj bezużyteczne sekcje
                if not is_valid_section(heading):
                    continue

                score = 0

                # Dopasowanie nazwy funkcji w headingu
                if target_function == heading_lower:
                    score += 20

                # Funkcja wspomniana w treści
                if target_function in content_lower:
                    score += 10

                # Słowa kluczowe z funkcji
                keywords = target_function.split('_')
                score += sum(1 for k in keywords if k in heading_lower or k in content_lower)

                if score > best_score:
                    best_score = score
                    best_match = (heading, content)

        if best_match and best_score >= 15:  # <- tylko jeśli naprawdę wysokie trafienie
            heading, content = best_match
            return f"### {heading}\n{content[:1000]}"

        # Jeśli nie ma sensownego dopasowania
        return None



