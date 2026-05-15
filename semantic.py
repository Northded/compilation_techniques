import sys


class SymbolEntry:
    def __init__(self, name, typ, scope, declared_line=None, param_types=None, is_vararg=False):
        self.name = name
        self.typ = typ
        self.scope = scope
        self.declared = True
        self.initialized = False
        self.declared_line = declared_line
        self.param_types = param_types if param_types is not None else []
        self.is_vararg = is_vararg


class SymbolTable:
    def __init__(self):
        self._table = {}

    def declare(self, name, typ, scope, line=None, param_types=None, is_vararg=False):
        key = (name, scope)
        if key in self._table:
            raise SemanticError(
                f"Повторное объявление переменной '{name}' "
                f"в области видимости '{scope}'"
            )
        self._table[key] = SymbolEntry(name, typ, scope, line, param_types, is_vararg)

    def lookup(self, name, scope):
        if (name, scope) in self._table:
            return self._table[(name, scope)]
        if (name, 'global') in self._table:
            return self._table[(name, 'global')]
        return None

    def mark_initialized(self, name, scope):
        e = self.lookup(name, scope)
        if e:
            e.initialized = True

    def all_entries(self):
        return list(self._table.values())

    def print_table(self):
        entries = self.all_entries()
        if not entries:
            print("(таблица символов пуста)")
            return
        col = [18, 10, 14, 16, 16]
        header = (f"{'Имя':<{col[0]}} {'Тип':<{col[1]}} "
                  f"{'Область':<{col[2]}} {'Объявлена':<{col[3]}} {'Инициализирована':<{col[4]}}")
        print(header)
        print('-' * sum(col))
        for e in entries:
            init_str = 'да' if e.initialized else 'нет'
            print(f"{e.name:<{col[0]}} {e.typ:<{col[1]}} "
                  f"{e.scope:<{col[2]}} {'да':<{col[3]}} {init_str:<{col[4]}}")


class Triad:
    def __init__(self, num, op, arg1, arg2=None):
        self.num = num
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self):
        if self.arg2 is not None:
            return f"{self.num}) ({self.op}, {self.arg1}, {self.arg2})"
        return f"{self.num}) ({self.op}, {self.arg1})"


class TriadList:
    def __init__(self):
        self._list = []

    def add(self, op, arg1, arg2=None):
        t = Triad(len(self._list) + 1, op, arg1, arg2)
        self._list.append(t)
        return f"^{t.num}"

    def print_all(self):
        for t in self._list:
            print(t)

    def all(self):
        return self._list


class SemanticError(Exception):
    pass


