# This is a sample Python script.

# Press ⇧F10 to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import logging

import fire


class CatalogerPythonEngine:

    def __init__(self) -> None:
        super().__init__()


class MainDefaultTest:

    @staticmethod
    def test():
        print('Hi, test')


logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)

if __name__ == '__main__':
    fire.Fire(CatalogerPythonEngine)
