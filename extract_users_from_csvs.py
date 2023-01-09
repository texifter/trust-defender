import argparse
from datetime import datetime, timezone
import glob
import pandas as pd
import os
import timestring
from utils import batch_list
from nltk import word_tokenize
from utils import get_hashtag_count, get_list_item_count, get_url_count, get_twitter_auth
import tweepy

SCREEN_NAME_COLUMN = 'Value'

twitter_api = None


def get_user_add_props(input_bio):
    bio_text = input_bio
    if not bio_text:
        bio_text = ""
    bio_text = bio_text.strip()
    tokens = word_tokenize(bio_text)
    tokens_terms_only = [word.lower() for word in tokens if word.isalpha()]

    desc_len_terms = len(tokens_terms_only)
    desc_len_chars = len(bio_text)
    num_list_items = get_list_item_count(bio_text)
    num_hashtags = get_hashtag_count(tokens)
    url_count = get_url_count(bio_text)

    return desc_len_terms, desc_len_chars, num_list_items, num_hashtags, url_count


def get_val(user_object, attribute_name):
    return getattr(user_object, attribute_name, None)


def get_twitter_api_batch(this_batch):
    retry_count = 0
    while True:
        try:
            user_data = twitter_api.lookup_users(screen_name=this_batch)
            return user_data
        except Exception as e:
            retry_count += 1
            if (retry_count > 3):
                print(
                    f'!! exception getting Twitter API data... retry {retry_count} of 3...')
            else:
                print(f'exception: {e}')
                print('... too many retrys... skipping...')
                return None


def get_batched_user_data(this_batch, todays_date):
    ret = []
    user_data = get_twitter_api_batch(this_batch)
    if not user_data:
        return []
    for this_user in user_data:
        user_create_date_str = get_val(this_user, "created_at")
        if not user_create_date_str:
            continue

        user_create_date = timestring.Date(user_create_date_str)

        num_statuses = int(get_val(this_user, "statuses_count"))
        follower_count = int(get_val(this_user, "followers_count"))
        following_count = int(get_val(this_user, "friends_count"))
        location = get_val(this_user, "location")

        num_days = (todays_date - user_create_date.date).days
        if num_days == 0:
            num_days = 1

        desc_len_terms, desc_len_chars, num_list_items, num_hashtags, url_count = get_user_add_props(
            get_val(this_user, "description"))

        ret_user = {
            "userid": get_val(this_user, "id"),
            "user_display_name": get_val(this_user, "name"),
            "user_screen_name": get_val(this_user, "screen_name"),
            "user_reported_location": location,
            "user_profile_description": get_val(this_user, "description"),
            "status_count": num_statuses,
            "follower_count": follower_count,
            "following_count": following_count,
            "num_days": num_days,
            "account_creation_date": user_create_date,
            "account_language": get_val(this_user, "id"),
            "statuses_per_day": num_statuses / num_days,
            "followers_per_day": follower_count / num_days,
            "following_per_day": following_count / num_days,
            "desc_len_terms": desc_len_terms,
            "desc_len_chars": desc_len_chars,
            "num_list_items": num_list_items,
            "num_hashtags": num_hashtags,
            "url_count": url_count,
            "has_location": 1 if location else 0,
            "verified": get_val(this_user, "verified")
        }
        ret.append(ret_user)
    return ret


def get_user_data(screen_names):
    ret = []
    todays_date = datetime.now(timezone.utc)
    for this_batch in batch_list(screen_names, 100):
        print(
            f'...getting batch of {len(this_batch)} from "{this_batch[0]}" to "{this_batch[-1]}"...')
        twitter_batch_data = get_batched_user_data(this_batch, todays_date)
        print(f'... got user data for {len(twitter_batch_data)} users...')
        if twitter_batch_data:
            ret.extend(twitter_batch_data)
        print(f'... gotten so far: {len(ret)}')
    return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input directory or file")
    parser.add_argument("-o", "--output", help="output file")
    parser.add_argument("-c", "--credentials", help="twitter credentials file")
    args = parser.parse_args()

    if not args.input:
        raise "missing input directory or file"
    if not args.output:
        raise "missing output file"
    if not args.credentials:
        raise "missing credentials file"

    twitter_app_auth = get_twitter_auth(args.credentials)
    twitter_auth = tweepy.OAuthHandler(
        twitter_app_auth["consumer_key"], twitter_app_auth["consumer_secret"])
    twitter_auth.set_access_token(
        twitter_app_auth["access_token"], twitter_app_auth["access_secret"])
    twitter_api = tweepy.API(twitter_auth, wait_on_rate_limit=True)

    if os.path.isdir(args.input):
        all_files = glob.glob(os.path.join(args.input, "*.csv"))
    elif os.path.isfile(args.input):
        all_files = [args.input]
    else:
        raise "Unknown input"

    all_file_len = len(all_files)
    print(f'... found {all_file_len} items')
    screen_names = {}
    f_counter = 0
    for this_file in all_files:
        print(f'... reading {this_file}')
        df = pd.read_csv(this_file, keep_default_na=False)
        for index, row in df.iterrows():
            this_screen_name = row[SCREEN_NAME_COLUMN]
            if this_screen_name not in screen_names:
                screen_names[this_screen_name] = True
        f_counter += 1
        print(f'... processed {f_counter} of {all_file_len}')

    print(f'Found a total of {len(screen_names)} users')

    all_users = get_user_data(screen_names.keys())
    print(f'total output of {len(all_users)} users...')

    df_out = pd.DataFrame(all_users)
    df_out.to_csv(args.output)
