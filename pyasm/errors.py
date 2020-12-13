class ParseError(Exception):
    lineno: int
    element_name: str

    @classmethod
    def create_custom(cls, message: str, **kwargs):
        err = cls(message)
        err.__dict__.update(kwargs)
        return err


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
