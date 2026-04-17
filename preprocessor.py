import re
import sys


def check_invalid_chars(source: str) -> None:
    for i, ch in enumerate(source):
        if ord(ch) < 32 and ch not in ('\t', '\n', '\r'):
            print(f"Ошибка: недопустимый символ с кодом {ord(ch)} на позиции {i}",
                  file=sys.stderr)
            sys.exit(1)


def check_unclosed_comments(source: str) -> None:
    open_count = source.count("/*")
    close_count = source.count("*/")
    if open_count > close_count:
        print(f"Ошибка: незакрытый многострочный комментарий "
              f"(найдено {open_count} '/*' и {close_count} '*/')", file=sys.stderr)
        sys.exit(1)
    if close_count > open_count:
        print(f"Ошибка: лишний символ закрытия '*/' "
              f"(найдено {open_count} '/*' и {close_count} '*/')", file=sys.stderr)
        sys.exit(1)


def protect_strings(source: str) -> tuple[str, list[str]]:
    strings = []
    result = []
    i = 0
    chars = list(source)

    while i < len(chars):
        if chars[i] == '"':
            s = '"'
            i += 1
            while i < len(chars) and chars[i] != '"':
                if chars[i] == '\n':
                    break
                s += chars[i]
                i += 1
            if i < len(chars) and chars[i] == '"':
                s += '"'
                i += 1
            placeholder = f'\x00STR{len(strings)}\x00'
            strings.append(s)
            result.append(placeholder)
        else:
            result.append(chars[i])
            i += 1

    return ''.join(result), strings


def restore_strings(source: str, strings: list[str]) -> str:
    for idx, s in enumerate(strings):
        source = source.replace(f'\x00STR{idx}\x00', s)
    return source


def preprocess(source: str) -> str:
    check_invalid_chars(source)
    source, strings = protect_strings(source)
    check_unclosed_comments(source)

    source = re.sub(r'(?s)/\*.*?\*/', '', source)

    source = re.sub(r'(?m)//.*$', '', source)

    source = restore_strings(source, strings)

    source = re.sub(r'(?m)^[ \t]+|[ \t]+$', '', source)

    source = re.sub(r'[ \t]+', ' ', source)

    while re.search(r'\n\s*\n', source):
        source = re.sub(r'\n\s*\n', '\n', source)

    return source.strip()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python preprocessor.py <файл>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding='utf-8') as f:
        source = f.read()

    result = preprocess(source)
    print(result)
    print("Ошибок не выявлено.", file=sys.stderr)