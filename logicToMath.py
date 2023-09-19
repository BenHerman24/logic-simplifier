import json
import sympy as sym

varNameFix = "∆ˆ¨¥√©˙ç√∫˚˜¬˙¨ˆ¥¨˚"


def getLogicMathJson():
    logicToMath: dict[str, str]
    with open("logicMath.json") as f:
        logicMath: dict[str, str] = json.load(f)
        keyCharList = []
    for key in logicMath.keys():
        for char in key:
            if char not in keyCharList:
                keyCharList.append(char)
    for key in logicMath.keys():
        logicMath[key] = logicMath[key].replace("a", "a_" + varNameFix)
        logicMath[key] = logicMath[key].replace("b", "b_" + varNameFix)
    return logicMath, keyCharList


def getCodeText():
    with open("logic.txt") as f:
        return f.read()


def splitCodeText(keyCharList, codeText, logicToMath, i=0):
    code: list[tuple[str, bool]] = []
    values = []
    piece = ""
    isOperator = False
    while i < len(codeText):
        char = codeText[i]
        i += 1
        if char == " ":
            continue
        if char == ")":
            if len(piece) > 0:
                code.append((piece, isOperator))
                if piece not in logicToMath.keys():
                    values.append(piece)
            return code, values, i
        if char in keyCharList:
            if isOperator:
                if piece in logicToMath.keys():
                    code.append((piece, True))
                    piece = char
                else:
                    piece += char
            else:
                if len(piece) > 0:
                    values.append(piece)
                    code.append((piece, False))
                isOperator = True
                piece = char
        else:
            if isOperator:
                if len(piece) > 0:
                    code.append((piece, True))
                isOperator = False
                if char == "(":
                    piece, values2, i = splitCodeText(keyCharList, codeText, logicToMath, i)
                    values.extend(values2)
                    code.append(piece)
                    isOperator = True
                    piece = ""
                else:
                    piece = char
            else:
                if char == "(":
                    piece, values2, i = splitCodeText(keyCharList, codeText, logicToMath, i)
                    values.extend(values2)
                    code.append(piece)
                    isOperator = True
                    piece = ""
                else:
                    piece += char
    if len(piece) > 0:
        code.append((piece, isOperator))
        if piece not in logicToMath.keys():
            values.append(piece)
    if char == ")":
        return code, values, i
    return code, list(dict.fromkeys(values))


def groupCodeText(code: list):
    # pass 1
    i = 0
    while i < len(code):
        block = code[i]
        if type(block) == tuple and block[1] and block[0] == "~" and not len(code) == 2:
            nextBlock = code[i + 1]
            if type(nextBlock) == list:
                nextBlock = groupCodeText(nextBlock)
            code[i] = [block, nextBlock]
            del code[i + 1]
        if type(block) == list:
            code[i] = groupCodeText(block)
        i += 1
    return code


def makeMathCode(code, logicToMath):
    i = 0
    while i < len(code):
        block = code[i]
        if type(block) == tuple and block[1]:
            block = {"math": logicToMath[block[0]], "a": None, "b": None}
            if "a_" + varNameFix in block["math"]:
                a = code[i - 1]
                if type(a) == list:
                    block["a"] = makeMathCode(a, logicToMath)
                else:
                    block["a"] = a[0]
            if "b_" + varNameFix in block["math"]:
                b = code[i + 1]
                if type(b) == list:
                    block["b"] = makeMathCode(b, logicToMath)
                else:
                    block["b"] = b[0]
            return block
        i += 1
    return makeMathCode(code[0], logicToMath)


def mergeMathCode(code: (dict[str, (dict | str | None)] | str | None)):
    mathText = "("
    if type(code) == str:
        mathText += code
    else:
        equation = code["math"]
        if "a_" + varNameFix in equation:
            equation = equation.replace("a_" + varNameFix, mergeMathCode(code["a"]))
        if "b_" + varNameFix in equation:
            equation = equation.replace("b_" + varNameFix, mergeMathCode(code["b"]))
        mathText += equation
    mathText += ")"
    return mathText


def runEquation(math: str, inputs: dict[str, bool]):
    for key in inputs.keys():
        math = math.replace(key, str(int(inputs[key])))
    return eval(math) == 1


def makeTable(math: str, values: list):
    table: dict[str, list] = {}

    inputs: dict[str, bool] = {}
    for val in values:
        inputs[val] = True
        table[val] = []

    table["eq: " + math] = []

    for key in inputs.keys():
        table[key].append(inputs[key])
    table["eq: " + math].append(runEquation(math, inputs))

    while any(inputs.values()):
        for val in reversed(values):
            if not inputs[val]:
                inputs[val] = True
            else:
                inputs[val] = False
                break
        for key in inputs.keys():
            table[key].append(inputs[key])
        table["eq: " + math].append(runEquation(math, inputs))
    return table


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)


def simplify(math: str):
    math = str(sym.simplify(math, ratio=10, measure=count))
    oldMath = None
    while "**" in math and oldMath != math:
        oldMath = math
        indexes = list(find_all(math, "**"))
        for i in indexes:
            if math[i - 1] != ")":
                math = math.replace("**" + math[i + 2], "")
                break
        math = str(sym.simplify(math, ratio=10, measure=count))
        indexes = list(find_all(math, "**"))
        for i in indexes:
            if math[i - 1] != ")":
                math = math.replace("**" + math[i + 2], "")
                break
        math = str(sym.simplify(math, ratio=10))
    return math


def count(x):
    return 1 / sym.count_ops(x)


logicToMath, keyCharList = getLogicMathJson()
codeText = getCodeText()
code, values = splitCodeText(keyCharList, codeText, logicToMath)
code = groupCodeText(code)
mathCode = makeMathCode(code, logicToMath)
math = mergeMathCode(mathCode)
math = simplify(math)
table = makeTable(math, values)


def makeTableRowString(table: dict, index: int):
    row = ""
    for val in table.keys():
        if row != "":
            row += " | "
        row += str(table[val][index])
        if table[val][index]:
            row += " "
    return row


print(list(table.keys()))
for i in range(2 ** len(values)):
    print(makeTableRowString(table, i))
