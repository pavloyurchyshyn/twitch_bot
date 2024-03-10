memory = {}


def single_tone_decorator(cls):
    def wrapper(**kwargs):
        if cls.__name__ not in memory:
            memory[cls.__name__] = cls(**kwargs)

        return memory[cls.__name__]

    return wrapper
