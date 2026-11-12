"""Builds ML/dataset.csv: randomised code snippets labelled by logic type,
with numeric features extracted from each snippet (not typed by hand)."""
import random
import pandas as pd
from features import extract_features

random.seed(42)
NAMES = ["a", "b", "x", "y", "n", "total", "count", "num", "val", "score", "age", "price", "result"]
CMP = [">", "<", "==", "!=", ">=", "<="]
ARITH = ["+", "-", "*", "/", "%"]


def nm(): return random.choice(NAMES)
def cond():
    c = f"{nm()} {random.choice(CMP)} {random.randint(0, 99)}"
    if random.random() < 0.25:
        c += f" {random.choice(['and', 'or'])} {nm()} {random.choice(CMP)} {random.randint(0, 99)}"
    return c
def stmt():
    return random.choice([
        f"{nm()} = {nm()} {random.choice(ARITH)} {random.randint(1, 50)}",
        f"{nm()} = int(input())",
        f"print({nm()})",
        f"{nm()} = {random.randint(0, 100)}"])
def block(n, d):
    return ["    " * d + stmt() for _ in range(random.randint(1, n))]


def sequential():
    return "\n".join(block(random.randint(2, 9), 0))

def conditional():
    out = [f"if {cond()}:"] + block(2, 1)
    for _ in range(random.choice([0, 0, 1, 2])):
        out += [f"elif {cond()}:"] + block(2, 1)
    if random.random() < 0.7:
        out += ["else:"] + block(2, 1)
    return "\n".join(block(2, 0) + out)

def looping():
    out = []
    for _ in range(random.choice([1, 1, 2])):
        if random.random() < 0.5:
            out += [f"for {nm()} in range({random.randint(2, 20)}):"] + block(3, 1)
        else:
            out += [f"while {nm()} {random.choice(['<', '>', '!='])} {random.randint(1, 50)}:"] + block(3, 1)
    return "\n".join(block(2, 0) + out)

def nested():
    kind = random.choice(["ff", "fi", "wi", "iff", "fif"])
    if kind == "ff":
        out = [f"for i in range({random.randint(2, 9)}):", f"    for j in range({random.randint(2, 9)}):"] + block(2, 2)
    elif kind == "fi":
        out = [f"for i in range({random.randint(2, 9)}):", f"    if {cond()}:"] + block(2, 2)
    elif kind == "wi":
        out = [f"while {cond()}:", f"    if {cond()}:"] + block(2, 2) + ["    else:"] + block(1, 2)
    elif kind == "iff":
        out = [f"if {cond()}:", f"    if {cond()}:"] + block(2, 2) + ["else:"] + block(1, 1)
    else:
        out = [f"for i in range({random.randint(2, 9)}):", f"    if {cond()}:", "        for j in range(3):"] + block(1, 3)
    return "\n".join(block(1, 0) + out)

def function_based():
    name = random.choice(["add", "check", "compute", "process", "solve", "calc"])
    body = random.choice([block(3, 1), [f"    if {cond()}:", "        return 1", "    return 0"],
                          [f"    for i in range({random.randint(2, 9)}):"] + block(1, 2) + ["    return i"]])
    out = [f"def {name}({nm()}, {nm()}):"] + body
    out += [f"result = {name}({random.randint(0, 9)}, {random.randint(0, 9)})", "print(result)"]
    if random.random() < 0.4:
        out = out[:-2] + [f"def helper({nm()}):", "    return 1"] + out[-2:]
    return "\n".join(out)

GENERATORS = {"Sequential": sequential, "Conditional": conditional, "Looping": looping,
              "Nested": nested, "Function-Based": function_based}

if __name__ == "__main__":
    rows = []
    for label, gen in GENERATORS.items():
        for _ in range(300):
            code = gen()
            rows.append({"code": code, **extract_features(code), "label": label})
    df = pd.DataFrame(rows).sample(frac=1, random_state=1).reset_index(drop=True)
    df.to_csv("dataset.csv", index=False)
    print(df.label.value_counts())
