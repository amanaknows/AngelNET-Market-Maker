import re, random, statistics, time

# =========================
# 🔹 OPCODE MAP
# =========================
OPCODES = {
    "PUSH": 10,
    "ADD": 20,
    "SUB": 21,
    "STORE": 30,
    "LOAD": 31,
    "JMP": 40,
    "JZ": 41,
    "SELF_MOD": 50,
    "RAND": 60,
    "HALT": 99,
    "SEND": 70,       # Custom VM opcodes
    "BROADCAST": 71
}

# =========================
# 🔹 LEXER
# =========================
def tokenize(code):
    tokens=[]
    for line in code.splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        tokens.append(re.split(r"\s+", line))
    return tokens

# =========================
# 🔹 AST NODE CLASSES
# =========================
class Node: pass

class Assign(Node):
