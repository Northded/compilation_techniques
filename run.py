import sys
from preprocessor import preprocess
from lexer import tokenize, check_lonely_tokens
from parser import parse_tokens, print_ast
from semantic import analyze

if len(sys.argv) < 2:
    print("Использование: python run.py <файл>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding='utf-8') as f:
    source = f.read()

print("=== Препроцессор ===")
cleaned = preprocess(source)
print(cleaned)

print("\n=== Лексер ===")
tokens = tokenize(cleaned)
check_lonely_tokens(tokens)
clean = [(t, v) for t, v, _ in tokens]
print(f"{'Лексема':<25} | Тип")
print("-" * 45)
for ttype, val in clean:
    print(f"{val:<25} | {ttype}")
seq = ", ".join(f"({t}, {v})" for t, v in clean)
print(f"\n[{seq}]")
print(f"\nОбнаружено {len(clean)} токенов. Ошибок не найдено.")

print("\n=== Синтаксический анализатор ===")
ast = parse_tokens(clean)
print_ast(ast, "", True)
print("\nОшибок не найдено.")

print("\n=== Семантический анализатор ===")
symbols, triads, errors = analyze(ast)

print("\nТаблица символов:")
symbols.print_table()

if errors:
    print(f"\nОбнаружено ошибок: {len(errors)}", file=sys.stderr)
    sys.exit(1)

print("\nОшибок не найдено.")
print("\nПоследовательность триад:")
triads.print_all()