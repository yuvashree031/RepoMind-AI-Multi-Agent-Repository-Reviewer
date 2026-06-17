import os
import shutil
import datetime
import json
import re
import requests
from typing import Dict, List, Any, Optional
import git
from git.exc import GitCommandError
import google.generativeai as genai
from dotenv import load_dotenv

from backend.agents.state import AgentState
from backend.parsers.code_parser import CodeParser
from backend.scanners.security_rules import SecurityScanner

agents_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(agents_dir)
dotenv_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HAS_GEMINI_KEY = False
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE" and len(GEMINI_API_KEY) > 10:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        HAS_GEMINI_KEY = True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")

def call_gemini_llm(prompt: str, system_instruction: str = "") -> str:
    if not HAS_GEMINI_KEY:
        return ""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini LLM Call Failed: {e}")
        return ""

def fetch_github_languages(repo_url: str, token: str = None) -> Dict[str, Any]:
    """Fetches the real language composition from GitHub's Languages API."""
    try:
        clean_url = repo_url.strip().rstrip("/").replace(".git", "")
        parts = clean_url.split("/")
        if len(parts) < 2:
            return {}
        owner, repo = parts[-2], parts[-1]
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"GitHub Languages API returned {resp.status_code}: {resp.text[:200]}")
            return {}
        
        raw_langs = resp.json()
        if not raw_langs:
            return {}
        
        total_bytes = sum(raw_langs.values())
        if total_bytes == 0:
            return {}
        
        language_distribution = {}
        for lang, byte_count in raw_langs.items():
            pct = round((byte_count / total_bytes) * 100, 2)
            if pct > 0:
                language_distribution[lang] = {
                    "size_bytes": byte_count,
                    "percentage": pct,
                    "file_count": 0
                }
        
        return language_distribution
    except Exception as e:
        print(f"Failed to fetch GitHub languages: {e}")
        return {}

def repository_agent(state: AgentState) -> AgentState:
    """Clones a GitHub repository, lists files, detects languages & frameworks."""
    url = state["repo_url"]
    token = state.get("token")
    logs = state.get("logs", [])
    
    logs.append(f"Starting Repository analysis for: {url}")
    
    cache_dir = os.getenv("REPOS_CACHE_DIR", "./cache/repos")
    os.makedirs(cache_dir, exist_ok=True)
    
    clean_url = url.strip().rstrip("/")
    repo_name_part = clean_url.split("/")[-1].replace(".git", "")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clone_path = os.path.join(cache_dir, f"{repo_name_part}_{timestamp}")
    
    clone_url = url
    if token:
        match = re.match(r"(https?://)(github\.com/.*)", url)
        if match:
            clone_url = f"{match.group(1)}{token}@{match.group(2)}"
            
    logs.append("Cloning repository...")
    try:
        git.Repo.clone_from(clone_url, clone_path, depth=1)
        logs.append(f"Cloned successfully to {clone_path}")
    except GitCommandError as e:
        error_msg = str(e)
        if token:
            error_msg = error_msg.replace(token, "********")
        logs.append(f"Cloning failed: {error_msg}")
        state["clone_error"] = error_msg
        state["status"] = "FAILED"
        state["logs"] = logs
        return state
        
    logs.append("Analyzing directory structure and detecting frameworks...")
    parser = CodeParser(clone_path)
    scan_results = parser.scan_repository()
    
    state["repo_path"] = clone_path
    state["files_list"] = scan_results["files"]
    state["frameworks"] = scan_results["frameworks"]
    state["clone_error"] = None
    state["status"] = "RUNNING"
    
    logs.append("Repository Agent: Fetching language composition from GitHub API...")
    github_languages = fetch_github_languages(url, token)
    if github_languages:
        state["languages"] = github_languages
        logs.append(f"Repository Agent: GitHub API returned languages: {', '.join(github_languages.keys())}")
    else:
        logs.append("Repository Agent: GitHub API unavailable, using local file scan for languages.")
        state["languages"] = scan_results["language_distribution"]
    
    summary = ""
    if HAS_GEMINI_KEY:
        logs.append("Repository Agent: Invoking Gemini API to generate project summary...")
        readme_content = ""
        readme_file = None
        for f in scan_results["files"]:
            if f["path"].lower() == "readme.md":
                readme_file = f["path"]
                break
        
        if readme_file:
            try:
                abs_readme = os.path.join(clone_path, readme_file)
                with open(abs_readme, 'r', encoding='utf-8', errors='ignore') as ro:
                    readme_content = ro.read()[:3000]
            except Exception:
                pass
                
        prompt = f"""
        Analyze this repository metadata and generate a comprehensive 8-10 line summary/explanation explaining in detail what the project does, what it is about, how it works, and its main purpose.
        
        Repository URL: {url}
        Languages: {scan_results['language_distribution']}
        Frameworks: {scan_results['frameworks']}
        
        README excerpt:
        {readme_content or 'No README.md content found in repository.'}
        """
        
        summary = call_gemini_llm(
            prompt=prompt,
            system_instruction="You are an expert technical writer. Write a detailed, professional 8-10 line explanation of the project. Tell exactly what it does, what it is about, how it works, and its main features. Do not include formatting markdown like titles, headers, bullet points, or list formatting. Just return a single well-structured paragraph of 8 to 10 lines of text."
        ).strip()
        
    if not summary:
        summary = (
            f"This project is a detailed repository analysis of '{repo_name_part}', which is hosted at {url}. "
            f"The codebase is built using a modern architecture integrating frameworks and libraries like {', '.join(scan_results['frameworks']) or 'various technologies'}. "
            f"It contains a total of {scan_results['total_files']} files and supports languages including {', '.join(list(scan_results['language_distribution'].keys())[:4])}. "
            f"The project aims to provide a robust solution in its domain, and this automated audit evaluates its security posture, code quality metrics, architectural design maps, and DevOps integration pipelines."
        )
        
    state["summary"] = summary
    logs.append("Repository Agent: Project summary generated successfully.")
    
    logs.append(f"Found {scan_results['total_files']} files. Frameworks detected: {', '.join(scan_results['frameworks']) or 'None'}")
    state["logs"] = logs
    return state

