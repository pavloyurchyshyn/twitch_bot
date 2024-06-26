import os
import yaml
from logger import LOGGER
from game_components.singletone_decorator import single_tone_decorator

CONFIG_PATH = 'config.yaml'


def load_yaml_config(file: os.PathLike) -> dict:
    with open(file, encoding='utf-8') as f:
        data = yaml.safe_load(f)
        LOGGER.info(f'Loaded {file} config')
        return data


class BaseConfig(dict):
    file: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.raw = {}
        if self.file:
            self.load_config()

    def load_config(self):
        config_data = load_yaml_config(self.file)
        self.raw = config_data
        for k, v in config_data.items():
            self.set_value(k, v)

    def save(self):
        with open(self.file, 'w') as f:
            yaml.safe_dump(self, f)

    def set_value(self, k: str, v: str):
        self[k] = self.init_value(v)

    def init_value(self, value):
        if isinstance(value, dict):
            return BaseConfig(**self.init_dict(value))
        elif isinstance(value, list):
            return [self.init_value(v) for v in value]
        else:
            return value

    def init_dict(self, data: dict) -> dict:
        sub_config = {}
        for k, v in data.items():
            if isinstance(v, dict):
                c_ = {}
                for k_, v_ in data.items():
                    c_[k_] = self.init_value(v_)
                sub_config[k] = BaseConfig(**c_)
            else:
                sub_config[k] = self.init_value(v)

        return sub_config

    def __getattr__(self, item):
        return self.get(item)

    def __str__(self):
        return str(self)


@single_tone_decorator
class Config(BaseConfig):
    file: str = CONFIG_PATH


if __name__ == '__main__':
    config = Config()
    pass
