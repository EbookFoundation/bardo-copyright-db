
class DataError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message

        for key, value in kwargs.items():
            setattr(self, key, value)

class LookupError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message

        for key, value in kwargs.items():
            setattr(self, key, value)
