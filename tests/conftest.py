import configparser


def dict_to_config(config_dict: dict) -> configparser.ConfigParser:
    """辞書をConfigParserオブジェクトに変換する"""
    config = configparser.ConfigParser()
    string_dict: dict[str, dict[str, str]] = {}
    for section, options in config_dict.items():
        string_dict[section] = {key: str(value) for key, value in options.items()}
    config.read_dict(string_dict)
    return config
