from pyasm import objasm


def generate_asm_for_operator(op: objasm.OpCode) -> str:
    return ' '.join([op.op] + op.args)


def generate_asm_for_label(label: objasm.Label, indent='\t') -> str:
    result = label.name + ':\n'
    for op in label.codes:
        result += indent + generate_asm_for_operator(op) + '\n'
    return result


def generate_asm(root: objasm.Program) -> str:
    result = ''
    for label in root.labels:
        result += '\n'
        result += generate_asm_for_label(label)
        result += '\n'
    return result


if __name__ == '__main__':
    from pyasm import parse
    import ast
    import sys
    print(generate_asm(parse.parse(ast.parse(open(sys.argv[1]).read()))))
