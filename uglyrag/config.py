import configparser
import threading
from pathlib import Path

import appdirs


# 单例修饰器
def singleton(cls):
    instances = {}
    lock = threading.Lock()  # 锁对象，保证线程安全

    def get_instance(*args, **kwargs):
        with lock:  # 保证线程同步
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Config:
    def __init__(self):
        # 获取 XDG 配置目录
        config_dir = Path(appdirs.user_config_dir("UglyRAG", roaming=True))
        self.config = configparser.ConfigParser()
        # 读取 INI 文件
        self.config_path = config_dir / "config.ini"
        # 确保配置目录存在
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 读取配置文件
            self.config.read(self.config_path)
        except Exception as e:
            print(f"Error reading configuration file: {e}")
            # 可以选择在这里退出程序或采取其他措施

    def get(self, section, option):
        return self.config.get(section, option)

    def set(self, section, option, value):
        self.config.set(section, option, value)

    # 保存配置文件
    def save(self):
        # 文件不存在则创建
        self.config_path.touch(exist_ok=True)
        with self.config_path.open() as configfile:
            self.config.write(configfile)

    # 注销 Config 实例时，保存配置文件
    def __del__(self):
        self.save()
