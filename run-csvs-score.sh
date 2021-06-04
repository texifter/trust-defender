#!/bin/bash

# import nltk
# nltk.download('punkt')

DataPath=$1
InputFilenameNoExt=$2

display_usage()
{
    echo "Usage: run-csvs-score.sh {data_path} {base_filename}"
}

if [ "$DataPath" == "" ]; then
    echo "Missing data path"
    $(display_usage)
    exit 1
fi

if [ "$InputFilenameNoExt" == "" ]; then
    echo "Missing base filename"
    $(display_usage)
    exit 1
fi

TwitterCredentials="./active_twitter_auth.json"
NNModel="./resources/model-is_bot_nnet.dat"
NGramModel="./resources/model-is_bot_user_desc_ngram_class.dat"
FullInputPath="$DataPath/$InputFilenameNoExt.csv"
ExtractOutputPath="$DataPath/$InputFilenameNoExt.userdat.csv"
FinalOutputPath="$DataPath/$InputFilenameNoExt.scored.csv"

python extract_users_from_csvs.py -i $FullInputPath -o $ExtractOutputPath -c $TwitterCredentials
python run_nnet.py -i $ExtractOutputPath -o $FinalOutputPath -n $NNModel -m $NGramModel
