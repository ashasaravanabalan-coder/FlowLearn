"""Feature extraction shared by ML training and the Flask backend."""
import re

FEATURES = ["num_conditions", "loop_count", "function_usage", "code_length",
            "operators_used", "complexity_level", "max_nesting"]

_COND = re.compile(r"\b(if|elif|case)\b")
_LOOP = re.compile(r"\b(for|while)\b")
_FUNC = re.compile(r"^\s*(?:def\s+\w+|function\s+\w+)", re.M)
_OPS = re.compile(r"==|!=|<=|>=|&&|\|\||[+\-*/%<>=]")
_LOGIC = re.compile(r"&&|\|\||\b(and|or)\b")
_CONTROL = re.compile(r"\b(if|elif|else|for|while|switch)\b")


def _max_nesting(code):
    """Maximum depth of nested control blocks (functions are not counted)."""
    mx = 0
    if "{" in code:
        stack = []
        for line in code.splitlines():
            ctrl = bool(_CONTROL.search(line))
            for ch in line:
                if ch == "}" and stack:
                    stack.pop()
                elif ch == "{":
                    stack.append(ctrl)
                    mx = max(mx, sum(stack))
        return mx
    stack = []
    for line in code.splitlines():
        s = line.strip()
        if not s:
            continue
        indent = len(line) - len(line.lstrip())
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if s.endswith(":") and re.match(r"(def|if|elif|else|for|while|with|try|except)\b", s):
            stack.append((indent, not s.startswith("def")))
            mx = max(mx, sum(c for _, c in stack))
    return mx


def extract_features(code: str) -> dict:
    conditions = len(_COND.findall(code))
    loops = len(_LOOP.findall(code))
    functions = len(_FUNC.findall(code))
    complexity = 1 + conditions + loops + len(_LOGIC.findall(code))
    return {
        "num_conditions": conditions,
        "loop_count": loops,
        "function_usage": functions,
        "code_length": len([l for l in code.splitlines() if l.strip()]),
        "operators_used": len(_OPS.findall(code)),
        "complexity_level": complexity,
        "max_nesting": _max_nesting(code),
    }
