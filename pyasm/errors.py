class PyASMError(Exception):
    lineno: int

    @classmethod
    def create_custom(cls, message: str, **kwargs):
        err = cls(message)
        err.__dict__.update(kwargs)
        return err


class ParseError(PyASMError):
    element_name: str


class UnsupportedSyntaxElement(ParseError, TypeError):
    colno: int

    @classmethod
    def create_custom(cls, location: str, line: int = None, column: int = None, el: str = None):
        eltypename = type(el).__name__
        kwargs = {
            'lineno': line,
            'colno': column,
            'element_name': eltypename
        }
        message = f'unsupported {location} type: {eltypename!r}'
        return super().create_custom(message, **kwargs)


class UnsupportedFunctionOrElement(ParseError, ValueError):
    @classmethod
    def create_custom(cls, what: str, message: str, line: int = None, elname: str = None):
        kwargs = {
            'lineno': line,
            'element_name': elname
        }
        msg = f'unsupported {what}{message}'
        return super().create_custom(msg, **kwargs)


class NoModuleError(PyASMError, ModuleNotFoundError):
    module: str

    @classmethod
    def create_custom(cls, module: str, lineno: int = None):
        return super().create_custom(f'unable to import module: no module named {module!r}',
                                     module=module, lineno=lineno)
