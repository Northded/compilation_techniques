import sys


class ASTNode:
    def __init__(self, kind, **attrs):
        self.kind = kind
        self.attrs = attrs
        self.children = []

    def add(self, child):
        self.children.append(child)
        return self


def print_ast(node, prefix="", last=True):
    connector = "└── " if last else "├── "
    line = prefix + connector + node.kind
    if node.attrs:
        line += "  [" + ", ".join(f"{k}: {v}" for k, v in node.attrs.items()) + "]"
    print(line)
    child_prefix = prefix + ("    " if last else "│   ")
    for i, child in enumerate(node.children):
        print_ast(child, child_prefix, i == len(node.children) - 1)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.declared = {}
        self.functions = {}
        self.in_loop = 0
        self.in_func = False

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def peek_type(self): return self.current()[0]
    def peek_val(self):  return self.current()[1]

    def advance(self):
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, ttype, tval=None):
        t, v = self.current()
        if t != ttype or (tval is not None and v != tval):
            want = f"'{tval}'" if tval else ttype
            self.error(f"Ожидался {want}, получен '{v}' ({t})")
        return self.advance()

    def match(self, ttype, tval=None):
        t, v = self.current()
        return t == ttype and (tval is None or v == tval)

    def error(self, msg):
        t, v = self.current()
        print(f"Синтаксическая ошибка [позиция {self.pos}]: {msg}. "
              f"Текущий токен: '{v}' ({t})", file=sys.stderr)
        sys.exit(1)

    def parse_program(self):
        i = 0
        while i < len(self.tokens):
            if self.tokens[i] == ("KEYWORD", "fun") and i + 1 < len(self.tokens):
                fname = self.tokens[i + 1][1]
                count = 0
                j = i + 2
                if j < len(self.tokens) and self.tokens[j] == ("DELIMITER", "("):
                    j += 1
                    depth = 1
                    while j < len(self.tokens) and depth > 0:
                        if self.tokens[j] == ("DELIMITER", "("):   depth += 1
                        elif self.tokens[j] == ("DELIMITER", ")"): depth -= 1
                        elif self.tokens[j][1] == ":" and depth == 1: count += 1
                        j += 1
                self.functions[fname] = count
            i += 1

        node = ASTNode("Program")
        while self.peek_type() != "EOF":
            node.add(self.parse_func_decl())
        return node

    def parse_func_decl(self):
        self.expect("KEYWORD", "fun")
        name = self.expect("IDENTIFIER")[1]
        node = ASTNode("FuncDecl", name=name)

        self.expect("DELIMITER", "(")
        self.in_func = True
        node.add(self.parse_param_list())
        self.expect("DELIMITER", ")")

        if self.match("DELIMITER", ":"):
            self.advance()
            node.attrs["return_type"] = self.parse_type()

        if not self.match("DELIMITER", "{"):
            _, v = self.current()
            self.error(f"Функция '{name}' не имеет тела — ожидался '{{', получен '{v}'")

        node.add(self.parse_block())
        self.in_func = False
        return node

    def parse_param_list(self):
        node = ASTNode("ParamList")
        if self.match("DELIMITER", ")"):
            return node
        node.add(self.parse_param())
        while self.match("DELIMITER", ","):
            self.advance()
            node.add(self.parse_param())
        return node

    def parse_param(self):
        name = self.expect("IDENTIFIER")[1]
        self.expect("DELIMITER", ":")
        ptype = self.parse_type()
        self.declared[name] = True
        return ASTNode("Param", name=name, type=ptype)

    def parse_type(self):
        if self.peek_type() != "IDENTIFIER":
            self.error("Ожидался тип (идентификатор)")
        return self.advance()[1]

    def parse_block(self):
        self.expect("DELIMITER", "{")
        node = ASTNode("Block")
        while not self.match("DELIMITER", "}"):
            if self.peek_type() == "EOF":
                self.error("Незакрытый блок: ожидался '}'")
            node.add(self.parse_stmt())
        self.expect("DELIMITER", "}")
        return node

    def parse_stmt(self):
        t, v = self.current()

        if t == "KEYWORD":
            if v in ("val", "var"): return self.parse_var_decl()
            if v == "return":       return self.parse_return_stmt()
            if v == "if":           return self.parse_if_stmt()
            if v == "for":          return self.parse_for_stmt()
            if v == "while":        return self.parse_while_stmt()
            if v == "break":        return self.parse_break_stmt()
            if v == "continue":     return self.parse_continue_stmt()

        if t == "IDENTIFIER":
            nxt = self.tokens[self.pos + 1][1] if self.pos + 1 < len(self.tokens) else ""
            if nxt == "=":          return self.parse_assign_stmt()
            if nxt in ("++", "--"): return self.parse_inc_stmt()
            if nxt == "(":          return self.parse_expr_stmt()
            self.error(f"Неожиданный токен '{v}' — ожидался оператор или вызов функции")
        self.error(f"Неожиданный токен '{v}' ({t}) — не является началом оператора")

    def parse_var_decl(self):
        kw = self.advance()[1]
        name = self.expect("IDENTIFIER")[1]
        node = ASTNode("VarDecl", keyword=kw, name=name)

        if self.match("DELIMITER", ":"):
            self.advance()
            node.attrs["type"] = self.parse_type()

        if self.match("OPERATOR", "="):
            self.advance()
            node.add(self.parse_expr())

        if name in self.declared:
            self.error(f"Переменная '{name}' уже объявлена")
        self.declared[name] = True
        return node

    def parse_assign_stmt(self):
        name = self.advance()[1]
        if name not in self.declared:
            self.error(f"Переменная '{name}' используется без объявления")
        self.expect("OPERATOR", "=")
        node = ASTNode("AssignStmt", target=name)
        node.add(self.parse_expr())
        return node

    def parse_inc_stmt(self):
        name = self.advance()[1]
        if name not in self.declared:
            self.error(f"Переменная '{name}' используется без объявления")
        op = self.advance()[1]
        return ASTNode("IncStmt", target=name, op=op)

    def parse_return_stmt(self):
        if not self.in_func:
            self.error("Оператор 'return' используется вне функции")
        self.expect("KEYWORD", "return")
        node = ASTNode("ReturnStmt")
        node.add(self.parse_expr())
        return node

    def parse_break_stmt(self):
        if self.in_loop == 0:
            self.error("Оператор 'break' используется вне цикла")
        self.advance()
        return ASTNode("BreakStmt")

    def parse_continue_stmt(self):
        if self.in_loop == 0:
            self.error("Оператор 'continue' используется вне цикла")
        self.advance()
        return ASTNode("ContinueStmt")

    def parse_if_stmt(self):
        self.expect("KEYWORD", "if")
        self.expect("DELIMITER", "(")
        node = ASTNode("IfStmt")
        cond = self.parse_expr()
        cond.kind = "Condition"
        node.add(cond)
        self.expect("DELIMITER", ")")
        tb = self.parse_block()
        tb.kind = "ThenBlock"
        node.add(tb)
        if self.match("KEYWORD", "else"):
            self.advance()
            eb = self.parse_block()
            eb.kind = "ElseBlock"
            node.add(eb)
        return node

    def parse_for_stmt(self):
        self.expect("KEYWORD", "for")
        self.expect("DELIMITER", "(")
        var = self.expect("IDENTIFIER")[1]
        self.expect("KEYWORD", "in")
        node = ASTNode("ForStmt", var=var)
        s = self.parse_expr()
        s.kind = "RangeStart"
        node.add(s)
        self.expect("OPERATOR", "..")
        e = self.parse_expr()
        e.kind = "RangeEnd"
        node.add(e)
        self.expect("DELIMITER", ")")
        self.declared[var] = True
        self.in_loop += 1
        node.add(self.parse_block())
        self.in_loop -= 1
        return node

    def parse_while_stmt(self):
        self.expect("KEYWORD", "while")
        self.expect("DELIMITER", "(")
        node = ASTNode("WhileStmt")
        cond = self.parse_expr()
        cond.kind = "Condition"
        node.add(cond)
        self.expect("DELIMITER", ")")
        self.in_loop += 1
        node.add(self.parse_block())
        self.in_loop -= 1
        return node

    def parse_expr_stmt(self):
        node = ASTNode("ExprStmt")
        node.add(self.parse_expr())
        return node

    def parse_expr(self):
        left = self.parse_primary()
        while self.peek_type() == "OPERATOR" and self.peek_val() not in ("++", "--", ".."):
            op = self.advance()[1]
            right = self.parse_primary()
            node = ASTNode("BinaryExpr", op=op)
            node.add(left)
            node.add(right)
            left = node
        return left

    def parse_primary(self):
        t, v = self.current()

        if t == "IDENTIFIER":
            self.advance()
            if self.match("DELIMITER", "("):
                self.advance()
                node = ASTNode("CallExpr", func=v)
                args = self.parse_arg_list()
                node.add(args)
                self.expect("DELIMITER", ")")
                if v in self.functions:
                    exp = self.functions[v]
                    got = len(args.children)
                    if exp != got:
                        self.error(f"Функция '{v}' ожидает {exp} аргумент(ов), передано {got}")
                return node
            if v not in self.declared:
                self.error(f"Переменная '{v}' используется без объявления")
            return ASTNode("Identifier", name=v)

        if t in ("CONSTANT_INT", "CONSTANT_FLOAT", "CONSTANT_STRING", "CONSTANT_BOOL"):
            self.advance()
            return ASTNode("Literal", type=t, value=v)

        if t == "DELIMITER" and v == "(":
            self.advance()
            node = self.parse_expr()
            self.expect("DELIMITER", ")")
            return node

        self.error(f"Ожидалось выражение, получен '{v}' ({t})")

    def parse_arg_list(self):
        node = ASTNode("ArgList")
        if self.match("DELIMITER", ")"):
            return node
        node.add(self.parse_expr())
        while self.match("DELIMITER", ","):
            self.advance()
            node.add(self.parse_expr())
        return node

def parse_tokens(token_list):
    parser = Parser(token_list)
    ast = parser.parse_program()
    if parser.peek_type() != "EOF":
        t, v = parser.current()
        print(f"Синтаксическая ошибка: лишние токены после конца программы. "
              f"Первый лишний: '{v}' ({t})", file=sys.stderr)
        sys.exit(1)
    return ast


if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    tokens = []
    for line in lines:
        if "|" not in line or line.startswith("-") or line.startswith("Лексема"):
            continue
        parts = line.split("|")
        if len(parts) == 2:
            v = parts[0].strip()
            t = parts[1].strip()
            if v and t:
                tokens.append((t, v))

    ast = parse_tokens(tokens)
    print_ast(ast, "", True)
    print("\nСинтаксический анализ завершён успешно. Ошибок не найдено.")