import yaml

CONFIG_PATH = 'config.yaml'


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Config(dict, metaclass=SingletonMeta):
    file = CONFIG_PATH

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_config(self):
        with open(self.file) as f:
            for k, v in yaml.safe_load(f).items():
                self.set_value(k, v)

    def set_value(self, k: str, v: str):
        super().__setitem__(k, self.init_value(v))

    def init_value(self, value):
        if isinstance(value, dict):
            return self.init_dict(value)
        elif isinstance(value, list):
            return [self.init_value(v) for v in value]
        else:
            return value

    def init_dict(self, data: dict) -> 'Config':
        sub_config = Config()
        for k, v in data.items():
            if isinstance(v, dict):
                sub_config[k] = {k_: v_ for k_, v_ in data.items()}
            else:
                sub_config[k] = self.init_value(v)

        return sub_config

    def __getattr__(self, item):
        return self.get(item)
