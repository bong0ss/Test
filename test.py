import os

from dotenv import load_dotenv


load_dotenv()


def add():
    x = float(input("Podaj x: "))
    y = float(input("Podaj y: "))
    print(f"{x} + {y} = {x + y}")
    print(os.getenv("HIDDEN_KEY"))


if __name__ == "__main__":
    add()
