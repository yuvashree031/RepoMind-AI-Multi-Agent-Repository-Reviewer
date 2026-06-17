from typing import TypedDict, List, Dict, Any, Optional, Annotated

def merge_dict(existing: Dict[str, Any], new_val: Dict[str, Any]) -> Dict[str, Any]:
    if not existing:
        return new_val or {}
    if not new_val:
        return existing or {}
    return {**existing, **new_val}

def merge_list(existing: List[Any], new_val: List[Any]) -> List[Any]:
    if not existing:
        return new_val or []
    if not new_val:
        return existing or []
    combined = list(existing)
    for item in new_val:
        if item not in combined:
            combined.append(item)
    return combined

class AgentState(TypedDict):
    repo_url: str
    token: Optional[str]
    
    repo_path: str
    clone_error: Optional[str]
    files_list: List[Dict[str, Any]]
    languages: Dict[str, Any]
    frameworks: List[str]
    status: str
    
    code_quality_findings: List[Dict[str, Any]]
    security_findings: List[Dict[str, Any]]
    architecture_components: Dict[str, Any]
    devops_findings: List[Dict[str, Any]]
    
    scores: Annotated[Dict[str, int], merge_dict]
    
    mermaid_diagram: str
    report_markdown: str
    summary: str
    
    logs: Annotated[List[str], merge_list]
