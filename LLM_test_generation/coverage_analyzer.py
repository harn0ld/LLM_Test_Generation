import subprocess
import json
import os
import ast
from collections import defaultdict


class CoverageAnalyzer:
    def __init__(self, test_dir="tests", source_dir=".", report_file="coverage.json"):
        self.test_dir = test_dir
        self.source_dir = source_dir
        self.report_file = report_file

    def run_coverage(self):
        """
        Run pytest with coverage and export as JSON.
        """
        env = os.environ.copy()
        env["PYTHONPATH"] = self.source_dir + os.pathsep + env.get("PYTHONPATH", "")
        print("[+] Running coverage...")

        run_result = subprocess.run(
            ["coverage", "run", "--source", self.source_dir, "-m", "pytest", self.test_dir],
            check=False,
            env=env
        )

        if run_result.returncode != 0:
            print(f" pytest failed with exit code {run_result.returncode} — some tests failed.")

        json_result = subprocess.run(
            ["coverage", "json", "-o", self.report_file],
            check=False,
            env=env
        )

        if json_result.returncode != 0:
            print(f" Failed to generate coverage JSON report (exit code {json_result.returncode}).")
    def parse_coverage(self):
        """
        Parse the generated coverage JSON and return function-level coverage.
        """
        with open(self.report_file, "r") as f:
            data = json.load(f)

        file_coverage = defaultdict(dict)

        files = data.get("files")
        if not files:
            print(" No coverage data found. Possibly no tests ran.")
            return {}

        for file_key, file_entry in files.items():
            file_path = file_entry.get("filename", file_key)
            summary = file_entry.get("summary", {})
            executed_lines = set(file_entry.get("executed_lines", []))
            missing_lines = set(file_entry.get("missing_lines", []))

            if not file_path.endswith(".py"):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    func_lines = set(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
                    if not func_lines:
                        continue

                    executed = len(func_lines & executed_lines)
                    total = len(func_lines)
                    coverage = (executed / total) * 100 if total > 0 else 0

                    file_name = os.path.basename(file_path)
                    file_coverage[file_name][func_name] = round(coverage, 1)
        return dict(file_coverage)
