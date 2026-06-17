import os
import re
import ast
from typing import Dict, List, Any, Set

class CodeParser:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.languages_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "React (JS)",
            ".ts": "TypeScript",
            ".tsx": "React (TS)",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++ Header",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".html": "HTML",
            ".css": "CSS",
            ".sh": "Shell",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".json": "JSON",
            ".toml": "TOML",
            ".xml": "XML",
            ".gradle": "Gradle",
        }

    def scan_repository(self) -> Dict[str, Any]:
        """
        Scans repository directory and returns files metadata,
        language distribution, and detected frameworks.
        """
        file_counts = {}
        file_sizes = {}
        language_stats = {}
        total_files = 0
        total_size = 0
        all_files = []
        frameworks = set()
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv', '.venv', 'cache', '__pycache__')]
            
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, self.repo_path)
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    continue

                _, ext = os.path.splitext(file)
                ext = ext.lower()
                lang = self.languages_map.get(ext, "Unknown")
                
                all_files.append({
                    "path": rel_path.replace(os.sep, '/'),
                    "size": size,
                    "language": lang
                })
                
                total_files += 1
                total_size += size
                
                if lang != "Unknown":
                    language_stats[lang] = language_stats.get(lang, 0) + size
                    file_counts[lang] = file_counts.get(lang, 0) + 1
                    
                self._detect_framework_from_file(file, filepath, frameworks)

        language_distribution = {}
        if total_size > 0:
            for lang, size in language_stats.items():
                pct = round((size / total_size) * 100, 2)
                if pct > 0:
                    language_distribution[lang] = {
                        "size_bytes": size,
                        "percentage": pct,
                        "file_count": file_counts[lang]
                    }

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "language_distribution": language_distribution,
            "frameworks": list(frameworks),
            "files": all_files
        }

    def _detect_framework_from_file(self, filename: str, filepath: str, frameworks: Set[str]):
        """Helper to scan filenames and config files to detect libraries/frameworks."""
        if filename == "package.json":
            frameworks.add("Node.js")
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if '"next"' in content:
                        frameworks.add("Next.js")
                    if '"react"' in content:
                        frameworks.add("React")
                    if '"express"' in content:
                        frameworks.add("Express")
                    if '"vue"' in content:
                        frameworks.add("Vue")
                    if '"angular"' in content:
                        frameworks.add("Angular")
                    if '"typescript"' in content:
                        frameworks.add("TypeScript")
            except Exception:
                pass
        elif filename == "requirements.txt" or filename == "Pipfile" or filename == "pyproject.toml":
            frameworks.add("Python Project")
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "fastapi" in content.lower():
                        frameworks.add("FastAPI")
                    if "flask" in content.lower():
                        frameworks.add("Flask")
                    if "django" in content.lower():
                        frameworks.add("Django")
            except Exception:
                pass
        elif filename == "pom.xml" or filename == "build.gradle":
            frameworks.add("Java Project")
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "spring-boot" in content.lower():
                        frameworks.add("Spring Boot")
            except Exception:
                pass
        elif filename == "Cargo.toml":
            frameworks.add("Rust Cargo")
        elif filename == "go.mod":
            frameworks.add("Go Module")
        elif filename == "Dockerfile":
            frameworks.add("Docker")
        elif filename == "docker-compose.yml" or filename == "docker-compose.yaml":
            frameworks.add("Docker Compose")
        elif filename == "deployment.yaml" or filename == "k8s.yaml":
            frameworks.add("Kubernetes")
        elif filename.endswith(".tf"):
            frameworks.add("Terraform")

    def parse_code_file(self, rel_path: str) -> Dict[str, Any]:
        """Parses a code file and extracts functions, classes, imports, and metrics."""
        abs_path = os.path.join(self.repo_path, rel_path)
        if not os.path.exists(abs_path):
            return {"error": "File not found"}

        _, ext = os.path.splitext(rel_path)
        ext = ext.lower()

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

        lines = content.splitlines()
        loc = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*')))
        blank_lines = sum(1 for line in lines if not line.strip())

        result = {
            "file_path": rel_path,
            "lines_of_code": loc,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "classes": [],
            "functions": [],
            "imports": [],
        }

        if ext == ".py":
            try:
                tree = ast.parse(content)
                self._analyze_python_ast(tree, result)
            except SyntaxError:
                self._analyze_regex_js_py_java(content, result, "python")
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            self._analyze_regex_js_py_java(content, result, "js")
        elif ext == ".java":
            self._analyze_regex_js_py_java(content, result, "java")

        return result

    def _analyze_python_ast(self, tree: ast.AST, result: Dict[str, Any]):
        """Extracts code constructs from a Python AST node."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    result["imports"].append(name.name)
            elif isinstance(node, ast.ImportFrom):
                result["imports"].append(f"{node.module or ''}.{node.names[0].name}")
            
            elif isinstance(node, ast.ClassDef):
                result["classes"].append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "methods_count": sum(1 for subnode in node.body if isinstance(subnode, ast.FunctionDef)),
                    "complexity": self._calculate_python_node_complexity(node)
                })
            
            elif isinstance(node, ast.FunctionDef):
                args_count = len(node.args.args)
                comp = self._calculate_python_node_complexity(node)
                result["functions"].append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "arguments_count": args_count,
                    "complexity": comp,
                    "is_complex": comp > 7 or args_count > 4
                })

    def _calculate_python_node_complexity(self, node: ast.AST) -> int:
        """Approximates cyclomatic complexity based on AST branching points."""
        complexity = 1
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(subnode, ast.BoolOp):
                complexity += len(subnode.values) - 1
        return complexity

    def _analyze_regex_js_py_java(self, content: str, result: Dict[str, Any], lang_type: str):
        """Regex-based parser fallback for code metrics & structural analysis."""
        lines = content.splitlines()

        import_patterns = {
            "python": [r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)"],
            "js": [r"^\s*import\s+.*\s+from\s+['\"]([^'\"]+)['\"]", r"^\s*const\s+.*\s*=\s*require\(['\"]([^'\"]+)['\"]\)"],
            "java": [r"^\s*import\s+([a-zA-Z0-9_\.]+)\s*;"]
        }
        
        class_patterns = {
            "python": r"^\s*class\s+([a-zA-Z0-9_]+)",
            "js": r"^\s*class\s+([a-zA-Z0-9_]+)",
            "java": r"^\s*(?:public|protected|private)?\s*(?:static\s+)?class\s+([a-zA-Z0-9_]+)"
        }

        func_patterns = {
            "python": r"^\s*def\s+([a-zA-Z0-9_]+)\s*\((.*)\)\s*:",
            "js": r"(?:function\s+([a-zA-Z0-9_]+)\s*\(|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:\(.*\)|[a-zA-Z0-9_]+)\s*=>|([a-zA-Z0-9_]+)\s*\((?:[^)]*)\)\s*\{)",
            "java": r"^\s*(?:public|protected|private)?\s*(?:static\s+)?(?:[\w<>]+\s+)+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{"
        }

        for pat in import_patterns.get(lang_type, []):
            for match in re.finditer(pat, content, re.MULTILINE):
                result["imports"].append(match.group(1))

        class_pat = class_patterns.get(lang_type)
        if class_pat:
            for idx, line in enumerate(lines):
                match = re.match(class_pat, line)
                if match:
                    result["classes"].append({
                        "name": match.group(1),
                        "start_line": idx + 1,
                        "methods_count": 0,
                        "complexity": 1
                    })

        func_pat = func_patterns.get(lang_type)
        if func_pat:
            for idx, line in enumerate(lines):
                match = re.search(func_pat, line)
                if match:
                    name = next((g for g in match.groups() if g is not None), "anonymous")
                    if name in ("class", "if", "while", "for", "switch", "catch", "return"):
                        continue
                        
                    args_str = match.group(len(match.groups())) if len(match.groups()) > 1 else ""
                    args_count = len([a for a in (args_str or "").split(",") if a.strip()])
                    
                    complexity = 1
                    for next_line in lines[idx+1 : idx+16]:
                        if any(kw in next_line for kw in ("if ", "else if", "while", "for ", "catch", "&&", "||", "case ")):
                            complexity += 1

                    result["functions"].append({
                        "name": name,
                        "start_line": idx + 1,
                        "arguments_count": args_count,
                        "complexity": complexity,
                        "is_complex": complexity > 7 or args_count > 4
                    })
