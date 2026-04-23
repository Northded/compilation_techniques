import sys
from collections import defaultdict

KEYWORDS = {"fun", "val", "var", "if", "else", "for", "while", "return", "in"}
BOOL_CONSTS = {"true", "false"}
OPERATORS_2 = {"&&", "||", "++", "--", "==", "!=", "<=", ">=", ".."}
OPERATORS_1 = set("+-*/%=<>!")
DELIMITERS = set("(){}[];,:")

def error(msg: str, line: int) -> None:
    print(f"Лексическая ошибка на строке {line}: {msg}", file=sys.stderr)
    sys.exit(1)

def tokenize(source: str) -> list[tuple[str, str, int]]:
    tokens = []
    i = 0
    chars = list(source)
    line = 1

    while i < len(chars):
        ch = chars[i]

        if ch == '\n':
            line += 1
            i += 1
            continue
        if ch in ' \t\r':
            i += 1
            continue

        if ch == '"':
            s = '"'
            i += 1
            while i < len(chars) and chars[i] != '"':
                if chars[i] == '\n':
                    error("Незакрытый строковый литерал", line)
                s += chars[i]
                i += 1
            if i >= len(chars):
                error("Незакрытый строковый литерал", line)
            s += '"'
            i += 1
            tokens.append(("CONSTANT_STRING", s, line))
            continue

        if ch.isdigit():
            num = ""
            dots = 0
            while i < len(chars) and (chars[i].isdigit() or chars[i] == '.'):
                if chars[i] == '.':
                    if i + 1 < len(chars) and chars[i + 1] == '.':
                        break
                    dots += 1
                    if dots > 1:
                        error(f"Некорректное число: две точки в '{num}'", line)
                num += chars[i]
                i += 1
            if i < len(chars) and chars[i].isalpha():
                error(f"Идентификатор начинается с цифры: '{num}{chars[i]}' — "
                      f"идентификаторы должны начинаться с буквы или _", line)
            if (i < len(chars) and chars[i] == ','
                    and i + 1 < len(chars) and chars[i + 1].isdigit()):
                error(f"Некорректное число: запятая не является разделителем "
                      f"дробной части в '{num},'. Используйте точку.", line)
            ttype = "CONSTANT_FLOAT" if dots == 1 else "CONSTANT_INT"
            tokens.append((ttype, num, line))
            continue

        if ch.isalpha() or ch == '_':
            word = ""
            while i < len(chars) and (chars[i].isalnum() or chars[i] == '_'):
                word += chars[i]
                i += 1
            if word in BOOL_CONSTS:
                ttype = "CONSTANT_BOOL"
            elif word in KEYWORDS:
                ttype = "KEYWORD"
            else:
                ttype = "IDENTIFIER"
            tokens.append((ttype, word, line))
            continue

        two = "".join(chars[i:i + 2])
        if two in OPERATORS_2:
            tokens.append(("OPERATOR", two, line))
            i += 2
            continue

        if ch in OPERATORS_1:
            tokens.append(("OPERATOR", ch, line))
            i += 1
            continue

        if ch in DELIMITERS:
            tokens.append(("DELIMITER", ch, line))
            i += 1
            continue

        error(f"Недопустимый символ: '{ch}'", line)

    return tokens


def check_lonely_tokens(tokens: list[tuple[str, str, int]]) -> None:
    by_line = defaultdict(list)
    for ttype, val, line in tokens:
        by_line[line].append((ttype, val, line))

    for line, line_tokens in by_line.items():
        if len(line_tokens) == 1:
            ttype, val, ln = line_tokens[0]
            if val in ('}', ')', '{', '(', 'else'):
                continue
            error(f"Одиночный токен '{val}' — выражение не является полным", ln)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python lexer.py <файл>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding='utf-8') as f:
        source = f.read()

    tokens = tokenize(source)
    check_lonely_tokens(tokens)

    clean = [(t, v) for t, v, _ in tokens]

    print(f"{'Лексема':<25} | Тип")
    print("-" * 45)
    for ttype, val in clean:
        print(f"{val:<25} | {ttype}")

    seq = ", ".join(f"({t}, {v})" for t, v in clean)
    print(f"\n[{seq}]")

    print(f"\nЛексический анализ завершён успешно. Обнаружено {len(clean)} токенов. Ошибок не найдено.")