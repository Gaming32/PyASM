from ast import *

Module(
    body=[
        ImportFrom(
            module='pyasm.stubs',
            names=[
                alias(name='*')],
            level=0),
        FunctionDef(
            name='mymacro',
            args=arguments(
                posonlyargs=[],
                args=[
                    arg(arg='arg')],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]),
            body=[
                Expr(
                    value=Call(
                        func=Name(id='jump', ctx=Load()),
                        args=[
                            Name(id='start', ctx=Load())],
                        keywords=[]))],
            decorator_list=[
                Name(id='inline_macro', ctx=Load())]),
        FunctionDef(
            name='start',
            args=arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]),
            body=[
                Pass(),
                Expr(
                    value=Call(
                        func=Name(id='call', ctx=Load()),
                        args=[
                            Name(id='mysub', ctx=Load())],
                        keywords=[])),
                Expr(
                    value=Call(
                        func=Name(id='mymacro', ctx=Load()),
                        args=[],
                        keywords=[])),
                Expr(
                    value=Call(
                        func=Name(id='halt', ctx=Load()),
                        args=[],
                        keywords=[]))],
            decorator_list=[]),
        FunctionDef(
            name='mysub',
            args=arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]),
            body=[
                Return()],
            decorator_list=[])],
    type_ignores=[])