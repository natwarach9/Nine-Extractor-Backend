import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from lua_deobfuscator.lexer.lexer import LuaLexer, SyntaxError as LexerSyntaxError
from lua_deobfuscator.parser.parser import LuaParser, SyntaxError as ParserSyntaxError
from lua_deobfuscator.deobfuscator.detector import ObfuscatorDetector
from lua_deobfuscator.deobfuscator.string_deobfuscator import StringDeobfuscator
from lua_deobfuscator.deobfuscator.control_flow import ControlFlowDeobfuscator
from lua_deobfuscator.deobfuscator.variable_renamer import VariableRenamer
from lua_deobfuscator.deobfuscator.pretty_printer import LuaPrettyPrinter
from lua_deobfuscator.sandbox.lua_sandbox import LuaSandbox

app = Flask(__name__)
CORS(app)  # อนุญาตให้เว็บหน้าบ้านเรียกใช้งาน API ได้

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "active", "message": "NINE HUB Deobfuscator Backend is running!"})

@app.route('/deobfuscate', methods=['POST'])
def deobfuscate_code():
    data = request.json
    if not data or 'code' not in data:
        return jsonify({"error": "No Lua code provided"}), 400

    lua_code = data['code']
    
    try:
        # Step 1: Detect Obfuscator
        detector = ObfuscatorDetector(lua_code)
        detection_result = detector.detect_obfuscator()

        # Step 2 & 3: Lexical & Syntax Analysis
        lexer = LuaLexer(lua_code)
        tokens = lexer.tokenize()
        parser = LuaParser(tokens)
        ast = parser.parse()

        # Step 4: String Deobfuscation
        string_deobfuscator = StringDeobfuscator(ast)
        string_deobfuscator.deobfuscate_strings()
        ast = string_deobfuscator.get_deobfuscated_ast()

        # Step 5: Control Flow Deobfuscation
        control_flow_deobfuscator = ControlFlowDeobfuscator(ast)
        ast = control_flow_deobfuscator.deobfuscate_control_flow()

        # Step 6: Variable Renaming
        variable_renamer = VariableRenamer(ast)
        ast = variable_renamer.rename_variables()

        # Step 7: Pretty Print
        pretty_printer = LuaPrettyPrinter(ast)
        deobfuscated_code = pretty_printer.generate_code()

        return jsonify({
            "success": True,
            "detection": detection_result,
            "deobfuscated_code": deobfuscated_code
        })

    except (LexerSyntaxError, ParserSyntaxError) as e:
        return jsonify({"error": f"Syntax Error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
