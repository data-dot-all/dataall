def iterable_to_scala_list(jvm, iterable):
    return jvm.scala.collection.JavaConversions.iterableAsScalaIterable(
        iterable
    ).toList()


def iterable_to_scala_set(jvm, iterable):
    return jvm.scala.collection.JavaConversions.iterableAsScalaIterable(
        iterable
    ).toSet()


def iterable_to_scala_seq(jvm, iterable):
    return jvm.scala.collection.JavaConversions.iterableAsScalaIterable(
        iterable
    ).toSeq()


def simple_date_format(jvm, s):
    return jvm.java.text.SimpleDateFormat(s)


def tuple2(jvm, t):
    return jvm.scala.Tuple2(*t)


def option(jvm, java_obj):
    return jvm.scala.Option.apply(java_obj)


def scala_none(jvm):
    return getattr(getattr(jvm.scala, "None$"), "MODULE$")


class scala_function1:
    def __init__(self, gateway, lambda_function):
        self.gateway = gateway
        self.lambda_function = lambda_function

    def apply(self, arg):
        return self.lambda_function(arg)

    class Java:
        implements = ["scala.Function1"]
