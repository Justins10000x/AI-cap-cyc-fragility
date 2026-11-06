"""Boom vs bubble: can the test tell rising earnings from rising multiples?
Writes results/boom_vs_bubble.csv.   Usage: python src/boom_vs_bubble.py [M]"""
import sys
import pandas as pd
from fundamentals import boom_vs_bubble_study

M = int(sys.argv[1]) if len(sys.argv) > 1 else 300
r = boom_vs_bubble_study(M=M, seed=5)
df = pd.DataFrame([dict(world=k, reject_price=v["price"], reject_ratio=v["ratio"]) for k, v in r.items()])
df.to_csv("results/boom_vs_bubble.csv", index=False)
print(df.to_string(index=False))
