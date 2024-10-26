import pandas as pd

error_types = {
        "省略 (Omission)": {'個数': 0, '単語': []},  # Omission
        "挿入 (Insertion)": {'個数': 0, '単語': []},  # Insertion
        "発音ミス (Mispronunciation)": {'個数': 0, '単語': []},  # Mispronunciation
        "不適切な間 (UnexpectedBreak)": {'個数': 0, '単語': []},  # UnexpectedBreak
        "間の欠如 (MissingBreak)": {'個数': 0, '単語': []},  # MissingBreak
        "単調 (Monotone)": {'個数': 0, '単語': []},  # Monotone
    }

df = pd.DataFrame.from_dict(error_types, orient='index')
print(df.loc['省略 (Omission)', '個数'])