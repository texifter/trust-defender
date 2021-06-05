echo off

IF %1.==. GOTO Error1
IF %2.==. GOTO Error2

SET DataPath=%1
SET InputFilenameNoExt=%2

SET TwitterCredentials=".\twitter_auth.json"
SET NNModel=".\resources\model-is_good_or_bad_nnet.dat"
SET NGramModel=".\resources\model-is_good_or_bad_user_desc_ngram_class.dat"
SET FullInputPath="%DataPath%\%InputFilenameNoExt%.csv"
SET ExtractOutputPath="%DataPath%\%InputFilenameNoExt%_userdat.csv"
SET FinalOutputPath="%DataPath%\%InputFilenameNoExt%_scored.csv"

python extract_users_from_csvs.py -i %FullInputPath% -o %ExtractOutputPath% -c %TwitterCredentials%
python run_nnet.py -i %ExtractOutputPath% -o %FinalOutputPath% -n %NNModel% -m %NGramModel%

GOTO EndScript

:Error1
	ECHO Missing parameter 1 for path_to_data
GOTO EndError

:Error2
	ECHO Missing parameter 2 for data_filename_without_extension
GOTO EndError

:EndError
	ECHO ------
	ECHO Command:: run-csvs-score path_to_data data_filename_without_extension
	ECHO ------

:EndScript
