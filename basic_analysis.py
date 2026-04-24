import pandas as pd

df = pd.read_csv(r"C:\Users\Jagrati suyal\Downloads\ROUND_1\ROUND1\prices_round_1_day_0.csv", sep=";")

import matplotlib.pyplot as plt

for p in df["product"].unique():
    temp = df[df["product"] == p]
    plt.figure(figsize=(10,4))
    plt.plot(temp["timestamp"], temp["mid_price"])
    plt.title(p)
    plt.show()