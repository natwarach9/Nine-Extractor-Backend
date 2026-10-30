import re

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, Line {self.line}, Col {self.column})"

class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.line = 1
        self.column = 1
        self.position = 0

        self.keywords = {
            "and", "break", "do", "else", "elseif", "end", "false", "for", "function",
            "if", "in", "local", "nil", "not", "or", "repeat", "return", "then", "true",
            "until", "while"
        }

        self.operators = {
            "+", "-", "*", "/", "%", "^", "#", "==", "~=", "<=", ">=", "<", ">", "=",
            "(", ")", "{", "}", "[", "]", ";", ":", ",", ".", "..", "...", "and", "or", "not"
        }

        self.token_specs = [
            (r"[a-zA-Z_][a-zA-Z0-9_]*", "IDENTIFIER"),  # Identifiers and Keywords
            (r"\d+(\.\d*)?([eE][+-]?\d+)?", "NUMBER"),  # Numbers (integers and floats)
            (r"\"(\\\\|\\\"|[^\\\"])*\"", "STRING"),  # Double-quoted strings
            (r"\'(\\\\|\\\'|[^\\\'])*\'", "STRING"),  # Single-quoted strings
            (r"\[\[.*?\]\]", "LONG_STRING"),  # Long strings/comments [[...]]
            (r"--\[\[.*?--\]\]", "LONG_COMMENT"),  # Long comments --[[...--]]
            (r"--.*", "SHORT_COMMENT"),  # Short comments --...
            (r"\.\.\.", "VARARG"), # ...
            (r"\.\.", "CONCAT"),   # ..
            (r"==", "EQ"),       # ==
            (r"~=", "NE"),       # ~=
            (r"<=", "LE"),       # <=
            (r">=", "GE"),       # >=
            (r"<<", "SHL"),      # <<
            (r">>", "SHR"),      # >>
            (r"//", "IDIV"),     # //
            (r"::", "LABEL"),    # ::
            (r"[+\-*/%^#<>=]", "OPERATOR"), # Basic operators
            (r"[(){}[];:,.]", "PUNCTUATOR"), # Punctuators
            (r"\s+", None),  # Whitespace (ignore)
        ]

    def tokenize(self):
        while self.position < len(self.source_code):
            match = self._match_token()
            if match:
                token_type, token_value = match
                if token_type:  # Ignore whitespace and comments
                    if token_type == "IDENTIFIER" and token_value in self.keywords:
                        token_type = token_value.upper()
                    elif token_type == "OPERATOR" and token_value in self.operators:
                        # Specific operators handled above, generic ones here
                        pass
                    elif token_type == "PUNCTUATOR" and token_value in self.operators:
                        # Specific punctuators handled above, generic ones here
                        pass
                    
                    self.tokens.append(Token(token_type, token_value, self.line, self.column))
                self._advance_position(token_value)
            else:
                raise SyntaxError(f"Unexpected character '{self.source_code[self.position]}' at Line {self.line}, Col {self.column}")
        return self.tokens

    def _match_token(self):
        for pattern, token_type in self.token_specs:
            regex_match = re.match(pattern, self.source_code[self.position:])
            if regex_match:
                value = regex_match.group(0)
                if token_type == "LONG_COMMENT": # Handle long comments as comments, not strings
                    token_type = None # Ignore comments
                elif token_type == "SHORT_COMMENT":
                    token_type = None # Ignore comments
                return token_type, value
        return None, None

    def _advance_position(self, value):
        for char in value:
            if char == '\\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.position += 1

# Example Usage:
if __name__ == "__main__":
    lua_code = """
local function test(a, b)
    -- This is a comment
    local x = 10 + "hello" .. [[
        long string
    ]]
    if a == b then
        print("Equal")
    else
        print("Not Equal")
    end
    --[[ long comment
        with multiple lines
    --]]
    return x
end
::label::
"""
    lexer = Lexer(lua_code)
    tokens = lexer.tokenize()
    for token in tokens:
        print(token)
