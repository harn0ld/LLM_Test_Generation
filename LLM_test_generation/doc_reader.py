import os
import re
import spacy

class DocReader:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.docs_data = {}
        self.nlp = spacy.load("en_core_web_sm")

    def read_docs(self):
        for subdir, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(('.md', '.rst')):
                    filepath = os.path.join(subdir, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    if len(content) > 10000:
                        content = content[:10000]

                    if not ('#' in content or '```' in content):
                        continue

                    try:
                        self.docs_data[filepath] = self.analyze_text(content)
                    except Exception as e:
                        print(f"Błąd w {filepath}: {e}")
        return self.docs_data

    def analyze_text(self, text):
        headings = []

        # Markdown-style headers
        headings += re.findall(r'^\s{0,3}#{1,6}\s+(.*)', text, re.MULTILINE)

        # reStructuredText headers (e.g., === underlines)
        rst_lines = text.splitlines()
        for i in range(1, len(rst_lines)):
            if re.match(r'^[=\-`~:\^\'"]{3,}$', rst_lines[i].strip()):
                headings.append(rst_lines[i - 1].strip())

        # Code blocks (Markdown-style or RST-style)
        code_blocks = re.findall(r'```[\s\S]*?```', text, re.MULTILINE)
        code_blocks += re.findall(r'::\n\n(?: {4}|\t).+', text, re.MULTILINE)

        return {
            "headings": headings,
            "examples": code_blocks,
            "raw": text[:1000]
        }

