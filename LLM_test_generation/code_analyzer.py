import ast
import os


class CodeAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.analysis_result = {}

    def extract_function_code(self, code, function_name):
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):  # FunctionDef to subclass of AST
                    if node.name == function_name:
                        return ast.get_source_segment(code, node)
            return None
        except Exception as e:
            print(f"AST error while extracting {function_name}: {e}")
            return None

    def analyze(self):
        for subdir, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(subdir, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                        analysis = self._analyze_code(code)
                        analysis["code"] = code
                        self.analysis_result[filepath] = analysis
        return self.analysis_result

    def _analyze_code(self, code):
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"error": str(e)}

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name = getattr(node, 'module', '')
                for alias in node.names:
                    imports.append(f"{module_name}.{alias.name}" if module_name else alias.name)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports
        }


