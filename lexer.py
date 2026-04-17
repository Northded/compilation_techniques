import sys

KEYWORDS   = {"fun", "val", "var", "if", "else", "for", "while", "return", "in"}
BOOL_CONSTS = {"true", "false"}
OPERATORS_2 = {"&&", "||", "++", "--", "==", "!=", "<=", ">=", ".."}
OPERATORS_1 = set("+-*/%=<>!")
DELIMITERS  = set("(){}[];,:")

def error(msg):
    print(f"Лексическая ошибка: {msg}", file=sys.stderr)
    sys.exit(1)

def tokenize(source):
    tokens = []
    i = 0
    chars = list(source)

    while i < len(chars):
        ch = chars[i]

        if ch in ' \t\n\r':
            i += 1
            continue

        if ch == '"':
            s = '"'
            i += 1
            while i < len(chars) and chars[i] != '"':
                if chars[i] == '\n':
                    error("Незакрытый строковый литерал")
                s += chars[i]
                i += 1
            if i >= len(chars):
                error("Незакрытый строковый литерал")
            s += '"'
            i += 1
            tokens.append(("CONSTANT_STRING", s))
            continue

        # Числовая константа
        if ch.isdigit():
            num = ""
            dots = 0
            while i < len(chars) and (chars[i].isdigit() or chars[i] == '.'):
                if chars[i] == '.':
                    if i + 1 < len(chars) and chars[i + 1] == '.':
                        break
                    dots += 1
                    if dots > 1:
                        error(f"Некорректное число: две точки в '{num}'")
                num += chars[i]
                i += 1
            if i < len(chars) and chars[i].isalpha():
                error(f"Идентификатор начинается с цифры: '{num}{chars[i]}' — идентификаторы должны начинаться с буквы или _")
            ttype = "CONSTANT_FLOAT" if dots == 1 else "CONSTANT_INT"
            tokens.append((ttype, num))
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
            tokens.append((ttype, word))
            continue

        two = "".join(chars[i:i + 2])
        if two in OPERATORS_2:
            tokens.append(("OPERATOR", two))
            i += 2
            continue

        if ch in OPERATORS_1:
            tokens.append(("OPERATOR", ch))
            i += 1
            continue

        if ch in DELIMITERS:
            tokens.append(("DELIMITER", ch))
            i += 1
            continue

        # Всё остальное — ошибка
        error(f"Недопустимый символ: '{ch}'")

    return tokens

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python lexer.py <файл>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding='utf-8') as f:
        source = f.read()

    tokens = tokenize(source)

    print(f"{'Лексема':<25} | Тип")
    print("-" * 45)
    for ttype, val in tokens:
        print(f"{val:<25} | {ttype}")

    seq = ", ".join(f"({t}, {v})" for t, v in tokens)
    print(f"\n[{seq}]")

    print(f"\nЛексический анализ завершён успешно. Обнаружено {len(tokens)} токенов. Ошибок не найдено.")
