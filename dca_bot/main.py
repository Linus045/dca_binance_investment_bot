import os

from dotenv import load_dotenv

from dca_investment_bot.config_manager import ConfigManager
from dca_investment_bot.DCAInvester import DCAInvester
from dca_investment_bot.logger import init_logger
from dca_investment_bot.logger import log_and_raise_exeption
from dca_investment_bot.logger import LOG_INFO
from dca_investment_bot.logger import LOG_WARNING_AND_NOTIFY
from dca_investment_bot.paths import Paths


def main():
    debug_tag = "[Main - Setup]"

    # TODO: make this path configurable via arguments or environment variables
    Paths.init_root_path(os.path.join(os.path.abspath(os.curdir)))

    config_manager = ConfigManager()
    config_manager.load_and_validate_config()
    init_logger(config_manager.log_level, config_manager.log_file)
    LOG_INFO(debug_tag, "Logger initialized")
    LOG_INFO(debug_tag, "Config file loaded")

    # load environment variables
    dotEnvPath = os.path.join(Paths.config_directory, ".env")
    if os.path.exists(dotEnvPath):
        load_dotenv(dotEnvPath)
    else:
        LOG_WARNING_AND_NOTIFY(debug_tag, "No .env file found at {}", dotEnvPath)

    invester = DCAInvester(config_manager)
    invester.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_and_raise_exeption(e, raise_exception=True)
