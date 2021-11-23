## 1. Create venv (recommended to use python3.7)

    python3 -m venv env

## 2 Activate venv

    Linux:
    source env/bin/activate

    Windows:
    env\Scripts\activate.bat

## 3. Install program requirements

    (env) ...\dca_binance_investment_bot\dca_bot> python -m pip install -r requirements.txt

This contains the requirements for the program itself.

## 3. Install the source code as module

    (env) ...\dca_binance_investment_bot\dca_bot> python -m pip install -e .

This installs the source code as a module so dependencies can be referenced easier.
If you just wanna test/use the bot, you can stop here.

## 4. Install dev requirements

    (env) ...\dca_binance_investment_bot\dca_bot> python -m pip install -r requirements_dev.txt

This is necessary make verifying of the code easier and formats the code automatically to match the coding style.

## 6. Install pre-commit hooks

    (env) ...\dca_binance_investment_bot\dca_bot> pre-commit install

This installs the pre-commit git hooks for the project and makes it possible to run the pre-commit script automatically when committing.

## 7. Run Tests and pre-commit scripts manually
### pre-commit checks
To manually run the pre-commit script:

    (env) ...\dca_binance_investment_bot\dca_bot> pre-commit run --all-files

### Tox
Make sure you enabled the virtual environment.
Tox tests the code for multiple envioremnts (Python 3.7, 3.8, 3.9) and checks code with flake8 and mypy (only on Python Version 3.7).
To run Tox, move into the dca_bot directory and run:

        (env) ...\dca_binance_investment_bot\dca_bot> tox

### PyTest
Make sure you enabled the virtual environment.
PyTest runs the unit tests for the code.
To run PyTest, move into the dca_bot directory and run:

        (env) ...\dca_binance_investment_bot\dca_bot> pytest


### Flake8
Make sure you enabled the virtual environment.
Flake8 checks the code for errors and warnings.
To run Flake8, move into the dca_bot directory and run:

        (env) ...\dca_binance_investment_bot\dca_bot> flake8 src

### Black
Make sure you enabled the virtual environment.
Black formats the code to match the coding style.
To run Black, move into the dca_bot directory and run:

        (env) ...\dca_binance_investment_bot\dca_bot> black src

