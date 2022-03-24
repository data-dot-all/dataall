class JavaClassNotFoundException(Exception):
    """
    Raise if required Java class is not found by py4j
    """

    def __init__(self, java_class):
        Exception.__init__(self)
        self.java_class = java_class

    def __str__(self):
        return "%s. Did you forget to add the jar to the class path?" % (
            self.java_class
        )

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.java_class)