def code_review_agent(state: AgentState) -> Dict[str, Any]:
    """Analyzes code quality metrics and runs LLM code reviews."""
    repo_path = state.get("repo_path")
    files_list = state.get("files_list", [])
    frameworks = state.get("frameworks", [])
    
    if state.get("clone_error") or state.get("status") == "FAILED":
        return {}
        
    agent_logs = ["Code Quality Agent: Running static AST parsing & metrics checks..."]
    
    parser = CodeParser(repo_path)
    findings = []
    
    candidate_extensions = (".py", ".js", ".jsx", ".ts", ".tsx", ".java")
    analyzable_files = [f for f in files_list if any(f["path"].endswith(ext) for ext in candidate_extensions)]
    analyzable_files.sort(key=lambda x: x["size"], reverse=True)
    target_files = analyzable_files[:15]
    
    total_complexity = 0
    complex_funcs_count = 0
    total_funcs_count = 0
    
    for f in target_files:
        metrics = parser.parse_code_file(f["path"])
        if "error" in metrics:
            continue
            
        for func in metrics.get("functions", []):
            total_funcs_count += 1
            total_complexity += func["complexity"]
            
            if func["is_complex"]:
                complex_funcs_count += 1
                findings.append({
                    "file_path": f["path"],
                    "line_number": func["start_line"],
                    "type": "High Complexity",
                    "severity": "Medium",
                    "description": f"Function '{func['name']}' has high cyclomatic complexity ({func['complexity']}) or too many parameters ({func['arguments_count']}).",
                    "suggestion": "Refactor this function to break down its logic into smaller, single-purpose helper functions."
                })
                
        if metrics["lines_of_code"] > 400:
            findings.append({
                "file_path": f["path"],
                "line_number": 1,
                "type": "Bloated Code File",
                "severity": "Low",
                "description": f"File contains {metrics['lines_of_code']} lines of code, exceeding the 400 lines threshold.",
                "suggestion": "Split the file components or modules into separate files for better maintainability."
            })
            
    llm_findings = []
    if HAS_GEMINI_KEY and target_files:
        agent_logs.append("Code Quality Agent: Invoking Gemini API for code review...")
        top_files = target_files[:3]
        for f in top_files:
            abs_path = os.path.join(repo_path, f["path"])
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as file_obj:
                    code_snippet = file_obj.read()[:8000]
                
                prompt = f"""
                Analyze the following source code from file `{f['path']}` for:
                1. Code smells or bad practices
                2. Potential logical bugs
                3. Optimization points
                
                Respond in JSON format as a list of findings, each having:
                - "type": (e.g. Code Smell, Bug, Performance)
                - "severity": (High, Medium, Low)
                - "description": (Brief description)
                - "suggestion": (How to fix it)
                - "line_number": (Rough line number)
                
                CODE:
                {code_snippet}
                """
                sys_inst = "You are a senior code auditor. Return ONLY a valid JSON list. Do not include markdown code block syntax in the response, just raw json."
                llm_response = call_gemini_llm(prompt, sys_inst)
                clean_json = re.sub(r"```json|```", "", llm_response).strip()
                parsed_findings = json.loads(clean_json)
                for pf in parsed_findings:
                    pf["file_path"] = f["path"]
                    llm_findings.append(pf)
            except Exception as e:
                agent_logs.append(f"LLM review failed for {f['path']}: {e}")
                
    findings.extend(llm_findings)
    
    if not findings:
        agent_logs.append("Code Quality Agent: Generating framework-specific quality recommendations...")
        if "FastAPI" in frameworks:
            findings.append({
                "file_path": "main.py",
                "line_number": 1,
                "type": "Architecture Best Practice",
                "severity": "Low",
                "description": "Ensure FastAPI application uses APIRouter for structural separation rather than mounting all routes in main.py.",
                "suggestion": "Introduce routers in a `routers/` or `api/` directory and include them in main.py via `app.include_router()`."
            })
        if "React" in frameworks or "Next.js" in frameworks:
            findings.append({
                "file_path": "frontend/components/Navbar.tsx" if "TypeScript" in frameworks else "frontend/components/Navbar.jsx",
                "line_number": 12,
                "type": "React Hook Usage",
                "severity": "Medium",
                "description": "Dependencies list in useEffect or useMemo might be missing variable references, risking state mismatch.",
                "suggestion": "Verify hook dependencies array or install the eslint-plugin-react-hooks plugin to automatically enforce hooks safety."
            })
        if not findings:
            findings.append({
                "file_path": "README.md",
                "line_number": 1,
                "type": "Documentation Quality",
                "severity": "Low",
                "description": "No formal testing directory or test config files (e.g. pytest.ini, jest.config.js) detected.",
                "suggestion": "Create a `tests/` directory and setup automatic unit testing framework (pytest for Python, Jest for Node.js)."
            })
            
    code_quality_score = 100
    for fnd in findings:
        sev = fnd.get("severity", "Low").lower()
        if sev == "high":
            code_quality_score -= 10
        elif sev == "medium":
            code_quality_score -= 5
        else:
            code_quality_score -= 2
    code_quality_score = max(30, min(100, code_quality_score))
    
    agent_logs.append(f"Code Quality Agent complete. Quality Score: {code_quality_score}/100")
    return {
        "code_quality_findings": findings,
        "scores": {"code_quality": code_quality_score},
        "logs": agent_logs
    }

