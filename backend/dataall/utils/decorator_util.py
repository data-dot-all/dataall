def process_func(func):
    """Helper function that helps decorate methods/functions"""
    def no_decorated(f):
        return f

    static_func = False
    try:
        func.__func__
        static_func = True
        fn = func.__func__
    except AttributeError:
        fn = func

    # returns a function to call and static decorator if applied
    return fn, staticmethod if static_func else no_decorated
