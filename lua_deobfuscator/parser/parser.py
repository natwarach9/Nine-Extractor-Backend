from ..lexer.lexer import Token

class ASTNode:
    def __init__(self, children=None):
        self.children = children if children is not None else []

    def __repr__(self):
        return self.__class__.__name__

    def add_child(self, node):
        self.children.append(node)

class Program(ASTNode):
    def __init__(self, body):
        super().__init__(children=body)
        self.body = body

class Block(ASTNode):
    def __init__(self, statements):
        super().__init__(children=statements)
        self.statements = statements

class Statement(ASTNode):
    pass

class Expression(ASTNode):
    pass

class Identifier(Expression):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return f"Identifier('{self.name}')"

class Literal(Expression):
    def __init__(self, value, type):
        super().__init__()
        self.value = value
        self.type = type

    def __repr__(self):
        return f"Literal({self.type}, {repr(self.value)})";

class BinaryOperator(Expression):
    def __init__(self, left, operator, right):
        super().__init__([left, right])
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.operator}, {self.left}, {self.right})"

class UnaryOperator(Expression):
    def __init__(self, operator, operand):
        super().__init__([operand])
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.operator}, {self.operand})"

class FunctionCall(Statement, Expression):
    def __init__(self, base, args):
        super().__init__([base] + args)
        self.base = base # Can be Identifier or another FunctionCall
        self.args = args

    def __repr__(self):
        return f"FunctionCall({self.base}, Args: {self.args})"

class Assignment(Statement):
    def __init__(self, variables, values):
        super().__init__(variables + values)
        self.variables = variables # List of Identifier nodes
        self.values = values     # List of Expression nodes

    def __repr__(self):
        return f"Assignment(Vars: {self.variables}, Values: {self.values})"

class LocalAssignment(Assignment):
    def __repr__(self):
        return f"LocalAssignment(Vars: {self.variables}, Values: {self.values})"

class IfStatement(Statement):
    def __init__(self, condition, then_block, else_block=None, elseif_blocks=None):
        children = [condition, then_block] 
        if elseif_blocks: children.extend([b for cond,b in elseif_blocks])
        if else_block: children.append(else_block)
        super().__init__(children)
        self.condition = condition
        self.then_block = then_block
        self.elseif_blocks = elseif_blocks if elseif_blocks is not None else [] # list of (condition, block)
        self.else_block = else_block

    def __repr__(self):
        return f"IfStatement(Cond: {self.condition}, Then: {self.then_block}, ElseIfs: {len(self.elseif_blocks)}, Else: {self.else_block is not None})"

class WhileStatement(Statement):
    def __init__(self, condition, body):
        super().__init__([condition, body])
        self.condition = condition
        self.body = body

class ForNumericStatement(Statement):
    def __init__(self, var, start, end, step, body):
        super().__init__([var, start, end, step, body])
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.body = body

class ForGenericStatement(Statement):
    def __init__(self, vars, exprs, body):
        super().__init__(vars + exprs + [body])
        self.vars = vars
        self.exprs = exprs
        self.body = body

class FunctionDeclaration(Statement):
    def __init__(self, name, parameters, body, is_local=False):
        super().__init__([body])
        if name: self.children.append(name)
        self.name = name # Identifier or MemberExpression for global/table functions
        self.parameters = parameters # List of Identifier nodes
        self.body = body # Block node
        self.is_local = is_local

    def __repr__(self):
        return f"FunctionDeclaration(Name: {self.name}, Params: {[p.name for p in self.parameters]}, Local: {self.is_local})"

class ReturnStatement(Statement):
    def __init__(self, expressions):
        super().__init__(expressions)
        self.expressions = expressions # List of Expression nodes

class BreakStatement(Statement):
    pass

class RepeatUntilStatement(Statement):
    def __init__(self, body, condition):
        super().__init__([body, condition])
        self.body = body
        self.condition = condition

class DoBlock(Statement):
    def __init__(self, body):
        super().__init__([body])
        self.body = body

class TableConstructor(Expression):
    def __init__(self, fields):
        super().__init__(fields)
        self.fields = fields # List of TableField nodes

    def __repr__(self):
        return f"TableConstructor(Fields: {len(self.fields)})"

class TableField(ASTNode):
    def __init__(self, key, value, is_key_expr=False):
        children = [value]
        if key: children.append(key)
        super().__init__(children)
        self.key = key # Identifier or Expression or Literal
        self.value = value
        self.is_key_expr = is_key_expr # True if key is [expr]

    def __repr__(self):
        return f"TableField(Key: {self.key}, Value: {self.value})"