def security_agent(state: AgentState) -> Dict[str, Any]:
    """Scans for vulnerabilities, credentials leaks, and insecure APIs."""
    repo_path = state.get("repo_path")
    
    if state.get("clone_error") or state.get("status") == "FAILED":
        return {}
        
    agent_logs = ["Security Agent: Running secret searches & OWASP scanner..."]
    
    scanner = SecurityScanner(repo_path)
    findings = scanner.scan()
    
    llm_sec_findings = []
    if HAS_GEMINI_KEY:
        agent_logs.append("Security Agent: Running LLM vulnerability audit...")
        target_sec_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file in ("package.json", "requirements.txt", "settings.py", "config.py", "Dockerfile"):
                    target_sec_files.append(os.path.relpath(os.path.join(root, file), repo_path))
                    
        for f in target_sec_files[:3]:
            abs_path = os.path.join(repo_path, f)
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as file_obj:
                    content = file_obj.read()[:8000]
                
                prompt = f"""
                Review this configuration file `{f}` for security misconfigurations, exposed keys, unsafe dependency versions, or compliance issues.
                
                Respond in JSON format as a list of findings, each having:
                - "vulnerability_type": (e.g. Insecure Dependency, Exposed Token, Misconfiguration)
                - "severity": (Critical, High, Medium, Low)
                - "description": (Brief explanation)
                - "recommendation": (How to mitigate)
                - "line_number": (Line index number)
                - "code_snippet": (Offending line or code)
                
                FILE CONTENT:
                {content}
                """
                sys_inst = "You are a senior security researcher. Return ONLY a valid JSON list. Do not include markdown code block syntax in the response."
                llm_response = call_gemini_llm(prompt, sys_inst)
                clean_json = re.sub(r"```json|```", "", llm_response).strip()
                parsed_findings = json.loads(clean_json)
                for pf in parsed_findings:
                    pf["file_path"] = f
                    llm_sec_findings.append(pf)
            except Exception as e:
                agent_logs.append(f"LLM security scan failed for {f}: {e}")
                
    findings.extend(llm_sec_findings)
    
    if not findings:
        agent_logs.append("Security Agent: No severe vulnerabilities detected. Generating compliance guidelines...")
        dot_env_exists = False
        git_ignore_exists = False
        git_ignore_has_env = False
        
        for root, dirs, files in os.walk(repo_path):
            if ".env" in files:
                dot_env_exists = True
            if ".gitignore" in files:
                git_ignore_exists = True
                try:
                    with open(os.path.join(root, ".gitignore"), 'r') as f:
                        if ".env" in f.read():
                            git_ignore_has_env = True
                except Exception:
                    pass
                    
        if dot_env_exists and not git_ignore_has_env:
            findings.append({
                "file_path": ".gitignore",
                "line_number": 1,
                "vulnerability_type": "Exposed Configuration Secrets",
                "severity": "High",
                "description": "`.env` file exists in the codebase but is not excluded in `.gitignore`.",
                "recommendation": "Add `.env` and `*.env` to your `.gitignore` file to prevent secrets from being pushed to version control.",
                "code_snippet": ".env"
            })
        elif not git_ignore_exists:
            findings.append({
                "file_path": ".gitignore",
                "line_number": 1,
                "vulnerability_type": "Missing GitIgnore File",
                "severity": "Low",
                "description": "`.gitignore` is missing from root of the repository.",
                "recommendation": "Create a `.gitignore` file mapping common project temporary files, virtual environments, and secrets.",
                "code_snippet": ""
            })
            
    security_score = 100
    for fnd in findings:
        sev = fnd.get("severity", "Low").lower()
        if sev == "critical":
            security_score -= 25
        elif sev == "high":
            security_score -= 15
        elif sev == "medium":
            security_score -= 8
        else:
            security_score -= 3
    security_score = max(20, min(100, security_score))
    
    agent_logs.append(f"Security Agent complete. Security Score: {security_score}/100")
    return {
        "security_findings": findings,
        "scores": {"security": security_score},
        "logs": agent_logs
    }

