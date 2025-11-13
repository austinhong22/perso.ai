import pandas as pd


def export_examples(path: str = "examples.xlsx") -> None:
    df = pd.DataFrame([{"question": "회사 정보는?", "answer": "예시 답변"}])
    df.to_excel(path, index=False)


if __name__ == "__main__":
    export_examples()





