from dca_investment_bot.DCAInvester import DCAInvester
from dca_investment_bot.logger import log_and_raise_exeption


def main():
    invester = DCAInvester()
    invester.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_and_raise_exeption(e, raise_exception=True)
