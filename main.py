from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

INT_RE  = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?')
STR_RE  = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
BOOL_RE = re.compile(r'\b(?:true|false|nil)\b')
FUNC_RE = re.compile(r'\bfunction\b')

def scan_tables(src: str):
    out, i, n = [], 0, len(src)
    while i < n:
        if src[i] == '{':
            depth, start, j = 0, i, i
            in_str = None
            while j < n:
                c = src[j]
                if in_str:
                    if c == '\\': j += 2; continue
                    if c == in_str: in_str = None
                elif c in '"\'': in_str = c
                elif c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        out.append(src[start:j + 1]); break
                j += 1
            i = j + 1 if j > i else i + 1
        else:
            i += 1
    return out

def classify(body: str):
    inner = body[1:-1]
    nf = len(FUNC_RE.findall(inner))
    if nf >= 8:
        return ('handlers', nf, None)
    ints  = INT_RE.findall(inner)
    strs  = STR_RE.findall(inner)
    bools = BOOL_RE.findall(inner)
    if len(ints) > 100 and not strs and not bools:
        return ('bytecode', len(ints), [int(x) if '.' not in x and 'e' not in x.lower() else float(x) for x in ints])
    if strs:
        return ('constants', len(strs), strs)
    return None

def unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in '"\'':
        return s[1:-1]
    return s

@app.route('/deobfuscate', methods=['POST'])
def deobfuscate():
    data = request.get_json() or {}
    src = data.get('code', '')
    
    if not src or len(src) < 50:
        return jsonify({'success': False, 'error': 'โค้ดสั้นเกินไปหรือว่างเปล่า'})

    try:
        bytecode, constants, handlers = None, None, 0
        for body in scan_tables(src):
            cls = classify(body)
            if not cls: continue
            kind, n, val = cls
            if kind == 'bytecode' and (bytecode is None or n > len(bytecode)):
                bytecode = val
            elif kind == 'constants' and (constants is None or n > len(constants)):
                constants = val
            elif kind == 'handlers':
                handlers = max(handlers, n)

        extracted_strings = []
        if constants:
            extracted_strings = [unquote(c) for c in constants if c and c[0] in '"\'']

        result_lines = [
            "-- [ NINE EXTRACTOR - STATIC ANALYSIS RESULT ]",
            f"-- Handlers detected: {handlers}",
            f"-- Bytecode probes: {len(bytecode) if bytecode else 0}",
            f"-- Constants found: {len(extracted_strings)} strings",
            "",
            "local Constants = {"
        ]
        for s in extracted_strings[:100]:
            result_lines.append(f"    {repr(s)},")
        result_lines.append("}")
        
        return jsonify({
            'success': True,
            'deobfuscated_code': '\n'.join(result_lines)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
