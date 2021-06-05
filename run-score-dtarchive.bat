echo off

IF %1.==. GOTO Error1
IF %2.==. GOTO Error2
IF %3.==. GOTO Error3

SET DataPath=%1
SET InputFilenameNoExt=%2
SET ArchiveId=%3

SET TwitterCredentials=".\twitter_auth.json"
SET DTCredentials=".\dt_credentials.json"
SET NNModel=".\resources\model-is_good_or_bad_nnet.dat"
SET NGramModel=".\resources\model-is_good_or_bad_user_desc_ngram_class.dat"
SET FullInputPath="%DataPath%\%InputFilenameNoExt%.csv"
SET ExtractOutputPath="%DataPath%\%InputFilenameNoExt%_userdat.csv"
SET FinalOutputPath="%DataPath%\%InputFilenameNoExt%_scored.csv"

python extract_users_from_dt.py -i %DTCredentials% -a %ArchiveId% -o %FullInputPath%
python extract_users_from_csvs.py -i %FullInputPath% -o %ExtractOutputPath% -c %TwitterCredentials%
python run_nnet.py -i %ExtractOutputPath% -o %FinalOutputPath% -n %NNModel% -m %NGramModel%

GOTO EndScript

:Error3
	ECHO Missing parameter 3 for archive_id
GOTO EndError

:Error2
	ECHO Missing parameter 2 for data_filename_without_extension
GOTO EndError

:Error1
	ECHO Missing parameter 1 for data_path
GOTO EndError

:EndError
	ECHO ------
	ECHO Command:: run-score-dtarchive data_path data_filename_without_extension archive_id
	ECHO ------

:EndScript
