class Maybe:
    def __init__(self, value):
        self.value = value
        self.is_nil = value is None

class Just(Maybe):
    def __init__(self, value):
        super().__init__(value)

class Nil(Maybe):
    def __init__(self):
        super().__init__(None)

