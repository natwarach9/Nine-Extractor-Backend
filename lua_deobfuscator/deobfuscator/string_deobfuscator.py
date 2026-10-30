
import re
import base64

from ..lexer.lexer import LuaLexer
from ..parser.parser import LuaParser, ASTNode

class StringDeobfuscator:
    def __init__(self, ast):
        self.ast = ast
        self.deobfuscated_strings = {}
        # A simple sandbox for evaluating expressions during deobfuscation
        # IMPORTANT: This is a very basic and INSECURE sandbox. 
        # A proper sandbox would use luavm or a more robust approach.
        self.sandbox_globals = {
            'string': {
                'char': chr,
                'byte': ord,
                'sub': lambda s, i, j: s[i-1:j] if j else s[i-1:]
            },
            'math': {
                'floor': int,
            },
            'table': {
                'concat': lambda t: ''.join(map(str, t))
            },
            '_G': {},
            '_ENV': {},
            'tonumber': int,
            'tostring': str,
            'pairs': lambda t: iter(t.items()) if hasattr(t, 'items') else iter([]) # Placeholder for iteration
        }

    def _evaluate_expression(self, node):
        # A very basic AST evaluator for simple expressions, mainly for string deobfuscation.
        # This is NOT a full Lua interpreter.
        if node.type == 'NUMBER_LITERAL':
            try:
                # Handle hex numbers from lexer if any
                if node.value.startswith('0x') or node.value.startswith('0X'):
                    return int(node.value, 16)
                return float(node.value) if '.' in node.value or 'e' in node.value.lower() else int(node.value)
            except ValueError:
                return None # Should not happen if lexer is correct
        elif node.type == 'STRING_LITERAL':
            return node.value
        elif node.type == 'BOOLEAN_LITERAL':
            return node.value
        elif node.type == 'IDENTIFIER':
            # Try to resolve from sandbox globals, very limited
            if node.value in self.sandbox_globals:
                return self.sandbox_globals[node.value]
            # For nested access like string.char
            if '.' in node.value:
                parts = node.value.split('.')
                current = self.sandbox_globals.get(parts[0])
                if current is not None:
                    for part in parts[1:]:
                        current = current.get(part)
                        if current is None: break
                return current
            return None # Cannot evaluate arbitrary identifiers
        elif node.type == 'UNARY_EXPRESSION':
            operand = self._evaluate_expression(node.children[0])
            if operand is None: return None
            if node.value == '-':
                return -operand
            elif node.value == 'not':
                return not operand
            elif node.value == '#':
                return len(operand) if isinstance(operand, (str, list, dict)) else None
        elif node.type == 'BINARY_EXPRESSION':
            left = self._evaluate_expression(node.children[0])
            right = self._evaluate_expression(node.children[1])
            if left is None or right is None: return None
            
            op = node.value
            if op == '+': return left + right
            elif op == '-': return left - right
            elif op == '*': return left * right
            elif op == '/': return left / right
            elif op == '%': return left % right
            elif op == '^': return left ** right # Lua power operator
            elif op == '..': return str(left) + str(right) # Lua concatenation
            elif op == '==': return left == right
            elif op == '~=': return left != right
            elif op == '<=': return left <= right
            elif op == '>=': return left >= right
            elif op == '>': return left > right
            elif op == '<': return left < right
            elif op == 'and': return left and right
            elif op == 'or': return left or right
            # Add other operators as needed
        elif node.type == 'CALL_EXPRESSION':
            func_node = node.children[0]
            args_node = node.children[1]
            
            func = None
            if func_node.type == 'DOT_ACCESS': # e.g., string.char
                base_obj = self._evaluate_expression(func_node.children[0])
                method_name = func_node.children[1].value
                if base_obj and hasattr(base_obj, 'get'): # Treat as dict for sandbox_globals
                    func = base_obj.get(method_name)
            elif func_node.type == 'IDENTIFIER': # e.g., print (not supported directly in eval)
                func = self.sandbox_globals.get(func_node.value)
            
            if func:
                evaluated_args = [self._evaluate_expression(arg) for arg in args_node.children]
                if None not in evaluated_args:
                    try:
                        return func(*evaluated_args)
                    except Exception as e:
                        # print(f"Sandbox function call failed: {e}")
                        return None
            return None
        elif node.type == 'TABLE_CONSTRUCTOR':
            # For simple tables of numbers/strings, e.g., {104, 101, 108}
            table_list = []
            for field in node.children:
                if field.type == 'TABLE_FIELD' and len(field.children) == 1: # Assumes array-like table
                    value = self._evaluate_expression(field.children[0])
                    if value is not None:
                        table_list.append(value)
                    else: return None # Cannot fully evaluate table
                else: return None # Complex table fields not supported for simple evaluation
            return table_list
        # Add other expression types as needed for specific deobfuscation patterns
        return None

    def _traverse_and_deobfuscate_strings(self, node):
        # Implement AST traversal and string deobfuscation logic here
        # This function will recursively visit AST nodes and look for string obfuscation patterns.
        # When a pattern is found, it will attempt to deobfuscate it and replace the AST node
        # or store the deobfuscated string.

        if not isinstance(node, ASTNode): # Handle lists of nodes
            if isinstance(node, list):
                for child in node:
                    self._traverse_and_deobfuscate_strings(child)
            return

        # Example: Simple XOR decryption pattern like `string.char(byte ^ key)` inside a loop or directly.
        # This is a placeholder. Real deobfuscation requires more complex pattern matching and evaluation.
        if node.type == 'BINARY_EXPRESSION' and node.value == '~=': # Lua's XOR is often `bit.bxor` or `~` operator in Luau
            # This is highly simplified and will likely need dedicated pattern matching later.
            # For now, we only detect the presence of XOR operations as a hint.
            pass 

        # Look for table.concat patterns with string.char or similar
        if node.type == 'CALL_EXPRESSION':
            if node.children[0].type == 'DOT_ACCESS' and \
               node.children[0].children[0].type == 'IDENTIFIER' and \
               node.children[0].children[0].value == 'table' and \
               node.children[0].children[1].value == 'concat':
                
                # Check if arguments include array-like table or iterators generating chars
                concat_args_node = node.children[1]
                if len(concat_args_node.children) == 1 and concat_args_node.children[0].type == 'TABLE_CONSTRUCTOR':
                    # Attempt to evaluate the table constructor to get the list of values
                    table_values = self._evaluate_expression(concat_args_node.children[0])
                    if table_values is not None and isinstance(table_values, list):
                        try:
                            # If table values are numbers, try to convert to chars
                            deobf_str = ''.join(chr(int(v)) for v in table_values if isinstance(v, (int, float)))
                            # Store for later replacement or direct replacement
                            self.deobfuscated_strings[id(node)] = deobf_str # Store with AST node ID
                            # print(f"Deobfuscated string from table.concat: {deobf_str}")
                            # Replace the CALL_EXPRESSION with a STRING_LITERAL in the AST
                            node.type = 'STRING_LITERAL'
                            node.value = deobf_str
                            node.children = [] # No children for literal
                        except (ValueError, TypeError):
                            pass # Not a simple char table, or contains non-numeric values

        # Recursively visit children
        for child in node.children:
            self._traverse_and_deobfuscate_strings(child)

    def deobfuscate_strings(self):
        if not self.ast:
            raise ValueError("AST is not available. Parse code first.")

        # Reset deobfuscated strings for a fresh run
        self.deobfuscated_strings = {}
        self._traverse_and_deobfuscate_strings(self.ast)
        return self.deobfuscated_strings

    def get_deobfuscated_ast(self):
        # Return the AST with strings replaced (if _traverse_and_deobfuscate_strings modified it in-place)
        return self.ast

