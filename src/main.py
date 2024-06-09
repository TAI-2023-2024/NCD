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
    "Process" : 1, # 0: generate Database, 1:Classify input file
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

    #create signature file
    
    sample_file = progPATHS["Database"] + "\\" +  "Adeste-Fideles-Shorter.wav"
    sfn = os.path.basename(sample_file)

    if (not(os.path.exists(sample_file))):
        return [1, f"Sample File not found [{sample_file}]"]
    
    getmaxfreqs_signatures(sample_file)

    #scores = list()
    scores = {
        "byScore" : dict(), #key=score: value=filename
        "byFile"  : 1 #score with the real file signature compression
    } 
    # read signature file to predict
    sample_to_predict = open(sig_file_name(sample_file), "rb").read()
    #dataset = "../Data/"
    for file in os.listdir(progPATHS[Signatures]):
        if file.endswith(".sig"):
            train_binary = open(progPATHS[Signatures]+"\\"+file, "rb").read()
            # # For each algorithm, calculate the NCD
            # scores.append({
            #     "file": file,
            #     **{
            #         alg: ncd(sample_to_predict, train_binary, globals()[f"compress_{alg}"])
            #         for alg in available_compressors
            #     }
            # })
            alg = flags["Compressor"]
            s = ncd(sample_to_predict, train_binary, globals()[f"compress_{alg}"])
            scores["byScore"][s] = file.removesuffix('.sig')
            if scores["byScore"][s] == sfn:
                scores["byFile"] = s
            



    # results = dict()
    # # Find the smallest distance according to each algorithm
    # for alg in available_compressors:
    #     results[alg] = sorted(scores, key=lambda res: res[alg])[0]["file"]
    # pp(results)
    ncdBestScore = sorted(list(dict(scores["byScore"]).keys()))[0]
    res = []
    return [
        0,
        f'''Guessing file {sfn} with {flags['Compressor']} compression:
        - Original file: {sfn} (NCD score: {scores['byFile']})
        - Guessed file: {scores['byScore'][ncdBestScore]} (NCD score: {ncdBestScore})'''
        ]
if __name__ == "__main__":
    
    
    result = []
    match flags["Process"]:
        case 0:
            result = gen_database()
        case 1:
            result = main()

    print (result[1])
            
