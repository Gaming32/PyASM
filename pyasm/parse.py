import ast
import os
import sys
import glob
from typing import Union

from pyasm import errors, objasm

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


def _parse_arg(arg: Union[ast.Name, ast.Constant], macargs=None, consts=None) -> str:
    if isinstance(arg, ast.Name):
        if macargs is not None and arg.id in macargs:
            return [arg.id, '']
        if consts is not None and arg.id in consts:
            return consts[arg.id]
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
        copy.append(item_copy)
    return copy


def _parse_pycall(call: ast.Call, macros: dict, macargs, consts) -> list[objasm.OpCode]:
    fname = call.func.id
    if fname in macros:
        return _fill_macro(macros[fname].ops, {ar: _parse_arg(ca, macargs, consts) for (ar, ca) in zip(macros[fname].args, call.args)})
    elif fname in fns:
        args = [_parse_arg(arg, macargs, consts) for arg in call.args]
        return [objasm.OpCode(op=fns[fname], args=args)]
    elif fname in dirimmfns:
        args = []
        for arg in call.args:
            args.append(_parse_arg(arg, macargs, consts))
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
            raise errors.UnsupportedFunctionOrElement.create_custom(
                'register',
                f' {call.args[0].id!r} for {fname!r}',
                call.lineno,
                fname
            )
        args = [_parse_arg(arg, macargs, consts) for arg in call.args[1:]]
        return [objasm.OpCode(op=regfns[fname][opix], args=args)]
    elif fname in immfns:
        regstr = call.args[0].id
        opix = {
            'accum': 0,
            'regx': 1,
            'regy': 2
        }.get(regstr)
        if opix is None:
            raise errors.UnsupportedFunctionOrElement.create_custom(
                'register',
                f' {call.args[0].id!r} for {fname!r}',
                call.lineno,
                fname
            )
        args = []
        for arg in call.args[1:]:
            args.append(_parse_arg(arg, macargs, consts))
            if type(args[-1]) == list:
                args[-1][1] = '#'
            else:
                args[-1] = '#' + args[-1]
        return [objasm.OpCode(op=immfns[fname][opix], args=args)]
    elif fname == 'halt':
        return [objasm.OpCode(op='jmp', args=['___hlt___'])]
    else:
        raise errors.UnsupportedFunctionOrElement.create_custom(
            'function',
            f': {fname!r}',
            call.lineno,
            fname
        )


def _parse_code(code: Union[ast.Expr, ast.Pass, ast.Return], macros: dict, macargs, consts) -> list[objasm.OpCode]:
    if isinstance(code, ast.Pass):
        return [objasm.OpCode(op='nop', args=[])]
    elif isinstance(code, ast.Expr):
        if isinstance(code.value, ast.Call):
            return _parse_pycall(code.value, macros, macargs, consts)
        else:
            raise errors.UnsupportedSyntaxElement.create_custom(
                'Expr.value',
                code.value.lineno,
                code.value.col_offset,
                code.value
            )
    elif isinstance(code, ast.Return):
        return [objasm.OpCode(op='rts', args=[])]
    else:
        raise errors.UnsupportedSyntaxElement.create_custom(
            'code',
            code.lineno,
            code.col_offset,
            code
        )


def _parse_function(fn: ast.FunctionDef, macros: dict, consts, ismacro=False) -> objasm.Label:
    result = objasm.Label(name=fn.name, codes=[])
    macargs = None
    if ismacro:
        macargs = [arg.arg for arg in fn.args.args]
    for body_part in fn.body:
        result.codes.extend(_parse_code(body_part, macros, macargs, consts))
    if ismacro:
        newmac = Macro()
        newmac.args = macargs
        newmac.ops = result.codes
        macros[fn.name] = newmac
    return result


MODULE_PATH = [
    '.',
    os.path.join(os.path.dirname(__file__), 'builtin-modules')
]

MODULE_EXTS = ['.pyasm', '.py']

def find_module(name: str) -> Union[str, None]:
    for dirname in MODULE_PATH + sys.path:
        for ext in MODULE_EXTS:
            patt = os.path.join(dirname, name + ext)
            for filepath in glob.iglob(patt):
                return filepath
    return None


MacroDict = dict[str, Macro]
ConstantDict = dict[str, str]
LabelList = list[str]


def parse2(root: ast.Module, _recurc: int = 0) -> tuple[objasm.Program, MacroDict, ConstantDict, LabelList]:
    result = objasm.Program(labels=[])
    reserved_labels = []
    macros = {}
    consts = {}
    for branch in root.body:
        if type(branch) == ast.ImportFrom:
            if branch.module == 'pyasm.stubs':
                continue
            elif (filepath := find_module(branch.module)) is not None:
                with open(filepath, 'r') as fp:
                    new_module = ast.parse(fp.read(), filepath)
                result.labels.append(objasm.Label(name=f'___jts1_{_recurc}___', codes=[
                    objasm.OpCode(op='jmp', args=[f'___jts2_{_recurc}___'])
                ]))
                new_result, new_macros, new_consts, new_reserved = parse2(new_module, _recurc + 1)
                result.labels.extend(new_result.labels)
                macros.update(new_macros)
                consts.update(new_consts)
                reserved_labels.extend(new_reserved)
                result.labels.append(objasm.Label(name=f'___jts2_{_recurc}___', codes=[]))
            else:
                raise errors.NoModuleError.create_custom(branch.module, branch.lineno)
        elif type(branch) == ast.FunctionDef:
            macro = False
            for dec in branch.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == 'inline_macro':
                    macro = True
            parse_result = _parse_function(branch, macros, consts, macro)
            if not macro:
                result.labels.append(parse_result)
        elif type(branch) == ast.Expr:
            if isinstance(branch.value, ast.Call):
                if branch.value.func.id == 'reserve_label':
                    reserved_labels.append(_parse_arg(branch.value.args[0], None, consts))
                else:
                    raise errors.UnsupportedFunctionOrElement.create_custom(
                        'top-level function',
                        f': {branch.value.func.id!r}',
                        branch.value.lineno,
                        branch.value.func.id
                    )
            else:
                raise errors.UnsupportedSyntaxElement.create_custom(
                    'body',
                    branch.value.lineno,
                    branch.value.col_offset,
                    branch.value
                )
        elif type(branch) == ast.Assign:
            for targ in branch.targets:
                consts[targ.id] = _parse_arg(branch.value, None, consts)
        else:
            raise errors.UnsupportedSyntaxElement.create_custom(
                'body',
                branch.lineno,
                branch.col_offset,
                branch
            )
    return result, macros, consts, reserved_labels


def parse(root: ast.Module) -> objasm.Program:
    result, _, _, reserved_labels = parse2(root)
    result.labels.append(objasm.Label(name='___hlt___', codes=[]))
    for label in reserved_labels:
        result.labels.append(objasm.Label(name=label, codes=[]))
    return result


if __name__ == '__main__':
    print(objasm.dump(parse(ast.parse(open('example.pyasm').read()))))
