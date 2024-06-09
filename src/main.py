import os
import functools as ft
import zlib
import lzma
import gzip
import bz2
from pprint import pp
import subprocess

# DECLARATIONS
available_compressors=[
        "zlib",
        "lzma",
        "gzip",
        "bz2"
    ]

flags={
    "Process" : 0, # 0: generate Database, 1:Classify input file
    "Compressor": available_compressors[0]
}

data_path = os.path.realpath(__file__).replace("src\\"+os.path.basename(__file__),"Data\\")
Database = "Database"
temp = "temp"
Signatures = "Signatures"
progPATHS = {
    "Database": data_path+Database,
    "temp": data_path+temp,
    "Signatures": data_path+Signatures
}

GetMaxFreqs = os.path.realpath(__file__).replace("src\\"+os.path.basename(__file__),"GetMaxFreqs\\bin\\GetMaxFreqs.exe")

# Signatures
def sig_file_name (wav_filename, p=temp):
    return progPATHS[p] + "\\"+ os.path.basename(wav_filename) + ".sig"

def getmaxfreqs_signatures(filename, p = temp):
    if(str(filename).endswith(".wav") and os.path.exists(filename)):
        sigFile = sig_file_name(filename,p)
        cmd = [GetMaxFreqs, "-w", sigFile, os.path.realpath(filename)]
        if(subprocess.run(cmd)==0):
            return [0,sigFile]
        else:
            return [1,f"File not found. Please check if the file exists and if it is a WAV file. [FILE: {filename}]"]
    else:
        return [1,"Error"]

def gen_database():
    #generate signatures
    ls=list(filter(lambda f : f.endswith(".wav"), list(os.listdir(progPATHS[Database]))))
    if (len(ls)==0):
        return [1,f"DATABASE: No WAV files found on {progPATHS[Database]}"]
    
    for file in ls:
        ffile = progPATHS[Database]+"\\"+file
        ffileSig = sig_file_name(progPATHS[Database]+"\\"+file,Signatures)
        if (os.path.exists(ffileSig)):
            os.remove(ffileSig)
        getmaxfreqs_signatures(ffile,Signatures)

    sigls = os.listdir(progPATHS["Signatures"])
    if(len(sigls)!= len(ls)):
        return [1,f"DATABASE: Signature files not generated for all Database files"]
    else:
        return [0,"OK"]

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
    # algorithms = [
    #     "zlib",
    #     "lzma",
    #     "gzip",
    #     "bz2"
    # ]


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
                    for alg in available_compressors
                }
            })

    results = dict()
    # Find the smallest distance according to each algorithm
    for alg in available_compressors:
        results[alg] = sorted(scores, key=lambda res: res[alg])[0]["file"]
    pp(results)


if __name__ == "__main__":
    
    

    match flags["Process"]:
        case 0:
            gen_database()
        case _,1:
            main()
            
