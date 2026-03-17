class ConsoleOutput:
    @staticmethod
    def print_director_box(output: str, ticker: str):
        print("\n" + "=" * 60)
        print(f"DIRECTOR ANSWER - {ticker}")
        print("=" * 60)
        print(output)
        print("=" * 60 + "\n")