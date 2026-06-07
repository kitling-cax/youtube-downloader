import os
import json

CONFIG_FILE = os.path.expanduser("~/.youtube_downloader_config.json")

# 敏感文件（cookie 等）存放到用户主目录下的隐藏文件夹中，
# 避免被误提交到 Git 仓库。
APP_DATA_DIR = os.path.expanduser("~/.youtube_downloader")
DEFAULT_COOKIE_FILE = os.path.join(APP_DATA_DIR, "cookie.txt")


def get_default_output_dir() -> str:
    """获取默认输出目录"""
    return os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")


def get_default_cookie_file() -> str:
    """获取默认 cookie 文件路径（位于用户主目录，不在项目内）"""
    return DEFAULT_COOKIE_FILE


def ensure_app_data_dir() -> None:
    """确保用户数据目录存在"""
    os.makedirs(APP_DATA_DIR, exist_ok=True)


def load_config() -> dict:
    """加载配置"""
    default_config = {
        'output_dir': get_default_output_dir(),
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default_config
    return default_config


def save_config(config: dict) -> None:
    """保存配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise Exception(f"Failed to save config: {e}")


def get_output_dir() -> str:
    """获取当前输出目录"""
    config = load_config()
    return config.get('output_dir', get_default_output_dir())


def set_output_dir(path: str) -> None:
    """设置输出目录并保存"""
    config = load_config()
    config['output_dir'] = path
    save_config(config)


def get_proxy() -> str:
    """获取代理设置"""
    config = load_config()
    return config.get('proxy', '')


def set_proxy(proxy: str) -> None:
    """设置代理并保存"""
    config = load_config()
    config['proxy'] = proxy
    save_config(config)
