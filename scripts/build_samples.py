"""Builds the demo mailbox: samples/*.eml + samples/index.json"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from phishlens.samples import build  # noqa: E402

for s in build("samples"):
    print(f"{s['id']:22s} {s['truth']:9s} {s['title']}")
