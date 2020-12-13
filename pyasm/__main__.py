import ast
import sys

from pyasm import errors, generate, parse

with open(sys.argv[1]) as fp:
    contents = fp.read()
    try:
        print(generate.generate_asm(parse.parse(ast.parse(contents))))
    except errors.ParseError as e:
        lines = contents.splitlines()
        line = lines[e.lineno - 1]
        print('error in file', f'{sys.argv[1]}:{e.lineno}')
        print('  ', line)
        if isinstance(e, errors.UnsupportedSyntaxElement):
            print(' ', ' ' * e.colno, '^')
        print(e.__class__.__qualname__ + ':', e.args[0])
