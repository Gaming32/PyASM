import ast
from typing import Union

from pyasm import objasm


fns = {
    'jump': 'jmp',
    'call': 'jsr',
    'add_memory': 'adc',
    'increment_memory': 'inc',

    'branch_plus': 'bpl',
    'branch_minus': 'bmi',
    'branch_eq': 'beq',
    'branch_ne': 'bne',
}

immfns = {
    'load_immediate': [
        'lda',
        'ldx',
        'ldy'
    ]
}

dirimmfns = {
    'add_value': 'adc'
}

regfns = {
    'load_address': [
        'ldx',
        'ldy',
        'lda',
        None
    ],
    'increment_register': [
        'inx',
        'iny',
        None,
        None
    ],
    'store_register': [
        'stx',
        'sty',
        'sta',
        None
    ],
    'push': [
        'txs',
        None,
        'pha',
        'php'
    ],
    'pull': [
        'tsx',
        None,
        'pla',
        'plp'
    ],

    'compare': [
        'cpx',
        'cpy',
        'cmp',
        None
    ]
}


class Macro:
    args: list[str]
    ops = list[objasm.OpCode]


def _parse_arg(arg: Union[ast.Name, ast.Constant], macargs=None) -> str:
    if isinstance(arg, ast.Name):
        if macargs is not None and arg.id in macargs:
            return [arg.id, '']
        return arg.id
    return str(arg.value)


def _fill_macro(macro: list[objasm.OpCode], args: dict[str, str]):
    copy = []
    for item in macro:
        item_copy = objasm.OpCode(**item.get_parts())
        for (i, arg) in enumerate(item_copy.args):
            if type(arg) == list:
                # newarg = 
                if type(args[arg[0]]) == list:
                    newarg = [args[arg[0]][0], arg[1] + args[arg[0]][1]]
                else:
                    newarg = arg[1] + args[arg[0]]
                item_copy.args[i] = newarg
            # adds = ''
            # if type(arg) == list:
            #     while arg[0] in args and type(args[arg[0]]) == list:
            #         adds += arg[1]
            #         arg = args[arg[0]]
            #     if arg[0] in args:
            #         adds += arg[1]
            #         arg = args[arg[0]] 
            # if type(arg) == list:
            #     arg[1] = adds + arg[1]
            #     item_copy.args[i] = arg
            # else:
            #     item_copy.args[i] = adds + arg
        copy.append(item_copy)
    return copy

def _parse_pycall(call: ast.Call, macros: dict, macargs) -> list[objasm.OpCode]:
    fname = call.func.id
    if fname in macros:
        return _fill_macro(macros[fname].ops, {ar: _parse_arg(ca, macargs) for (ar, ca) in zip(macros[fname].args, call.args)})
    elif fname in fns:
        args = [_parse_arg(arg, macargs) for arg in call.args]
        return [objasm.OpCode(op=fns[fname], args=args)]
    elif fname in dirimmfns:
        args = []
        for arg in call.args:
            args.append(_parse_arg(arg, macargs))
            if type(args[-1]) == list:
                args[-1][1] = '#'
            else:
                args[-1] = '#' + args[-1]
        return [objasm.OpCode(op=dirimmfns[fname], args=args)]
    elif fname in regfns:
        regstr = call.args[0].id
        opix = {
            'regx': 0,
            'regy': 1,
            'accum': 2,
            'proc': 3
        }.get(regstr)
        if opix is None:
            raise ValueError(f'unsupported register {call.args[0].id!r} for {fname!r}')
        args = [_parse_arg(arg, macargs) for arg in call.args[1:]]
        return [objasm.OpCode(op=regfns[fname][opix], args=args)]
    elif fname in immfns:
        regstr = call.args[0].id
        opix = {
            'accum': 0,
            'regx': 1,
            'regy': 2
        }.get(regstr)
        if opix is None:
            raise ValueError(f'unsupported register {call.args[0].id!r} for {fname!r}')
        args = []
        for arg in call.args[1:]:
            args.append(_parse_arg(arg, macargs))
            if type(args[-1]) == list:
                args[-1][1] = '#'
            else:
                args[-1] = '#' + args[-1]
        return [objasm.OpCode(op=immfns[fname][opix], args=args)]
    elif fname == 'halt':
        return [objasm.OpCode(op='jmp', args=['___hlt___'])]
    else:
        raise ValueError(f'unsupported function: {fname!r}')


def _parse_code(code: Union[ast.Expr, ast.Pass, ast.Return], macros: dict, macargs) -> list[objasm.OpCode]:
    if isinstance(code, ast.Pass):
        return [objasm.OpCode(op='nop', args=[])]
    elif isinstance(code, ast.Expr):
        if isinstance(code.value, ast.Call):
            return _parse_pycall(code.value, macros, macargs)
        else:
            raise TypeError(f'unsupported Expr.value type: {type(code.value).__name__!r}')
    elif isinstance(code, ast.Return):
        return [objasm.OpCode(op='rts', args=[])]
    else:
        raise TypeError(f'unsupported code type: {type(code).__name__!r}')


def _parse_function(fn: ast.FunctionDef, macros: dict, ismacro=False) -> objasm.Label:
    result = objasm.Label(name=fn.name, codes=[])
    macargs = None
    if ismacro:
        macargs = [arg.arg for arg in fn.args.args]
    for body_part in fn.body:
        result.codes.extend(_parse_code(body_part, macros, macargs))
    if ismacro:
        newmac = Macro()
        newmac.args = macargs
        newmac.ops = result.codes
        macros[fn.name] = newmac
    return result


def parse(root: ast.Module) -> objasm.Program:
    result = objasm.Program(labels=[])
    reserved_labels = []
    macros = {}
    for branch in root.body:
        if type(branch) == ast.ImportFrom:
            if branch.module == 'pyasm.stubs':
                continue
        elif type(branch) == ast.FunctionDef:
            macro = False
            for dec in branch.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == 'inline_macro':
                    macro = True
            parse_result = _parse_function(branch, macros, macro)
            if not macro:
                result.labels.append(parse_result)
        elif type(branch) == ast.Expr:
            if isinstance(branch.value, ast.Call):
                if branch.value.func.id == 'reserve_label':
                    reserved_labels.append(branch.value.args[0].value)
                else:
                    raise ValueError(f'unsupported top-level function: {branch.value.name!r}')
            else:
                raise TypeError(f'unsupported body type: {type(branch.value).__name__!r}')
        else:
            raise TypeError(f'unsupported body type: {type(branch).__name__!r}')
    result.labels.append(objasm.Label(name='___hlt___', codes=[]))
    for label in reserved_labels:
        result.labels.append(objasm.Label(name=label, codes=[]))
    return result


if __name__ == '__main__':
    print(objasm.dump(parse(ast.parse(open('example.pyasm').read()))))
