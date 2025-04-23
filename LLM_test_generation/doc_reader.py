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
                        print(f"Error in {filepath}: {e}")
        return self.docs_data

    def analyze_text(self, text):
        headings = []
        sections = {}

        # Markdown-style headers (e.g., ### Header)
        md_pattern = re.compile(r'^\s{0,3}(#{1,6})\s+(.*)', re.MULTILINE)
        matches = list(md_pattern.finditer(text))

        for i, match in enumerate(matches):
            level, title = match.groups()
            headings.append(title.strip())
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_content = text[start:end].strip()
            sections[title.strip()] = section_content

        # RST-style headers (e.g., underlined ===)
        rst_lines = text.splitlines()
        for i in range(1, len(rst_lines)):
            if re.match(r'^[=\-`~:\^\'"]{3,}$', rst_lines[i].strip()):
                title = rst_lines[i - 1].strip()
                headings.append(title)
                start = text.find(title)
                next_title = None
                for j in range(i + 1, len(rst_lines)):
                    if re.match(r'^[=\-`~:\^\'"]{3,}$', rst_lines[j].strip()):
                        next_title = rst_lines[j - 1].strip()
                        break
                end = text.find(next_title) if next_title else len(text)
                section_content = text[start:end].strip()
                sections[title] = section_content

        # Code examples
        code_blocks = re.findall(r'```[\s\S]*?```', text, re.MULTILINE)
        code_blocks += re.findall(r'::\n\n(?: {4}|\t).+', text, re.MULTILINE)

        return {
            "headings": headings,
            "examples": code_blocks,
            "sections": sections,
            "raw": text[:1000]
        }
