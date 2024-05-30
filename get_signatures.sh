#!/bin/bash

for filename in ./Data/*.wav; do
  echo $filename
  ./GetMaxFreqs/bin/GetMaxFreqs -v -w "Data/$(basename "$filename").sig" $filename
done