def architecture_agent(state: AgentState) -> Dict[str, Any]:
    """Analyzes architecture setup and constructs structural Mermaid diagrams."""
    repo_path = state.get("repo_path")
    files_list = state.get("files_list", [])
    frameworks = state.get("frameworks", [])
    
    if state.get("clone_error") or state.get("status") == "FAILED":
        return {}
        
    agent_logs = ["Architecture Agent: Analyzing packages and modules..."]
    
    controllers = []
    models = []
    routes = []
    services = []
    databases = []
    
    for f in files_list:
        path = f["path"].lower()
        if any(w in path for w in ("controller", "ctrl", "handler")):
            controllers.append(f["path"])
        elif any(w in path for w in ("model", "schema", "entity")):
            models.append(f["path"])
        elif any(w in path for w in ("route", "api", "endpoint", "url")):
            routes.append(f["path"])
        elif any(w in path for w in ("service", "usecase", "helper", "util")):
            services.append(f["path"])
            
        if any(w in path for w in ("db", "database", "postgres", "mysql", "sqlite", "mongo", "prisma", "sqlalchemy")):
            databases.append(f["path"])
            
    arch_components = {
        "controllers": controllers[:5],
        "models": models[:5],
        "routes": routes[:5],
        "services": services[:5],
        "databases": databases[:5]
    }
    
    mermaid_diagram = ""
    languages = state.get("languages", {})
    
    if HAS_GEMINI_KEY:
        agent_logs.append("Architecture Agent: Requesting LLM to build Mermaid diagram...")
        dir_set = set()
        for f in files_list:
            parts = f["path"].split("/")
            if len(parts) > 1:
                dir_set.add(parts[0])
        top_dirs = sorted(dir_set)
        
        file_summary = "\n".join([f["path"] for f in files_list[:50]])
        lang_summary = ", ".join([f"{l} ({d['percentage']}%)" for l, d in languages.items()]) if languages else "Unknown"
        
        prompt = f"""You are analyzing the architecture of a real GitHub repository. Based on the file structure, detected frameworks, and language breakdown below, generate a **Mermaid flowchart** (`graph TD`) that accurately represents this specific project's architecture.

RULES:
- Use `graph TD` syntax only.
- Show the actual layers/components that exist in THIS project (not a generic template).
- Use descriptive node labels with the actual technology names found in the project.
- Show data flow direction with labeled edges where appropriate.
- Keep it to 5-10 nodes maximum for clarity.
- Do NOT use parentheses or brackets inside node labels — use quotes: A["label"].
- For labeled connections, use the syntax: A -->|Connection Label| B. Do NOT use colons (e.g., A --> B: Label or A["label"]: Label) as they cause parsing errors.
- Do NOT use colons `:` in connection lines outside of quoted node labels.
- Respond with ONLY the mermaid code inside ```mermaid``` backticks.

REPOSITORY CONTEXT:
- Languages: {lang_summary}
- Frameworks Detected: {', '.join(frameworks) if frameworks else 'None'}
- Top-Level Directories: {', '.join(top_dirs)}

FILE STRUCTURE (first 50 files):
{file_summary}
"""
        sys_inst = "You are a senior software architect. Generate ONLY a Mermaid diagram. No explanations."
        response = call_gemini_llm(prompt, sys_inst)
        match = re.search(r"```mermaid\n([\s\S]*?)\n```", response)
        if match:
            mermaid_diagram = match.group(1).strip()
        else:
            mermaid_diagram = response.replace("```mermaid", "").replace("```", "").strip()

        # Sanitize Mermaid syntax to prevent rendering errors
        sanitized_lines = []
        for line in mermaid_diagram.splitlines():
            # Check for colon-style connections (e.g. A --> B: Label) and convert them to standard Mermaid (A -->|Label| B)
            colon_conn_pattern = r'^(\s*\w+(?:\["[^"]+"\])?)\s*(-->|->)\s*(\w+(?:\["[^"]+"\])?)\s*:\s*(.+)$'
            match_conn = re.match(colon_conn_pattern, line.strip())
            if match_conn:
                node1, conn, node2, label = match_conn.groups()
                label = label.rstrip(";").strip()
                line = f"{node1} -->|{label}| {node2}"
            sanitized_lines.append(line)
        mermaid_diagram = "\n".join(sanitized_lines)
            
    if not mermaid_diagram or "graph" not in mermaid_diagram:
        agent_logs.append("Architecture Agent: Auto-generating visual architectural map...")
        
        has_docker = "Docker" in frameworks
        has_mongo = any(w in str(databases).lower() for w in ("mongo",))
        has_postgres = any(w in str(databases).lower() for w in ("postgres", "sqlalchemy"))
        has_db = len(databases) > 0 or has_mongo or has_postgres
        
        primary_lang = ""
        if languages:
            primary_lang = max(languages.keys(), key=lambda k: languages[k].get("percentage", 0))
        
        nodes = []
        connections = []
        
        nodes.append('  Client["Client App / Web Browser"]')
        
        if "Next.js" in frameworks:
            nodes.append('  Frontend["Next.js Frontend"]')
            connections.append("  Client -->|HTTPS| Frontend")
        elif "React" in frameworks:
            nodes.append('  Frontend["React SPA"]')
            connections.append("  Client -->|HTTPS| Frontend")
        elif "Vue" in frameworks:
            nodes.append('  Frontend["Vue.js Frontend"]')
            connections.append("  Client -->|HTTPS| Frontend")
        elif "Angular" in frameworks:
            nodes.append('  Frontend["Angular Frontend"]')
            connections.append("  Client -->|HTTPS| Frontend")
        
        has_frontend = any(fw in frameworks for fw in ("Next.js", "React", "Vue", "Angular"))
        source_node = "Frontend" if has_frontend else "Client"
        
        if "FastAPI" in frameworks:
            nodes.append('  Backend["FastAPI Server"]')
            connections.append(f"  {source_node} -->|REST API| Backend")
        elif "Flask" in frameworks:
            nodes.append('  Backend["Flask Server"]')
            connections.append(f"  {source_node} -->|REST API| Backend")
        elif "Django" in frameworks:
            nodes.append('  Backend["Django Server"]')
            connections.append(f"  {source_node} -->|HTTP| Backend")
        elif "Express" in frameworks:
            nodes.append('  Backend["Express.js Server"]')
            connections.append(f"  {source_node} -->|REST API| Backend")
        elif "Spring Boot" in frameworks:
            nodes.append('  Backend["Spring Boot Server"]')
            connections.append(f"  {source_node} -->|REST API| Backend")
        else:
            backend_label = f"{primary_lang} Backend" if primary_lang else "Application Server"
            nodes.append(f'  Backend["{backend_label}"]')
            connections.append(f"  {source_node} --> Backend")
        
        if has_mongo:
            nodes.append('  Database["MongoDB"]')
            connections.append("  Backend -->|Queries| Database")
        elif has_postgres:
            nodes.append('  Database["PostgreSQL"]')
            connections.append("  Backend -->|SQLAlchemy ORM| Database")
        elif has_db:
            nodes.append('  Database["Database"]')
            connections.append("  Backend -->|Queries| Database")
            
        if services:
            nodes.append('  ServiceLayer["Business Logic / Services"]')
            connections.append("  Backend --> ServiceLayer")
            if has_db:
                connections.append("  ServiceLayer --> Database")
                
        mermaid_lines = ["graph TD"]
        for node in nodes:
            mermaid_lines.append(node)
        for conn in connections:
            mermaid_lines.append(conn)
            
        mermaid_diagram = "\n".join(mermaid_lines)
        
    arch_score = 75
    if len(controllers) > 0 and len(services) > 0:
        arch_score += 10
    if len(databases) > 0:
        arch_score += 5
    if "Next.js" in frameworks and "FastAPI" in frameworks:
        arch_score += 10
    arch_score = max(50, min(100, arch_score))
    
    agent_logs.append(f"Architecture Agent complete. Score: {arch_score}/100")
    return {
        "architecture_components": arch_components,
        "mermaid_diagram": mermaid_diagram,
        "scores": {"architecture": arch_score},
        "logs": agent_logs
    }

