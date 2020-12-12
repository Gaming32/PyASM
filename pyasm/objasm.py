from __future__ import annotations
from typing import Any, Dict


class ASMNode:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
    
    def get_parts(self) -> Dict[str, Any]:
        res = {}
        for ann in self.__class__.__annotations__:
            res[ann] = getattr(self, ann)
        return res


class Program(ASMNode):
    labels: list[Label]


class Label(ASMNode):
    name: str
    codes: list[OpCode]


class OpCode(ASMNode):
    op: str
    args: list[str]


def _dump_single(obj) -> str:
    substr = ''
    if type(obj) == list:
        substr = '['
        for sub in obj:
            substr += _dump_single(sub) + ', '
        substr = substr.removesuffix(', ') + ']'
    elif isinstance(obj, ASMNode):
        substr = dump(obj)
    else:
        substr = repr(obj)
    return substr


def dump(obj: ASMNode):
    result = type(obj).__name__ + '('
    for subname in type(obj).__annotations__:
        subobj = getattr(obj, subname)
        substr = _dump_single(subobj)
        subresult = subname + '=' + substr + ', '
        result += subresult
    return result.removesuffix(', ') + ')'
