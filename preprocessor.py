import re
import sys

def check_unclosed_comments(source):
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

def check_invalid_chars(source):
    for i, ch in enumerate(source):
        if ord(ch) < 32 and ch not in ('\t', '\n', '\r'):
            print(f"Ошибка: недопустимый символ с кодом {ord(ch)} на позиции {i}",
                  file=sys.stderr)
            sys.exit(1)

def preprocess(source):
    check_invalid_chars(source)
    check_unclosed_comments(source)

    source = re.sub(r'(?s)/\*.*?\*/', '', source)

    source = re.sub(r'(?m)//.*$', '', source)

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
