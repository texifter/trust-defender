from functools import reduce
import json

def batch_list(input_list, batch_size):
    def reducer(cumulator, item):
        if len(cumulator[-1]) < batch_size:
            cumulator[-1].append(item)
            return cumulator
        else:
            cumulator.append([item])
            return cumulator
    return reduce(reducer, input_list, [[]])


def get_twitter_auth(auth_file):
    with open(auth_file) as auth_file_handle:
        credentials = json.load(auth_file_handle)
        return {
            "consumer_key": credentials["consumer_key"],
            "consumer_secret": credentials["consumer_secret"],
            "access_token": credentials["access_token"],
            "access_secret": credentials["access_secret"]
        }