if __name__ == '__main__':
    print("--- String Deobfuscator Testing ---")

    # Example 1: Simple table.concat of character codes
    code_1 = "local s = table.concat({string.char(104), string.char(101), string.char(108), string.char(108), string.char(111)})"
    lexer1 = LuaLexer(code_1)
    parser1 = LuaParser(lexer1.tokenize())
    ast1 = parser1.parse()
    
    print("\nOriginal AST 1:")
    print(ast1.pretty_print())

    deobfuscator1 = StringDeobfuscator(ast1)
    deobf_strings1 = deobfuscator1.deobfuscate_strings()
    print("Deobfuscated Strings 1:", deobf_strings1)
    
    print("Deobfuscated AST 1:")
    print(deobfuscator1.get_deobfuscated_ast().pretty_print())

    # Example 2: More complex concatenation with numbers and operations
    code_2 = "local secret = table.concat({72, 101, 108, 108, 111, string.char(32), 87, 111, 114, 108, 100})"
    lexer2 = LuaLexer(code_2)
    parser2 = LuaParser(lexer2.tokenize())
    ast2 = parser2.parse()

    print("\nOriginal AST 2:")
    print(ast2.pretty_print())

    deobfuscator2 = StringDeobfuscator(ast2)
    deobf_strings2 = deobfuscator2.deobfuscate_strings()
    print("Deobfuscated Strings 2:", deobfuscator2.deobfuscated_strings)
    print("Deobfuscated AST 2:")
    print(deobfuscator2.get_deobfuscated_ast().pretty_print())

    # Example 3: Code with string.char(XOR_OPERATION)
    # This specific pattern requires a more advanced evaluator/symbolic execution
    code_3 = "local xor_val = 0xAA; local encrypted = { 104^xor_val, 101^xor_val, 108^xor_val }; local s = table.concat({string.char(encrypted[1]), string.char(encrypted[2]), string.char(encrypted[3])})"
    lexer3 = LuaLexer(code_3)
    parser3 = LuaParser(lexer3.tokenize())
    ast3 = parser3.parse()

    print("\nOriginal AST 3:")
    print(ast3.pretty_print())

    deobfuscator3 = StringDeobfuscator(ast3)
    deobf_strings3 = deobfuscator3.deobfuscate_strings()
    print("Deobfuscated Strings 3:", deobfuscator3.deobfuscated_strings)
    print("Deobfuscated AST 3:")
    print(deobfuscator3.get_deobfuscated_ast().pretty_print())
    print("Note: XOR deobfuscation needs more advanced symbolic execution or a proper Lua VM integration.")

    # Example 4: Base64 string (manual detection and decoding for now)
    code_4 = "local encoded = \"SGVsbG8gV29ybGQ=\"; local decoded = base64.decode(encoded)"
    lexer4 = LuaLexer(code_4)
    parser4 = LuaParser(lexer4.tokenize())
    ast4 = parser4.parse()
    deobfuscator4 = StringDeobfuscator(ast4)
    deobf_strings4 = deobfuscator4.deobfuscate_strings()
    print("\nCode 4 (Base64) - Manual Deobfuscation needed:\", deobfuscator4.deobfuscated_strings)
    # Manual Base64 decode example for the print statement
    try:
        base64_str = "SGVsbG8gV29ybGQ="
        decoded_val = base64.b64decode(base64_str).decode('utf-8')
        print(f"Manual Base64 Decode: {decoded_val}")
    except Exception as e:
        print(f"Base64 decode error: {e}")


