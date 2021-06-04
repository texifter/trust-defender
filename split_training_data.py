import pandas as pd
from sklearn.model_selection import train_test_split

full_data_path = "./resources/training.csv"
class_label_field = "class_value"
user_desc_field = "user_profile_description"

output_paths = {
    "training": "./resources/test_trainingdata",
    "test": "./resources/test_testdata"
}

percent_test = 0.25


def combine_files(file_list, output_file):
    frames = []
    for this_file in file_list:
        df = pd.read_csv(this_file, keep_default_na=False)
        frames.append(df)
    out_df = pd.concat(frames)
    out_df = out_df.sample(frac=1).reset_index(drop=True)
    out_df.to_csv(output_file)


df = pd.read_csv(full_data_path, keep_default_na=False)
print(df.shape)
df = df[(df[user_desc_field].notnull()) &
        (df[user_desc_field].str.len() > 0)]
print(df.shape)
class_counts = df[class_label_field].value_counts()
classes = list(class_counts.keys())

print(f'class_counts: {class_counts}')

min_value = 9999999999
for this_class in classes:
    min_value = min_value if class_counts[this_class] > min_value else class_counts[this_class]

print(f'min value: {min_value}')

training_files = []
test_files = []

for this_class in classes:
    class_count = class_counts[this_class]
    num_samples = int(class_count if class_count <= min_value else min_value)
    print(f'sampling: {this_class}, {num_samples} items')
    values_sample_filter = df.loc[df[class_label_field] == this_class]
    print(f'... filtered...')
    values_sample = values_sample_filter.sample(num_samples)
    print(f'... sampled...')
    train, test = train_test_split(values_sample, test_size=percent_test)
    print(f'... split.')
    train_out_path = f'{output_paths["training"]}_{this_class}.csv'
    test_out_path = f'{output_paths["test"]}_{this_class}.csv'
    train.to_csv(train_out_path)
    test.to_csv(test_out_path)
    training_files.append(train_out_path)
    test_files.append(test_out_path)

combine_files(training_files, f'{output_paths["training"]}.csv')
combine_files(test_files, f'{output_paths["test"]}.csv')