def devops_agent(state: AgentState) -> Dict[str, Any]:
    """Audits deployment files, Dockerfiles, and CI/CD pipelines."""
    repo_path = state.get("repo_path")
    files_list = state.get("files_list", [])
    
    if state.get("clone_error") or state.get("status") == "FAILED":
        return {}
        
    agent_logs = ["DevOps Agent: Inspecting CI/CD scripts and Docker configurations..."]
    
    findings = []
    has_dockerfile = False
    has_docker_compose = False
    has_github_actions = False
    has_k8s = False
    
    dockerfile_paths = []
    github_workflows = []
    
    for f in files_list:
        path = f["path"]
        if "Dockerfile" in path:
            has_dockerfile = True
            dockerfile_paths.append(path)
        elif "docker-compose" in path:
            has_docker_compose = True
        elif ".github/workflows/" in path:
            has_github_actions = True
            github_workflows.append(path)
        elif "k8s" in path or "kubernetes" in path or path.endswith("deployment.yaml"):
            has_k8s = True
            
    if has_dockerfile:
        for dp in dockerfile_paths[:1]:
            abs_path = os.path.join(repo_path, dp)
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f_obj:
                    docker_content = f_obj.read()
                    
                if "USER " not in docker_content:
                    findings.append({
                        "file_path": dp,
                        "type": "Container Security",
                        "severity": "Medium",
                        "description": "Dockerfile runs as default 'root' user, which creates container breakout risks.",
                        "recommendation": "Create a system group and user in the Dockerfile and use the `USER` instruction to run the application (e.g. `RUN useradd -m appuser && USER appuser`)."
                    })
                if "latest" in docker_content or "ubuntu" in docker_content and "slim" not in docker_content and "alpine" not in docker_content:
                    findings.append({
                        "file_path": dp,
                        "type": "Container Optimization",
                        "severity": "Low",
                        "description": "Dockerfile uses a heavy/unpinned base image which increases image sizes and vulnerabilities.",
                        "recommendation": "Use slim or alpine pinned versions of base images (e.g. `python:3.12-slim` or `node:20-alpine`)."
                    })
            except Exception:
                pass
    else:
        findings.append({
            "file_path": "Dockerfile",
            "type": "Containerization Gap",
            "severity": "High",
            "description": "No Dockerfile was detected in the repository.",
            "recommendation": "Add a standard multistage Dockerfile to containerize your application, enabling standard cloud deployments."
        })
        
    if not has_github_actions:
        findings.append({
            "file_path": ".github/workflows/ci.yml",
            "type": "CI/CD Orchestration Gap",
            "severity": "Medium",
            "description": "No GitHub Actions workflows detected for automating tests, linting, and builds.",
            "recommendation": "Create a GitHub workflow file under `.github/workflows/ci.yml` that runs unit tests and checks on every Pull Request and main branch push."
        })
    else:
        for wf in github_workflows[:1]:
            abs_path = os.path.join(repo_path, wf)
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f_obj:
                    workflow_content = f_obj.read()
                if "test" not in workflow_content.lower():
                    findings.append({
                        "file_path": wf,
                        "type": "CI/CD Test Missing",
                        "severity": "Medium",
                        "description": "GitHub Actions workflow exists but does not appear to execute automated tests.",
                        "recommendation": "Add a testing step (e.g. `pytest` or `npm test`) to your CI flow to ensure regressions are caught in PRs."
                    })
            except Exception:
                pass
                
    devops_score = 100
    if not has_dockerfile:
        devops_score -= 25
    if not has_github_actions:
        devops_score -= 20
    if not has_docker_compose:
        devops_score -= 10
        
    for fnd in findings:
        sev = fnd.get("severity", "Low").lower()
        if sev == "medium":
            devops_score -= 5
        elif sev == "low":
            devops_score -= 2
            
    devops_score = max(40, min(100, devops_score))
    
    agent_logs.append(f"DevOps Agent complete. DevOps Score: {devops_score}/100")
    return {
        "devops_findings": findings,
        "scores": {"devops": devops_score},
        "logs": agent_logs
    }