def sem_error(msg):
    print(f"Семантическая ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


TYPE_COMPAT = {
    ('Int',   'Int'):   'Int',
    ('Float', 'Float'): 'Float',
    ('Int',   'Float'): 'Float',
    ('Float', 'Int'):   'Float',
    ('Bool',  'Bool'):  'Bool',
}


def kotlin_type(raw):
    mapping = {'Boolean': 'Bool', 'Double': 'Float', 'Long': 'Int'}
    return mapping.get(raw, raw)


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.triads = TriadList()
        self.current_scope = 'global'
        self.errors = []
        self.current_return_type = None
        self._register_builtins()

    def _register_builtins(self):
        builtins = [
            ('println', 'Unit', [], True),
            ('print', 'Unit', [], True),
            ('arrayOf', 'Array', [], True),
            ('listOf', 'List', [], True),
            ('setOf', 'Set', [], True),
            ('mapOf', 'Map', [], True),
            ('requireNotNull', 'Any', ['Unknown'], False),
            ('checkNotNull', 'Any', ['Unknown'], False),
        ]
        for name, ret_type, param_types, is_vararg in builtins:
            try:
                self.symbols.declare(name, ret_type, 'global',
                                     param_types=param_types, is_vararg=is_vararg)
                self.symbols.mark_initialized(name, 'global')
            except SemanticError:
                pass

    def error(self, msg, node=None):
        location = ""
        if node is not None and hasattr(node, 'attrs'):
            line = node.attrs.get('line')
            col = node.attrs.get('col')
            if line is not None and col is not None:
                location = f" в строке {line}, столбце {col}"
            elif line is not None:
                location = f" в строке {line}"
        if not location:
            if self.current_scope != 'global':
                location = f" в функции '{self.current_scope}'"
            if node is not None and hasattr(node, 'kind'):
                location += f" (узел: {node.kind})"
        full_msg = f"Семантическая ошибка{location}: {msg}"
        self.errors.append(full_msg)
        print(full_msg, file=sys.stderr)

    def analyze(self, ast):
        if ast.kind != 'Program':
            sem_error("Корень AST должен быть Program")
        for child in ast.children:
            if child.kind == 'FuncDecl':
                self.visit_func_decl(child)
        return self.symbols, self.triads

    def visit_func_decl(self, node):
        fname = node.attrs.get('name', '?')
        prev_scope = self.current_scope
        self.current_scope = fname
        ret_type = kotlin_type(node.attrs.get('return_type', 'Unknown'))
        param_types = []
        for child in node.children:
            if child.kind == 'ParamList':
                for param in child.children:
                    if param.kind == 'Param':
                        ptype = kotlin_type(param.attrs.get('type', 'Unknown'))
                        param_types.append(ptype)
        try:
            self.symbols.declare(fname, ret_type, 'global', param_types=param_types)
            self.symbols.mark_initialized(fname, 'global')
        except SemanticError as e:
            self.error(str(e), node=node)
        prev_return_type = self.current_return_type
        self.current_return_type = ret_type
        for child in node.children:
            if child.kind == 'ParamList':
                self.visit_param_list(child)
            elif child.kind == 'Block':
                self.visit_block(child)
        self.current_return_type = prev_return_type
        self.current_scope = prev_scope

    def visit_param_list(self, node):
        for child in node.children:
            if child.kind == 'Param':
                name = child.attrs.get('name', '?')
                typ = kotlin_type(child.attrs.get('type', 'Unknown'))
                try:
                    self.symbols.declare(name, typ, self.current_scope)
                    self.symbols.mark_initialized(name, self.current_scope)
                except SemanticError as e:
                    self.error(str(e), node=child)

    def visit_block(self, node):
        for child in node.children:
            self.visit_stmt(child)

    def visit_stmt(self, node):
        k = node.kind
        if k == 'VarDecl':
            self.visit_var_decl(node)
        elif k == 'AssignStmt':
            self.visit_assign(node)
        elif k == 'IncStmt':
            self.visit_inc(node)
        elif k == 'ReturnStmt':
            self.visit_return(node)
        elif k == 'IfStmt':
            self.visit_if(node)
        elif k == 'ForStmt':
            self.visit_for(node)
        elif k == 'WhileStmt':
            self.visit_while(node)
        elif k == 'ExprStmt':
            self.visit_expr(node.children[0] if node.children else node)
        elif k == 'BreakStmt':
            self.triads.add('break', '-')
        elif k == 'ContinueStmt':
            self.triads.add('continue', '-')
        else:
            if node.children:
                self.visit_block(node)

    def visit_var_decl(self, node):
        name = node.attrs.get('name', '?')
        typ_raw = node.attrs.get('type', None)
        typ = kotlin_type(typ_raw) if typ_raw else None
        init_ref = None
        init_type = None
        if node.children:
            init_ref, init_type = self.visit_expr(node.children[0])
        if typ is None:
            typ = init_type or 'Unknown'
        if typ and init_type and typ != 'Unknown' and init_type != 'Unknown':
            if not self._types_compatible(typ, init_type):
                self.error(
                    f"Несоответствие типов: переменная '{name}' имеет тип {typ}, "
                    f"но инициализируется значением типа {init_type}",
                    node=node
                )
        try:
            self.symbols.declare(name, typ, self.current_scope)
        except SemanticError as e:
            self.error(str(e), node=node)
        if init_ref is not None:
            self.symbols.mark_initialized(name, self.current_scope)
            self.triads.add(':=', name, init_ref)

    def visit_assign(self, node):
        target = node.attrs.get('target', '?')
        entry = self.symbols.lookup(target, self.current_scope)
        if entry is None:
            self.error(f"Переменная '{target}' используется без объявления", node=node)
            return
        if node.children:
            rhs_ref, rhs_type = self.visit_expr(node.children[0])
            if (entry.typ and rhs_type and
                    entry.typ != 'Unknown' and rhs_type != 'Unknown'):
                if not self._types_compatible(entry.typ, rhs_type):
                    self.error(
                        f"Несоответствие типов в присваивании: "
                        f"'{target}' имеет тип {entry.typ}, "
                        f"правая часть имеет тип {rhs_type}",
                        node=node
                    )
            self.symbols.mark_initialized(target, self.current_scope)
            self.triads.add(':=', target, rhs_ref)

    def visit_inc(self, node):
        target = node.attrs.get('target', '?')
        op = node.attrs.get('op', '++')
        entry = self.symbols.lookup(target, self.current_scope)
        if entry is None:
            self.error(f"Переменная '{target}' используется без объявления", node=node)
            return
        if entry.typ not in ('Int', 'Float', 'Unknown'):
            self.error(
                f"Оператор '{op}' недопустим для типа {entry.typ} "
                f"(переменная '{target}')",
                node=node
            )
        ref = self.triads.add(op, target)
        self.triads.add(':=', target, ref)

    def visit_return(self, node):
        if node.children:
            ref, expr_type = self.visit_expr(node.children[0])
            if self.current_return_type and expr_type != 'Unknown':
                if not self._types_compatible(self.current_return_type, expr_type):
                    self.error(
                        f"Несоответствие типов возврата: функция должна вернуть "
                        f"{self.current_return_type}, а выражение имеет тип {expr_type}",
                        node=node
                    )
            self.triads.add('return', ref)
        else:
            if self.current_return_type not in (None, 'Unknown', 'Unit'):
                self.error(
                    f"Функция должна вернуть {self.current_return_type}, "
                    f"но используется return без значения",
                    node=node
                )
            self.triads.add('return', '-')

    def visit_if(self, node):
        for child in node.children:
            if child.kind == 'Condition':
                cond_ref, cond_type = self.visit_expr(child)
                if cond_type in ('Int', 'Float'):
                    cond_type = 'Bool'
                if cond_type not in ('Bool', 'Unknown'):
                    self.error(
                        f"Условие должно иметь тип Bool, а имеет {cond_type}",
                        node=child
                    )
                self.triads.add('if', cond_ref)
            elif child.kind in ('ThenBlock', 'Block'):
                self.visit_block(child)
            elif child.kind == 'ElseBlock':
                self.triads.add('else', '-')
                self.visit_block(child)

    def visit_for(self, node):
        var = node.attrs.get('var', '?')
        try:
            self.symbols.declare(var, 'Int', self.current_scope)
            self.symbols.mark_initialized(var, self.current_scope)
        except SemanticError:
            pass
        start_ref = end_ref = '?'
        for child in node.children:
            if child.kind == 'RangeStart':
                start_ref, start_type = self.visit_expr(child)
                if start_type not in ('Int', 'Float', 'Unknown'):
                    self.error(
                        f"Начало диапазона должно быть числом, а имеет тип {start_type}",
                        node=child
                    )
            elif child.kind == 'RangeEnd':
                end_ref, end_type = self.visit_expr(child)
                if end_type not in ('Int', 'Float', 'Unknown'):
                    self.error(
                        f"Конец диапазона должен быть числом, а имеет тип {end_type}",
                        node=child
                    )
            elif child.kind == 'Block':
                self.triads.add('for', var, f"{start_ref}..{end_ref}")
                self.visit_block(child)
                self.triads.add('end_for', var)

    def visit_while(self, node):
        for child in node.children:
            if child.kind == 'Condition':
                cond_ref, cond_type = self.visit_expr(child)
                if cond_type in ('Int', 'Float'):
                    cond_type = 'Bool'
                if cond_type not in ('Bool', 'Unknown'):
                    self.error(
                        f"Условие цикла должно иметь тип Bool, а имеет {cond_type}",
                        node=child
                    )
                self.triads.add('while', cond_ref)
            elif child.kind == 'Block':
                self.visit_block(child)
                self.triads.add('end_while', '-')

    def visit_expr(self, node):
        k = node.kind

        if k == 'Literal':
            typ = self._literal_type(node.attrs.get('type', ''))
            return node.attrs.get('value', '?'), typ

        if k == 'Identifier':
            name = node.attrs.get('name', '?')
            entry = self.symbols.lookup(name, self.current_scope)
            if entry is None:
                self.error(f"Переменная '{name}' используется без объявления", node=node)
                return name, 'Unknown'
            if not entry.initialized and entry.typ != 'Unknown':
                self.error(f"Переменная '{name}' используется до инициализации", node=node)
            return name, entry.typ

        if k == 'BinaryExpr':
            op = node.attrs.get('op', '?')
            left = node.children[0] if len(node.children) > 0 else None
            right = node.children[1] if len(node.children) > 1 else None
            l_ref, l_type = self.visit_expr(left) if left else ('?', 'Unknown')
            r_ref, r_type = self.visit_expr(right) if right else ('?', 'Unknown')
            res_type = self._result_type(op, l_type, r_type)
            if res_type == 'Unknown':
                op_lower = op.lower()
                if op_lower in ('<', '>', '<=', '>=', '==', '!=', 'lt', 'gt', 'le', 'ge', 'eq', 'ne'):
                    res_type = 'Bool'
                else:
                    self.error(
                        f"Несовместимые типы в операции {op}: {l_type} и {r_type}",
                        node=node
                    )
            ref = self.triads.add(op, l_ref, r_ref)
            return ref, res_type

        if k == 'CallExpr':
            func = node.attrs.get('func', '?')
            func_entry = self.symbols.lookup(func, 'global')
            if func_entry is None:
                self.error(f"Функция '{func}' не объявлена", node=node)
                return '?', 'Unknown'
            args = []
            arg_types = []
            for child in node.children:
                if child.kind == 'ArgList':
                    for arg in child.children:
                        ref, arg_type = self.visit_expr(arg)
                        args.append(ref)
                        arg_types.append(arg_type)
            if not func_entry.is_vararg:
                expected_param_count = len(func_entry.param_types)
                actual_arg_count = len(args)
                if expected_param_count != actual_arg_count:
                    self.error(
                        f"Функция '{func}' ожидает {expected_param_count} аргумент(ов), "
                        f"а передано {actual_arg_count}",
                        node=node
                    )
                else:
                    for i, (arg_type, expected_type) in enumerate(zip(arg_types, func_entry.param_types)):
                        if not self._types_compatible(expected_type, arg_type):
                            self.error(
                                f"Аргумент {i+1} функции '{func}' должен иметь тип {expected_type}, "
                                f"а имеет {arg_type}",
                                node=node
                            )
            arg_str = ', '.join(args) if args else '-'
            ref = self.triads.add('call', func, arg_str)
            return ref, func_entry.typ

        if node.children:
            return self.visit_expr(node.children[0])

        return '?', 'Unknown'

    def _literal_type(self, token_type):
        return {
            'CONSTANT_INT':    'Int',
            'CONSTANT_FLOAT':  'Float',
            'CONSTANT_STRING': 'String',
            'CONSTANT_BOOL':   'Bool',
        }.get(token_type, 'Unknown')

    def _types_compatible(self, t1, t2):
        if t1 == 'Unknown' or t2 == 'Unknown':
            return True
        if t1 == t2:
            return True
        return t1 in ('Int', 'Float') and t2 in ('Int', 'Float')

    def _result_type(self, op, t1, t2):
        op_upper = op.upper()
        comparison_ops = (
            '&&', '||', '>', '<', '>=', '<=', '==', '!=',
            'EQ', 'NE', 'LT', 'LE', 'GT', 'GE', 'AND', 'OR'
        )
        if op_upper in comparison_ops:
            return 'Bool'
        return TYPE_COMPAT.get((t1, t2), TYPE_COMPAT.get((t2, t1), 'Unknown'))


def analyze(ast):
    sa = SemanticAnalyzer()
    symbols, triads = sa.analyze(ast)
    if sa.errors:
        print(f"\nОбнаружено ошибок: {len(sa.errors)}", file=sys.stderr)
    return symbols, triads, sa.errors


if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from parser import parse_tokens

    lines = sys.stdin.read().splitlines()
    tokens = []
    for line in lines:
        if '|' not in line or line.startswith('-') or line.startswith('Лексема'):
            continue
        parts = line.split('|')
        if len(parts) == 2:
            v = parts[0].strip()
            t = parts[1].strip()
            if v and t:
                tokens.append((t, v))

    ast = parse_tokens(tokens)

    print("=== Семантический анализ ===\n")
    symbols, triads, errors = analyze(ast)

    print("Таблица символов:")
    symbols.print_table()

    if errors:
        print(f"\nОбнаружено семантических ошибок: {len(errors)}")
        for e in errors:
            print(f"  • {e}")
    else:
        print("\nСемантический анализ завершён успешно. Ошибок не найдено.")

    print("\nПоследовательность триад:")
    triads.print_all()