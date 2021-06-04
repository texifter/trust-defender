# Trust Defender - A Twitter User Bot Classifier

A collection of scripts used to train and run a classifier to classify Twitter users as potential bots.
The classifier models are based on Twitter user information and focuses heavily on the user bio description.

-   [Prerequisites](#Prerequisites)
-   [Basic Workflow (CSV file)](#Basic-Workflow-CSV-file)
-   [Basic Workflow (DiscoverText API)](#Basic-Workflow-DiscoverText-API)
-   [Basic Workflow (Gnip Raw Json)](#Basic-Workflow-Gnip-Raw-Json)
-   [Training and Re-training the model](#Training-and-Re-training-the-model)
-   [Individual Scripts](#Individual-Scripts)
-   [License](#License)

## Prerequisites

-   Python 3.6 or higher
-   If using Windows, you may need to use 32-bit python as there have been issues using the Pandas library on 64 bit
-   A Twitter Developer account with an application (https://developer.twitter.com/). You'll need the _Consumer API keys_ as well as a set of _Access token & access token secret_ pairs for the application.
-   (if connecting to the DiscoverText API), you'll need your DiscoverText API key, API secret, hostname, username, and password

### Credential Setup:

In the root directory, you'll find two files: `dt_credentials.json` and `twitter_auth.json`. Fill in the requested values for each. These files will be used as input to various scripts.

## Basic Workflow (CSV file)

The `run-csvs-score` helper script will run the following scripts:

1. it runs the [extract_users_from_csvs](#script-extract_users_from_csvs-py) script to transform the list of usernames to get their Twitter information
2. it then runs the [run_nnet](#script-run_nnet-py) script across the gathered Twitter data to score the user information

```
Usage: run-csvs-score {data_directory} {base_filename_without_ext}
```

## Basic Workflow (Using the DiscoverText API)

If you have an Enterprise-level DiscoverText account with API access, you can directly pull the list of username metadata
from a DiscoverText archive or bucket.

The `run-score-dtarchive` helper script performs the following:

1. Run the [extract_users_from_dt](#script-extract_users_from_dt-py) script to export a list of usernames from an archive or bucket
2. Run the [extract_users_from_csvs](#script-extract_users_from_csvs-py) script to transform the list of usernames to get their Twitter information
3. Run the [run_nnet](#script-run_nnet-py) script across the gathered Twitter data to score the user information

```
Usage: run-score-dtarchive {data_directory} {base_filename_without_ext} {archive_id}
```

## Training and Re-training the model

_(note: there are already well-tuned, pre-trained classifiers in place - only re-train if necessary)_
The pre-trained models can be found at:

-   `/resources/model-is_bot_nnet.dat`: Keras trained file for the neural network
-   `/resources/model-is_bot_nnet.dat.h5`: Keras trained file for the neural network
-   `/resources/model-is_bot_user_desc_ngram_class.dat`: the n-gram classifier pre-trained model

There are two primary classifier types:

-   an _n-gram_ naive bayes classifier model, which uses 5,6,7,8, and 9-gram models combined and results a probability score for two classes: `bot` or `good`
-   a neural network that takes as input:
    -   `p(bot)` (from the ngram classifier)
    -   `p(good)` (from the ngram classifier)
    -   number of days the Twitter account has been active
    -   average number of statuses per day
    -   average number of followers per day
    -   average number of following per day
    -   the description length in number of individual terms
    -   the number of "lists" in the description (e.g. `god, country, president` would be considedered a "list")
    -   the number of hashtags used in the description
    -   the number of URLs found in the description

Use the script [train_ngram_classifier.py](#script-train_ngram_classifier-py) to train the n-gram classifier.

```
Usage: python train_ngram_classifier.py -i {input_csv_file} -o {output_model_file}
```

The input data in `train_ngram_classifier.py` can be specified by modifying:

-   **CLASSES**: array of classes to be use
-   **TEXT_COLUMN**: the heading label of the column that contains the text to train on
-   **CLASS_COLUMN**: the heading label of the column that contains the correct class for the record

The script [train_nnet.py](#script-train_nnet-py) is used to train the neural network.

```
Usage: python train_nnet.py -i {input_csv_file}
                            -m {ngram_classifier_model_file}
                            -n {number_training_rounds}
                            -t {testing_file_csv_path}
                            -o {output_model_file}
```

## Individual Scripts:

-   [extract_users_from_csvs.py](#script-extract_users_from_csvs-py): Get Twitter user information from CSV username list
-   [extract_users_from_dt.py](#script-extract_users_from_dt-py): Extract Twitter usernames from a DiscoverText archive or bucket
-   [gather_bio_corpus_stats.py](#script-gather_bio_corpus_stats-py): Output various statistics for bios in a corpus
-   [run_nnet.py](#script-run_nnet-py): Runs the neural network model across Twitter user information
-   [split_training_data.py](#script-split_training_data-py): Splits a training CSV file into training and test sets
-   [train_ngram_classifier.py](#script-train_ngram_classifier-py): Trains the n-gram classifier
-   [train_nnet.py](#script-train_nnet-py): Trains the neural network

### script: extract_users_from_csvs.py

Reads in a file or directory of CSV files (primarily from DiscoverText metadata item exports), and gets Twitter information from the usernames.

```
Usage: extract_users_from_csvs.py -i (input_file) -o (output_file) -c (credentials_file)
```

-   input file is a CSV of usernames (in the `Value` column by default)
-   output file is a CSV of information for each of the Twitter users' bios
-   credentials file is your `twitter_auth.json` credentials

### script: extract_users_from_dt.py

Interactive or CLI script to extract and save usernames from a DiscoverText archive or bucket (to then further use to feed into extract_users_from_csvs.py)

```
Usage: extract_users_from_dt.py -i {DiscoverText_credentials}
                                [-a {archive_id} -o {output_file}]
                                [-b {bucket_id} -o {output_file}]
```

-   input file is your `dt_credentials.json` file
-   optionally, specifying the archive id and output file will extract and run from an archive
-   or, optionally, specifying the bucket id and output file will extract and run from a bucket
-   or, running interactivly, the script will prompt for information and ask where to save the output file to

### script: gather_bio_corpus_stats.py

Gathers a bit of supurious stat information about user bio data in a corpus

```
Usage: gather_bio_corpus_stats.py -i (input_file)
```

-   input file is the CSV output from extract_users_from_csvs.py

The output will be printed to the console with the top 100 terms, top 100 URLs, and top 100 hashtags.

### script: run_nnet.py

Runs the classifier and neural network, scoring Twitter data as bot or not.

```
Usage: run_nnet.py -i (input_file) -o (output_file) -n (neural_net_model) -m (ngram_model)
```

-   input file is the CSV output from extract_users_from_csvs.py
-   output file will be a CSV, same as the input, but augmented with bot scores
-   the neural net model is the path to the _is_bot_nnet.dat_ file
-   the ngram model is the path to the _is_bot_user_desc_ngram_class.dat_ file

### script: split_training_data.py

Splits training data into training and test data. Paths are configured within the script

### script: train_ngram_classifier.py

Trains the ngram classifier from training data.

```
Usage: train_ngram_classifier.py -i (input_file) -o (output_file)
```

-   input file is the training data CSV with user_profile_description and a class_value (bot or good)
-   output file is the .dat file with the trainined ngram model

### script: train_nnet.py

Trains and tests the neural network.

```
Usage: python train_nnet.py -i {input_csv_file}
                            -m {ngram_classifier_model_file}
                            -n {number_training_rounds}
                            -t {testing_file_csv_path}
                            -o {output_model_file}
```

-   input file is the training data CSV with user_profile_description and a class_value (bot or good)
-   ngram_model is the .dat file from the trained ngram classifier
-   number of rounds is the number of rounds to train
-   test file is the test CSV file used to gather accuracy testing
-   output file is the .dat files with the trained neural network model

## License

This software is licensed under the MIT license (see the [LICENSE](./LICENSE) file).

By using this code, you assume all responsibility for any damages, additional charges, and all issues.