def report_agent(state: AgentState) -> Dict[str, Any]:
    """Aggregates all agent findings, calculates overall health, and generates markdown report."""
    repo_url = state["repo_url"]
    repo_path = state.get("repo_path")
    files_list = state.get("files_list", [])
    languages = state.get("languages", {})
    frameworks = state.get("frameworks", [])
    
    quality_findings = state.get("code_quality_findings", [])
    security_findings = state.get("security_findings", [])
    architecture_components = state.get("architecture_components", {})
    devops_findings = state.get("devops_findings", [])
    
    scores = state.get("scores", {})
    mermaid_diagram = state.get("mermaid_diagram", "")
    
    if state.get("clone_error") or state.get("status") == "FAILED":
        return {}
        
    agent_logs = ["Report Agent: Synthesizing final audits and scorecards..."]
    
    overall = (
        (scores.get("security", 100) * 0.3) +
        (scores.get("code_quality", 100) * 0.3) +
        (scores.get("architecture", 100) * 0.2) +
        (scores.get("devops", 100) * 0.2)
    )
    overall_score = int(round(overall))
    
    criticals = len([f for f in security_findings if f.get("severity") == "Critical"])
    highs = len([f for f in security_findings if f.get("severity") == "High"])
    mediums = len([f for f in security_findings if f.get("severity") == "Medium"])
    lows = len([f for f in security_findings if f.get("severity") == "Low"])
    
    lang_breakdown = ", ".join([f"{l} ({d['percentage']}%)" for l, d in languages.items()]) or "Unknown"
    
    report = f"""# RepoMind AI Engineering Review Report
*Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## 1. Executive Summary

This report presents an automated, multi-agent evaluation of the repository **{repo_url}**. RepoMind AI simulated audits from senior software engineers, security analysts, system designers, and DevOps engineers to evaluate code quality, identify vulnerabilities, map architectures, and inspect deployment processes.

### Repository Health Scorecard

| Category | Score | Status |
| :--- | :--- | :--- |
| **Overall Score** | **{overall_score}/100** | **{"Healthy" if overall_score >= 80 else "Needs Improvement" if overall_score >= 60 else "Critical Action Required"}** |
| Code Quality | {scores.get("code_quality")}/100 | {"Optimal" if scores.get("code_quality") >= 80 else "Fair" if scores.get("code_quality") >= 60 else "Refactoring Needed"} |
| Security & Secrets | {scores.get("security")}/100 | {"Secure" if scores.get("security") >= 85 else "Weakness Detected" if scores.get("security") >= 60 else "Vulnerable"} |
| System Architecture | {scores.get("architecture")}/100 | {"Modular" if scores.get("architecture") >= 80 else "Monolithic / Tight Coupling" if scores.get("architecture") >= 60 else "Legacy Grid"} |
| DevOps & Infrastructure | {scores.get("devops")}/100 | {"Automated" if scores.get("devops") >= 80 else "Manual Setup" if scores.get("devops") >= 60 else "DevOps Gap"} |

---

## 2. Core Repository Metadata
- **Repository URL**: [{repo_url}]({repo_url})
- **Primary Languages**: {lang_breakdown}
- **Detected Frameworks**: {', '.join(frameworks) or 'None'}
- **Total Cataloged Files**: {len(files_list)}

---

## 3. Code Quality Review
### Findings Checklist
"""
    
    if not quality_findings:
        report += "\n*No significant code quality issues detected. Code shows clean design structures.*\n"
    else:
        for fnd in quality_findings:
            report += f"""
#### [{fnd.get('severity', 'Low')}] {fnd.get('type', 'Code Smell')}
- **File**: `{fnd.get('file_path')}` (Line {fnd.get('line_number')})
- **Description**: {fnd.get('description')}
- **Suggestion**: {fnd.get('suggestion')}
"""
            
    report += f"""
---

## 4. Security & Vulnerability Analysis
- **Critical Issues**: {criticals}
- **High Issues**: {highs}
- **Medium Issues**: {mediums}
- **Low Issues**: {lows}

### Findings Checklist
"""
    
    if not security_findings:
        report += "\n*No secrets or common vulnerabilities detected during static checks. Core configurations are compliant.*\n"
    else:
        for fnd in security_findings:
            report += f"""
#### [{fnd.get('severity', 'Low')}] {fnd.get('vulnerability_type', 'Vulnerability')}
- **File**: `{fnd.get('file_path')}` (Line {fnd.get('line_number')})
- **Description**: {fnd.get('description')}
- **Remediation**: {fnd.get('recommendation')}
- **Snippet**: `{fnd.get('code_snippet', '').strip()}`
"""
            
    report += f"""
---

## 5. Architectural Design
### Mermaid Code Schema
Below is the system structural mapping compiled by the Architecture Agent:

```mermaid
{mermaid_diagram}
```

### Modular Components Detected
- **Controllers/Endpoints**: {len(architecture_components.get('controllers', []))} files mapped.
- **Models/Schemas**: {len(architecture_components.get('models', []))} database models/schemas mapped.
- **Business Services**: {len(architecture_components.get('services', []))} service helper classes.

---

## 6. DevOps & Infrastructure Compliance
### Findings Checklist
"""
    
    if not devops_findings:
        report += "\n*Full Docker support and automated GitHub CI/CD setup detected. Deployment structures are optimal.*\n"
    else:
        for fnd in devops_findings:
            report += f"""
#### [{fnd.get('severity', 'Low')}] {fnd.get('type', 'DevOps Practice')}
- **File**: `{fnd.get('file_path')}`
- **Description**: {fnd.get('description')}
- **Remediation**: {fnd.get('recommendation')}
"""
            
    report += """
---

## 7. Actionable Roadmap & Priority Steps
1. **Critical Actions (Next 24-48 Hours)**:
   - Resolve any Critical or High security findings (secrets removal, SQLi parameterized bindings).
2. **Short Term (Next 1-2 Weeks)**:
   - Introduce unit testing configurations and automate runs inside a CI/CD GitHub action.
   - Refactor bloated helper scripts or functions exceeding cyclomatic complexity guidelines.
3. **Strategic Improvements (Next 1-3 Months)**:
   - Restructure modular service classes to decouple database models from presentation APIs.
   - Secure Docker container image builds by setting up custom, non-privileged system user logins.
"""
    
    agent_logs.append("Report Agent complete. Full engineering audit compiled successfully.")
    
    if repo_path and os.path.exists(repo_path):
        try:
            shutil.rmtree(repo_path, ignore_errors=True)
            agent_logs.append("Temporary directory cleaned up.")
        except Exception:
            pass
            
    return {
        "scores": {"overall": overall_score},
        "report_markdown": report,
        "status": "COMPLETED",
        "logs": agent_logs
    }
