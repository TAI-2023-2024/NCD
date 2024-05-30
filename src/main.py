import os
import functools as ft
import zlib
import lzma
import gzip
import bz2
from pprint import pp

# different functions C for NCD
@ft.lru_cache()
def compress_zlib(data):
    return len(zlib.compress(data))


@ft.lru_cache()
def compress_lzma(data):
    return len(lzma.compress(data))


@ft.lru_cache()
def compress_gzip(data):
    return len(gzip.compress(data))


@ft.lru_cache()
def compress_bz2(data):
    return len(bz2.compress(data))


def ncd(sample, train_sample, fn):
    # X + Y
    cxy = fn(sample + train_sample)
    # X
    cx = fn(sample)
    # Y
    cy = fn(train_sample)

    # formula
    return (cxy - min(cx, cy)) / max(cx, cy)


def main():
    algorithms = [
        "zlib",
        "lzma",
        "gzip",
        "bz2"
    ]

    scores = list()
    # read signature file to predict
    sample_to_predict = open("../sample07.wav.sig", "rb").read()
    dataset = "../Data/"
    for file in os.listdir(dataset):
        if file.endswith(".sig"):
            train_binary = open(dataset + file, "rb").read()
            # For each algorithm, calculate the NCD
            scores.append({
                "file": file,
                **{
                    alg: ncd(sample_to_predict, train_binary, globals()[f"compress_{alg}"])
                    for alg in algorithms
                }
            })

    results = dict()
    # Find the smallest distance according to each algorithm
    for alg in algorithms:
        results[alg] = sorted(scores, key=lambda res: res[alg])[0]["file"]
    pp(results)


if __name__ == "__main__":
    main()
