import re
import os
from typing import List, Dict, Any

class SecurityScanner:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        
        self.rules = [
            (
                "Hardcoded Private Key",
                r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
                "Critical",
                "An exposed cryptographic private key was found in the source code.",
                "Remove the private key immediately and rotate any compromised credentials. Use environment variables or a secrets manager.",
                [".pem", ".key", ".py", ".js", ".ts", ".json", ".yml", ".yaml", ".env"]
            ),
            (
                "Generic Exposed Secret",
                r"(?i)(?:key|pwd|password|secret|token|api_key|apikey|passwd|aws_secret|client_secret|client_id)\s*[:=]\s*['\"][a-zA-Z0-9_\-\+]{16,}['\"]",
                "High",
                "A potential hardcoded API key, credential, or secret token was detected.",
                "Move secrets to environment variables, a .env file (ensure it is added to .gitignore), or use a cloud Key Vault.",
                [".py", ".js", ".ts", ".json", ".yml", ".yaml", ".env", ".java"]
            ),
            (
                "Potential SQL Injection (Python)",
                r"(?i)\.execute\(\s*f['\"].*SELECT.*\{.*\}",
                "High",
                "An SQL query constructed with f-strings or direct variable string concatenation was detected. This allows SQL Injection.",
                "Use parameterized queries (e.g. `cursor.execute('SELECT * FROM users WHERE name = %s', (username,))`) instead of string formatting.",
                [".py"]
            ),
            (
                "Potential SQL Injection (JS/TS)",
                r"(?i)(?:db|conn|query|execute)\s*\(\s*[`'\"].*SELECT.*\$\{.*\}",
                "High",
                "An SQL query using string template interpolation was detected, presenting SQL Injection risk.",
                "Use prepared statements or parameterized queries provided by your ORM/DB driver.",
                [".js", ".ts", ".jsx", ".tsx"]
            ),
            (
                "Unsafe Command Execution",
                r"(?i)(?:os\.system|subprocess\.Popen|subprocess\.run|exec|eval)\s*\(\s*[^'\"]",
                "Critical",
                "Use of shell execution functions with dynamic strings can lead to command injection vulnerabilities.",
                "Avoid using shell=True and executing string inputs. Pass list parameters to subprocess or use native programming APIs.",
                [".py"]
            ),
            (
                "Unsafe eval() / exec() in JS",
                r"\b(?:eval|exec)\s*\([^\)]+\)",
                "High",
                "Use of eval() or exec() with dynamic inputs allows remote code execution (RCE).",
                "Refactor code to avoid evaluating expressions as strings. Use JSON.parse or strict map lookup tables.",
                [".js", ".ts", ".jsx", ".tsx"]
            ),
            (
                "Insecure Hash Algorithm",
                r"(?i)\b(?:hashlib\.md5|hashlib\.sha1)\b",
                "Medium",
                "MD5 and SHA-1 hashing algorithms are cryptographically broken and prone to collision attacks.",
                "Upgrade to secure algorithms like bcrypt, Argon2, or SHA-256 for data integrity and password hashing.",
                [".py"]
            ),
            (
                "Insecure CORS Config (Wildcard)",
                r"(?i)origins\s*=\s*['\"]\*(?:['\"]|\b)|cors\s*.*allow_origins\s*=\s*\[\s*['\"]\*(?:['\"]|\b)",
                "Medium",
                "CORS settings allow access from any origin ('*'), opening the application to Cross-Origin exploits.",
                "Restrict allowed origins to specific trusted domains, especially for authenticated routes.",
                [".py", ".js", ".ts"]
            ),
            (
                "Insecure Debug Configuration",
                r"(?i)(?:debug\s*=\s*True|app\.config\[['\"]DEBUG['\"]\]\s*=\s*True)",
                "Medium",
                "Application is configured with debug mode enabled. In production, this can leak sensitive stack traces.",
                "Ensure debug mode is disabled in production environments. Control it via an environment variable.",
                [".py"]
            )
        ]

    def scan(self) -> List[Dict[str, Any]]:
        """Scans the repository folder and returns security findings."""
        findings = []

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv', '.venv', 'cache', '__pycache__')]
            
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, self.repo_path).replace(os.sep, '/')
                _, ext = os.path.splitext(file)
                ext = ext.lower()

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue

                content = "".join(lines)

                for rule_name, pattern, severity, desc, rec, allowed_exts in self.rules:
                    if ext not in allowed_exts and "*" not in allowed_exts:
                        continue
                    
                    if re.search(pattern, content):
                        for line_idx, line in enumerate(lines):
                            if re.search(pattern, line):
                                findings.append({
                                    "file_path": rel_path,
                                    "line_number": line_idx + 1,
                                    "vulnerability_type": rule_name,
                                    "severity": severity,
                                    "description": desc,
                                    "recommendation": rec,
                                    "code_snippet": line.strip()[:200]
                                })
        
        return findings
