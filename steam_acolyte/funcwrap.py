import inspect
import functools

__version__ = '0.0.1'


def wraps(func, wrapper=None):

    """
    Return a wrapper around ``wrapper`` that preserves the signature of
    the original function ``func`` exactly.
    """

    if wrapper is None:
        return functools.partial(wraps, func)

    signature = inspect.signature(func)
    argspec = inspect.getfullargspec(func)
    funcsig = list(argspec.args)
    callargs = list(argspec.args)

    if argspec.varargs:
        funcsig.append('*' + argspec.varargs)
        callargs.append('*' + argspec.varargs)
    elif argspec.kwonlyargs:
        funcsig.append('*')
    for a in argspec.kwonlyargs:
        funcsig.append('%s' % a)
        callargs.append('%s=%s' % (a, a))
    if argspec.varkw:
        funcsig.append('**' + argspec.varkw)
        callargs.append('**' + argspec.varkw)

    num_pos_only = next(
        (i for i, p in enumerate(signature.parameters.values())
         if p.kind.name != 'POSITIONAL_ONLY'),
        len(signature.parameters))
    if num_pos_only > 0:
        funcsig.insert(num_pos_only, '/')

    wrapper_name = '__call__'
    while wrapper_name in signature.parameters:
        wrapper_name += '_'

    source = 'lambda {funcsig}: {callee}({callargs})'.format(
        callee=wrapper_name,
        funcsig=', '.join(funcsig),
        callargs=', '.join(callargs),
    )

    try:
        sourcefile = inspect.getsourcefile(func)
        filename = '<decorator {}>'.format(sourcefile)
    except TypeError:
        filename = '<decorator>'

    code = compile(source, filename, 'eval')
    fun = eval(code, {wrapper_name: wrapper})
    fun.__name__ = getattr(func, '__name__', '<unknown>')
    fun.__doc__ = getattr(func, '__doc__', '')
    fun.__dict__ = getattr(func, '__dict__', {}).copy()
    fun.__defaults__ = argspec.defaults
    fun.__kwdefaults__ = argspec.kwonlydefaults
    fun.__annotations__ = argspec.annotations
    fun.__module__ = getattr(func, '__module__', None)
    fun.__wrapped__ = func
    fun.__source__ = source
    if hasattr(func, '__qualname__'):
        fun.__qualname__ = func.__qualname__
    return fun
