import os
import functools as ft
import zlib
import lzma
import gzip
import bz2
from pprint import pp
import subprocess
import songs_handling

# DECLARATIONS
available_compressors=[
        "zlib",
        "lzma",
        "gzip",
        "bz2"
    ]
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
flags={
    "Process" : 1, # 0: generate Database, 1:Classify input file
    "Compressor": available_compressors[0],
    "wavFile": progPATHS["Database"] + "\\" +  "Adeste-Fideles-Shorter.wav",
    "sampleStart": 0.3, # percentage of duration of the sample
    "sampleDuration": 10, # time in seconds. When 0 it uses the full wavFile as the sample file
    "noiseLevel": 1 #percentage of noise
 }

# SIGNATURES
def sig_file_name (wav_filename, p=temp):
    return progPATHS[p] + "\\"+ os.path.basename(wav_filename) + ".sig"

def getmaxfreqs_signatures(filename, p = temp):
    if(str(filename).endswith(".wav") and os.path.exists(filename)):
        sigFile = sig_file_name(filename,p)
        cmd = [GetMaxFreqs, "-w", sigFile, os.path.realpath(filename)]
        r = subprocess.run(cmd)
        print(r)
        if(r.returncode==0):
            return [0,sigFile]
        else:
            return [1,f"File not found. Please check if the file exists and if it is a WAV file. [FILE: {filename}]"]
    else:
        return [1,"Error"]

# DATABASE
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

    audio_file = flags["wavFile"]
    afn = os.path.basename(audio_file)
    sample_file = ""
    sfn = ""

    alg = flags["Compressor"]
    sampleStart = flags["sampleStart"]
    sampleDuration = flags["sampleDuration"]
    noiseLevel = float(flags["noiseLevel"]*0.5)

    #get sample from input
    if(sampleDuration>0): 
        audioprocessor = songs_handling.AudioProcessor(audio_file,None)    
        duration = audioprocessor._get_audio_duration()
        segment_start_time = round(flags["sampleStart"]*duration)
        segment_duration = int(min(flags["sampleDuration"], duration - segment_start_time))
        segment_filename = str(afn)
        segment_filename = segment_filename.replace(".wav",f"_s{segment_start_time}_d{segment_duration}.wav") 
        segment_file = os.path.join(progPATHS["temp"], segment_filename)
        audioprocessor.output_audio = segment_file
        audioprocessor._extract_segment(start_time=segment_start_time, duration=segment_duration)

        # Add noise to the segment
        if(os.path.exists(segment_file)): 
            if(flags["noiseLevel"]>0):
                noised_output_file = segment_file
                noised_output_file = noised_output_file.replace(".wav",f"_n{int(flags["noiseLevel"]*100)}.wav")
                noise_processor = songs_handling.AudioProcessor(segment_file, noised_output_file)
                noise_processor._add_noise(noise_duration=segment_duration, noise_level=noiseLevel)
                if(os.path.exists(noised_output_file)):
                    sample_file = noised_output_file
                else:
                    return [1,f"Error while adding noise to the segment of audio file {audio_file}"]        
            else:
                sample_file = segment_file
        else:
            return [1,f"Error while generating segment of audio file {audio_file}"]
        
    else:
        sample_file = audio_file

    # Final Sample Definition
    sfn = os.path.basename(sample_file)

    #create signature file
    if (not(os.path.exists(sample_file))):
        return [1, f"Sample File not found [{sample_file}]"]
    
    r=getmaxfreqs_signatures(sample_file)
    if(r[0] != 0):
        return r
    
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
            s = ncd(sample_to_predict, train_binary, globals()[f"compress_{alg}"])
            scores["byScore"][s] = file.removesuffix('.sig')
            if scores["byScore"][s] == afn:
                scores["byFile"] = s
            
    # delete temporary files
    for f in os.listdir(progPATHS[temp]):
        os.remove(progPATHS[temp]+"\\"+f)

    # results = dict()
    # # Find the smallest distance according to each algorithm
    # for alg in available_compressors:
    #     results[alg] = sorted(scores, key=lambda res: res[alg])[0]["file"]
    # pp(results)
    ncdBestScore = sorted(list(dict(scores["byScore"]).keys()))[0]
    res = []
    return [
        0,
        f'''Guessing file {afn} with {flags['Compressor']} compression:
        - Original file: {afn} (NCD score: {scores['byFile']})
        - Guessed file: {scores['byScore'][ncdBestScore]} (NCD score: {ncdBestScore})''',
        f"{afn},{scores['byScore'][ncdBestScore]},{ncdBestScore},{alg},{sampleStart},{sampleDuration},{noiseLevel}"
        ]


if __name__ == "__main__":
    #Parse arguments

    #Program Execussion
    result = []
    match flags["Process"]:
        case 0:
            result = gen_database()
        case 1:
            result = main()

    print (result[1])
            