class MemberExpression(Expression):
    def __init__(self, base, identifier, is_colon=False, is_bracket=False):
        super().__init__([base, identifier])
        self.base = base
        self.identifier = identifier # Identifier or Expression for bracket access
        self.is_colon = is_colon # For obj:method() calls
        self.is_bracket = is_bracket # For obj[expr] access

    def __repr__(self):
        access_type = "." if not self.is_bracket else "[]"
        if self.is_colon: access_type = ":"
        return f"MemberExpression({self.base}{access_type}{self.identifier})"

class IndexExpression(MemberExpression):
    def __init__(self, base, index_expr):
        super().__init__(base, index_expr, is_bracket=True)
        self.index_expr = index_expr

    def __repr__(self):
        return f"IndexExpression({self.base}[{self.index_expr}])"

class VarargExpression(Expression):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "VarargExpression()"

class LabelStatement(Statement):
    def __init__(self, name):
        super().__init__()
        self.name = name # Identifier

    def __repr__(self):
        return f"LabelStatement({self.name})"

class GotoStatement(Statement):
    def __init__(self, label_name):
        super().__init__()
        self.label_name = label_name # Identifier

    def __repr__(self):
        return f"GotoStatement({self.label_name})"



class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = tokens[0] if tokens else None

        self.precedence = {
            "OR": 1,
            "AND": 2,
            "<" : 3, ">": 3, "<=": 3, ">=": 3, "~=": 3, "==": 3,
            "..": 4,
            "+": 5, "-": 5,
            "*": 6, "/": 6, "%" : 6, "//": 6,
            "UNARY": 7, # For unary operators like 'not', '-', '#' 
            "^": 8,
        }

    def _advance(self):
        self.current_token_index += 1
        self.current_token = self.tokens[self.current_token_index] if self.current_token_index < len(self.tokens) else None

    def _eat(self, token_type, value=None):
        if self.current_token and self.current_token.type == token_type:
            if value is None or self.current_token.value == value:
                token = self.current_token
                self._advance()
                return token
        self._error(f"Expected {token_type}" + (f" with value {value}" if value else ""))

    def _peek(self, offset=0):
        idx = self.current_token_index + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def _error(self, message):
        token_info = "EOF" if not self.current_token else f"'{self.current_token.value}' (Type: {self.current_token.type}) at Line {self.current_token.line}, Col {self.current_token.column}"
        raise SyntaxError(f"Parsing Error: {message} near {token_info}")

    def parse(self):
        return Program(self._parse_block())

    def _parse_block(self):
        statements = []
        while self.current_token and self.current_token.type not in ("END", "ELSE", "ELSEIF", "UNTIL", "EOF"):
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
            else:
                # Handle cases where _parse_statement might return None (e.g., empty semicolons)
                if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ";":
                    self._eat("PUNCTUATOR", ";") # consume optional semicolons
                else:
                    break # Should not happen if grammar is well-defined
        return Block(statements)

    def _parse_statement(self):
        if self.current_token is None: return None
        token_type = self.current_token.type
        token_value = self.current_token.value

        if token_type == "LOCAL":
            return self._parse_local_statement()
        elif token_type == "FUNCTION":
            return self._parse_function_declaration(is_local=False)
        elif token_type == "IF":
            return self._parse_if_statement()
        elif token_type == "WHILE":
            return self._parse_while_statement()
        elif token_type == "FOR":
            return self._parse_for_statement()
        elif token_type == "RETURN":
            return self._parse_return_statement()
        elif token_type == "BREAK":
            self._eat("BREAK")
            return BreakStatement()
        elif token_type == "REPEAT":
            return self._parse_repeat_until_statement()
        elif token_type == "DO":
            self._eat("DO")
            block = self._parse_block()
            self._eat("END")
            return DoBlock(block)
        elif token_type == "PUNCTUATOR" and token_value == "::":
            return self._parse_label_statement()
        elif token_type == "GOTO":
            return self._parse_goto_statement()
        
        # Try to parse as assignment or function call
        # This requires lookahead because var_list = expr_list and func_call(args) both start with an expression.
        # We'll parse the 'prefix expression' first and then decide.
        prefix_expr = self._parse_prefix_expression()

        if prefix_expr:
            next_token = self.current_token
            if next_token and (next_token.type == "PUNCTUATOR" and next_token.value == "=") or (next_token.type == "PUNCTUATOR" and next_token.value == "," and self._is_assignment_lookahead()):
                # This is an assignment statement
                variables = [prefix_expr] # First variable
                while self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
                    self._eat("PUNCTUATOR", ",")
                    variables.append(self._parse_prefix_expression()) # Subsequent variables
                
                self._eat("PUNCTUATOR", "=")
                values = self._parse_expression_list()
                return Assignment(variables, values)
            elif isinstance(prefix_expr, FunctionCall):
                return prefix_expr # It's a function call statement
            elif isinstance(prefix_expr, (Identifier, MemberExpression, IndexExpression)):
                # This could be a variable declaration without assignment, or a standalone identifier (which is not a statement)
                # For now, treat as an expression statement if not followed by assignment. 
                # Lua grammar states: `varlist = explist` | `functioncall`
                # So, a lone identifier or member expression isn't a statement unless it's a function call.
                # We will handle cases where a prefix_expr is an Identifier but not an assignment if we strictly follow Lua grammar.
                # For robustness, we'll allow an expression as a statement here, though strictly, Lua doesn't.
                # This needs refinement to match Lua's official grammar if strict adherence is required.
                # For now, if it's an Identifier and not part of an assignment/function call, it's ignored or handled by a higher rule.
                # For simplicity, if it's not a function call or assignment, we'll return None, implying no statement was parsed.
                return None
        
        # If nothing else matched, it might be an expression statement, but Lua only allows function calls as expression statements.
        # So, if we parsed something that wasn't a function call and not an assignment, it's not a valid statement on its own.
        return None # No statement parsed

    def _is_assignment_lookahead(self):
        # Look ahead to determine if it's an assignment or just an expression list
        # This is a simplification; a full Lua parser would need more robust lookahead or backtracking
        temp_index = self.current_token_index
        temp_token = self.current_token
        
        # Skip past identifiers and commas to find an '=' 
        while temp_token and (temp_token.type == "IDENTIFIER" or 
                               (temp_token.type == "PUNCTUATOR" and temp_token.value in (",", ".", ":", "["))):
            if temp_token.type == "PUNCTUATOR" and temp_token.value == "=":
                return True
            self._advance()
            temp_token = self.current_token
        
        # Reset position
        self.current_token_index = temp_index
        self.current_token = temp_token
        return False

    def _parse_local_statement(self):
        self._eat("LOCAL")
        if self.current_token.type == "FUNCTION":
            return self._parse_function_declaration(is_local=True)
        else:
            variables = [self._parse_identifier()] # Must be at least one local variable
            while self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
                self._eat("PUNCTUATOR", ",")
                variables.append(self._parse_identifier())

            values = []
            if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == "=":
                self._eat("PUNCTUATOR", "=")
                values = self._parse_expression_list()
            return LocalAssignment(variables, values)

    def _parse_function_declaration(self, is_local=False):
        self._eat("FUNCTION")
        name = None
        if not is_local:
            name = self._parse_function_name()
        elif self.current_token and self.current_token.type == "IDENTIFIER": # Local function must have a name
            name = self._parse_identifier()
        else:
            self._error("Expected function name after local function declaration")
        
        self._eat("PUNCTUATOR", "(")
        parameters = []
        if self.current_token and self.current_token.type != "PUNCTUATOR" and self.current_token.value != ")":
            parameters.append(self._parse_identifier())
            while self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
                self._eat("PUNCTUATOR", ",")
                if self.current_token.type == "VARARG": # Allow '...' as last parameter
                    parameters.append(VarargExpression())
                    self._eat("VARARG")
                    break
                parameters.append(self._parse_identifier())
            if self.current_token and self.current_token.type == "VARARG": # Allow '...' as sole parameter
                if not parameters or not isinstance(parameters[-1], VarargExpression):
                    self._eat("VARARG")
                    parameters.append(VarargExpression())

        self._eat("PUNCTUATOR", ")")

        body = self._parse_block()
        self._eat("END")
        return FunctionDeclaration(name, parameters, body, is_local)

    def _parse_function_name(self):
        base = self._parse_identifier()
        while self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ".":
            self._eat("PUNCTUATOR", ".")
            identifier = self._parse_identifier()
            base = MemberExpression(base, identifier)
        if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ":":
            self._eat("PUNCTUATOR", ":")
            identifier = self._parse_identifier()
            base = MemberExpression(base, identifier, is_colon=True)
        return base

    def _parse_if_statement(self):
        self._eat("IF")
        condition = self._parse_expression()
        self._eat("THEN")
        then_block = self._parse_block()
        
        elseif_blocks = []
        while self.current_token and self.current_token.type == "ELSEIF":
            self._eat("ELSEIF")
            elseif_condition = self._parse_expression()
            self._eat("THEN")
            elseif_block = self._parse_block()
            elseif_blocks.append((elseif_condition, elseif_block))

        else_block = None
        if self.current_token and self.current_token.type == "ELSE":
            self._eat("ELSE")
            else_block = self._parse_block()
        
        self._eat("END")
        return IfStatement(condition, then_block, else_block, elseif_blocks)

    def _parse_while_statement(self):
        self._eat("WHILE")
        condition = self._parse_expression()
        self._eat("DO")
        body = self._parse_block()
        self._eat("END")
        return WhileStatement(condition, body)

    def _parse_for_statement(self):
        self._eat("FOR")
        var = self._parse_identifier()

        if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == "=":
            # Numeric For Loop
            self._eat("PUNCTUATOR", "=")
            start = self._parse_expression()
            self._eat("PUNCTUATOR", ",")
            end = self._parse_expression()
            step = None
            if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
                self._eat("PUNCTUATOR", ",")
                step = self._parse_expression()
            self._eat("DO")
            body = self._parse_block()
            self._eat("END")
            return ForNumericStatement(var, start, end, step, body)
        elif self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
            # Generic For Loop - multiple variables, then 'in' expr_list
            vars = [var]
            while self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
                self._eat("PUNCTUATOR", ",")
                vars.append(self._parse_identifier())
            
            self._eat("IN")
            exprs = self._parse_expression_list()
            self._eat("DO")
            body = self._parse_block()
            self._eat("END")
            return ForGenericStatement(vars, exprs, body)
        else:
            self._error("Invalid FOR loop syntax")

    def _parse_return_statement(self):
        self._eat("RETURN")
        expressions = []
        if self.current_token and self.current_token.type not in ("END", "ELSE", "ELSEIF", "UNTIL", "EOF"):
            expressions = self._parse_expression_list()
        return ReturnStatement(expressions)

    def _parse_label_statement(self):
        self._eat("PUNCTUATOR", "::")
        name = self._parse_identifier()
        self._eat("PUNCTUATOR", "::")
        return LabelStatement(name)

    def _parse_goto_statement(self):
        self._eat("GOTO")
        label_name = self._parse_identifier()
        return GotoStatement(label_name)

    def _parse_repeat_until_statement(self):
        self._eat("REPEAT")
        body = self._parse_block()
        self._eat("UNTIL")
        condition = self._parse_expression()
        return RepeatUntilStatement(body, condition)

    def _parse_expression_list(self):
        expressions = [self._parse_expression()]
        while self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == ",":
            self._eat("PUNCTUATOR", ",")
            expressions.append(self._parse_expression())
        return expressions

    def _parse_expression(self, precedence_level=0):
        left = self._parse_primary_expression()

        while self.current_token and self.current_token.value in self.precedence and \
              self.precedence[self.current_token.value] >= precedence_level:
            operator = self.current_token.value
            operator_precedence = self.precedence[operator]

            if operator == "..": # Right-associative
                self._advance()
                right = self._parse_expression(operator_precedence)
            else:
                self._advance()
                right = self._parse_expression(operator_precedence + 1)
            left = BinaryOperator(left, operator, right)
        return left

    def _parse_primary_expression(self):
        token_type = self.current_token.type
        token_value = self.current_token.value

        if token_type == "IDENTIFIER":
            return self._parse_prefix_expression()
        elif token_type in ("NUMBER", "STRING", "TRUE", "FALSE", "NIL"):
            literal_token = self.current_token
            self._advance()
            return Literal(literal_token.value, literal_token.type)
        elif token_type == "PUNCTUATOR" and token_value == "(":
            self._eat("PUNCTUATOR", "(")
            expr = self._parse_expression()
            self._eat("PUNCTUATOR", ")")
            return self._parse_suffix_expression(expr) # Handle (expr)() or (expr).member
        elif token_type == "PUNCTUATOR" and token_value == "{":
            return self._parse_table_constructor()
        elif token_type == "VARARG":
            self._eat("VARARG")
            return VarargExpression()
        elif token_value in ("NOT", "-", "#") or (token_type == "OPERATOR" and token_value in ("-", "not", "#")):
            operator = self.current_token.value
            self._advance()
            operand = self._parse_expression(self.precedence["UNARY"])
            return UnaryOperator(operator, operand)
        else:
            self._error(f"Unexpected token in expression: {self.current_token}")

    def _parse_prefix_expression(self):
        expr = self._parse_atom_expression()
        return self._parse_suffix_expression(expr)

    def _parse_atom_expression(self):
        if self.current_token.type == "IDENTIFIER":
            name = self.current_token.value
            self._advance()
            return Identifier(name)
        elif self.current_token.type == "PUNCTUATOR" and self.current_token.value == "(":
            self._eat("PUNCTUATOR", "(")
            expr = self._parse_expression()
            self._eat("PUNCTUATOR", ")")
            return expr
        else:
            self._error(f"Expected identifier or (expression), got {self.current_token}")

    def _parse_suffix_expression(self, base):
        while self.current_token and self.current_token.type in ("PUNCTUATOR", "STRING", "NUMBER"):
            token_value = self.current_token.value

            if token_value == ".":
                self._eat("PUNCTUATOR", ".")
                identifier = self._parse_identifier()
                base = MemberExpression(base, identifier)
            elif token_value == ":":
                self._eat("PUNCTUATOR", ":")
                identifier = self._parse_identifier()
                base = MemberExpression(base, identifier, is_colon=True)
            elif token_value == "[":
                self._eat("PUNCTUATOR", "[")
                index_expr = self._parse_expression()
                self._eat("PUNCTUATOR", "]")
                base = IndexExpression(base, index_expr)
            elif token_value == "(": # Function call with args list
                self._eat("PUNCTUATOR", "(")
                args = []
                if self.current_token and self.current_token.type != "PUNCTUATOR" and self.current_token.value != ")":
                    args = self._parse_expression_list()
                self._eat("PUNCTUATOR", ")")
                base = FunctionCall(base, args)
            elif token_type == "STRING": # Function call with string literal as arg
                string_arg = self.current_token.value
                string_type = self.current_token.type
                self._advance()
                base = FunctionCall(base, [Literal(string_arg, string_type)])
            elif token_type == "PUNCTUATOR" and token_value == "{": # Function call with table constructor as arg
                table_arg = self._parse_table_constructor()
                base = FunctionCall(base, [table_arg])
            else:
                break
        return base

    def _parse_identifier(self):
        ident_token = self._eat("IDENTIFIER")
        return Identifier(ident_token.value)

    def _parse_table_constructor(self):
        self._eat("PUNCTUATOR", "{")
        fields = []
        while self.current_token and self.current_token.type != "PUNCTUATOR" and self.current_token.value != "}":
            field = self._parse_table_field()
            fields.append(field)
            if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value in (",", ";"):
                self._eat("PUNCTUATOR", self.current_token.value)
            else:
                break
        self._eat("PUNCTUATOR", "}")
        return TableConstructor(fields)

    def _parse_table_field(self):
        if self.current_token and self.current_token.type == "PUNCTUATOR" and self.current_token.value == "[":
            self._eat("PUNCTUATOR", "[")
            key = self._parse_expression()
            self._eat("PUNCTUATOR", "]")
            self._eat("PUNCTUATOR", "=")
            value = self._parse_expression()
            return TableField(key, value, is_key_expr=True)
        elif self.current_token and self.current_token.type == "IDENTIFIER" and \
            self._peek() and self._peek().type == "PUNCTUATOR" and self._peek().value == "=":
            key = self._parse_identifier()
            self._eat("PUNCTUATOR", "=")
            value = self._parse_expression()
            return TableField(key, value)
        else:
            value = self._parse_expression()
            return TableField(None, value) # Positional field


# Example Usage:
if __name__ == "__main__":
    from lexer import Lexer

    lua_code = """
local a = 10
local b = "hello"
local function add(x, y)
    return x + y
end

if a > 5 then
    print(add(a, 5))
elseif a == 10 then
    local tbl = { key = "value", [1] = true, {nested = 1} }
    print(tbl.key, tbl[1])
else
    print("Less than 5")
end

for i = 1, 10, 2 do
    print(i)
end

for k, v in pairs(tbl) do
    print(k, v)
end

::my_label::
goto my_label

local function foo(...)
    print(...)
end

"""

    lexer = Lexer(lua_code)
    tokens = lexer.tokenize()

    # for token in tokens:
    #     print(token)

    parser = Parser(tokens)
    ast = parser.parse()

    # Basic AST printing (can be improved with a dedicated pretty printer)
    def print_ast(node, indent=0):
        print("  " * indent + repr(node))
        for child in node.children:
            print_ast(child, indent + 1)

    print("\n--- AST ---")
    print_ast(ast)

