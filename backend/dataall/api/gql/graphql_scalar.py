class Scalar:
    def __init__(self, name):
        self.name = name

    def gql(self):
        return self.name


ID = Scalar(name='ID')
String = Scalar(name='String')
Boolean = Scalar(name='Boolean')
Integer = Scalar(name='Int')
Number = Scalar(name='Number')
Date = Scalar(name='Date')
AWSDateTime = Scalar(name='String')


scalars = (String, Boolean, Integer, Number, Date)
