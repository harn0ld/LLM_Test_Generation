import re

class FuzzTestGenerator:
    def __init__(self, extract_function_code_func, llm_client):
        self.extract_function_code = extract_function_code_func
        self.llm_client = llm_client

    def generate_fuzz_prompt(self, file_path, function_name, source_code, imports=None):
        imports = imports or []
        function_code = self.extract_function_code(source_code, function_name)

        prompt = f"""
# File: {file_path}
# Function: {function_name}
# Goal: Generate fuzz tests for this function using Hypothesis.
{chr(10).join(imports)}

{function_code}

Write Python fuzz tests using the `hypothesis` library to test the function `{function_name}`.
Cover edge cases, type variability, and invalid input combinations if applicable.
The tests must be compatible with pytest and include assert statements to verify correctness.
"""
        return prompt

    def auto_append_assertion(self, test_code: str, function_name: str) -> str:
        """
        Add an auto-generated assertion block if missing or too vague.
        """
        if "assert" in test_code:
            return test_code  # Already has assertions

        # Try to locate function call in test
        match = re.search(rf"(\w+)\s*=\s*{function_name}\(.*?\)", test_code)
        if match:
            var_name = match.group(1)
        else:
            var_name = "result"

        # Insert a basic assertion at the end
        assert_block = f"\n    assert {var_name} is not None\n    assert not isinstance({var_name}, Exception)"
        lines = test_code.strip().splitlines()
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("def ") and lines[i].endswith(":"):
                # Append after the test function block
                lines.insert(i + 2, assert_block)
                break
            if lines[i].strip().startswith("return"):
                lines.insert(i, assert_block)
                break
        return "\n".join(lines)

    def generate_tests_for_functions(self, code_analysis_results, max_files=10):
        fuzz_tests = []

        for i, (file_path, data) in enumerate(code_analysis_results.items()):
            if i >= max_files:
                break
            source_code = data.get("code", "")
            imports = data.get("imports", [])

            for function_name in data.get("functions", []):
                prompt = self.generate_fuzz_prompt(
                    file_path=file_path,
                    function_name=function_name,
                    source_code=source_code,
                    imports=imports
                )
                print(f"[+] Generating fuzz test for: {function_name}")
                response = self.llm_client.generate(prompt)

                if response:
                    response = self.auto_append_assertion(response, function_name)

                fuzz_tests.append({
                    "file": file_path,
                    "function": function_name,
                    "prompt": prompt,
                    "response": response
                })

        return fuzz_tests
