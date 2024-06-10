# NCD
Develop and test a setup using NCD for the automatic  identification of musics.

**Usage** 

Generate the Database:

To generate the database by creating signatures for all WAV files in the Data/Database directory:
```
python taizam.py <process_number>
```
**(Process) 0:** Process to generate the database

**Example:**
```
python taizam.py 0
```

**Classify Input File**
To classify an input WAV file based on the generated database:

```
python taizam.py <process_number> <compressor> <wavFile> --sampleStart <sampleStart> --sampleDuration <sampleDuration> --noiseLevel <noiseLevel>
```
**(Process) 1:** Process to classify the input file

**compressor:** Choose the compressor (zlib, lzma, gzip, bz2)

**wavFile:** Path to the WAV file to process

**--sampleStart:** Percentage(s) of the duration of the sample (multiple values allowed)

**--sampleDuration:** Time(s) in seconds for the sample duration (multiple values allowed)

**--noiseLevel:** Percentage(s) of noise to add (multiple values allowed)
