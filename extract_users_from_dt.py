import argparse
import collections
from discovertext_api import DiscoverTextApi
import pandas as pd

dt_api = None


def print_item_list(item_list):
    print("------------------------------------------------------------------")
    print("ID       Timestamp                Name")
    for item in item_list:
        print(f'{item["id"]:6}   {item["timestamp"]:24} {item["name"]}')
    print("----")


def extract_and_save(project_id, entity_type, entity_id, entity_name, output_file=None):
    screen_names = collections.Counter()
    current_offset = 0
    while True:
        if entity_type == "archive":
            current_units = dt_api.get_archive_units(
                entity_id, offset=current_offset, limit=100, include_metadata=True)
        elif entity_type == "bucket":
            current_units = dt_api.get_bucket_units(
                entity_id, offset=current_offset, limit=100, include_metadata=True)
        if not current_units:
            break
        max_limit = current_units["meta"]["count"]
        print(f"offset {current_offset} out of {max_limit}")

        if not "items" in current_units:
            break
        for this_item in current_units["items"]:
            if not "metadata" in this_item:
                continue
            screen_name_list = list(
                filter(lambda x: x["key"].startswith("screen_name"), this_item["metadata"]))
            if len(screen_name_list) > 0:
                screen_names.update({screen_name_list[0]["value"]: 1})

        current_offset += 100
        if current_offset >= max_limit:
            break

    print(f'Completed {entity_type}: "{entity_name}"')
    if output_file:
        output_filename = output_file
    else:
        output_filename = input(
            f"Gathered {len(screen_names)} total names. Output file: ")
    print(f'Writing output to: {output_filename}')
    df = pd.DataFrame.from_dict(screen_names, orient='index').reset_index()
    df = df.rename(columns={'index': 'Value', 0: 'Total'})
    df.to_csv(output_filename, encoding='utf8')


def extract_from_archive(project_id, bucket_id, bucket_name):
    print(f"Extracting from archive: {bucket_name}")
    extract_and_save(project_id, "archive", bucket_id, bucket_name)


def extract_from_bucket(project_id, bucket_id, bucket_name):
    print(f"Extracting from bucket: {bucket_name}")
    extract_and_save(project_id, "bucket", bucket_id, bucket_name)


def get_project_buckets(project_id, project_name):
    buckets = dt_api.get_project_buckets(project_id, limit=1000)
    bucket_list = sorted(map(lambda x: {
        "name": x["name"],
        "id": x["id"],
        "timestamp": x["timestamp"]
    }, buckets["items"]),
        key=lambda x: x["timestamp"],
        reverse=True)
    print_item_list(bucket_list)

    while True:
        bucket_id_str = input("BucketId to extract from (0 for exit): ")
        if not bucket_id_str:
            print_item_list(bucket_list)
            continue
        bucket_id = int(bucket_id_str)
        if bucket_id == 0:
            return
        selected_bucket = list(
            filter(lambda x: x["id"] == bucket_id, bucket_list))
        if (len(selected_bucket) == 0):
            print("unknown project id")
        else:
            extract_from_bucket(
                project_id, selected_bucket[0]["id"], selected_bucket[0]["name"])
            return


def get_project_archives(project_id, project_name):
    archives = dt_api.get_project_archives(project_id, limit=1000)
    archive_list = sorted(map(lambda x: {
        "name": x["name"],
        "id": x["id"],
        "timestamp": x["timestamp"]
    }, archives["items"]),
        key=lambda x: x["timestamp"],
        reverse=True)
    print_item_list(archive_list)

    while True:
        archive_id_str = input("ArchiveId to extract from (0 for exit): ")
        if not archive_id_str:
            print_item_list(archive_list)
            continue
        archive_id = int(archive_id_str)
        if archive_id == 0:
            return
        selecterd_archive_list = list(
            filter(lambda x: x["id"] == archive_id, archive_list))
        if (len(selecterd_archive_list) == 0):
            print("unknown archive id")
        else:
            extract_from_archive(
                project_id, selecterd_archive_list[0]["id"], selecterd_archive_list[0]["name"])
            return


def do_selected_project(project_id, project_name):
    while True:
        print("--------")
        print(f"Project: {project_name}")
        item_selection = input("archive or bucket (or exit)? ")
        if item_selection == "exit":
            return
        elif item_selection == "archive":
            get_project_archives(project_id, project_name)
        elif item_selection == "bucket":
            get_project_buckets(project_id, project_name)
        else:
            print("unknown function")


def do_project_select(project_list):
    print_item_list(project_list)
    while True:
        project_id_str = input("ProjectId (0 for exit): ")
        if not project_id_str:
            print_item_list(project_list)
            continue
        project_id = int(project_id_str)
        if project_id == 0:
            return
        selected_project = list(
            filter(lambda x: x["id"] == project_id, project_list))
        if (len(selected_project) == 0):
            print("unknown project id")
        else:
            do_selected_project(
                selected_project[0]["id"], selected_project[0]["name"])


def extract_from_cli_archive(archive_id, output_file):
    archive = dt_api.get_archive(archive_id)
    if not archive:
        print("unknown archive id")
        return

    print(f'Extracting from archive {archive_id}: {archive["name"]}')

    print(f'writing file to: {output_file}')

    extract_and_save(0, "archive", archive_id,
                     archive['name'], output_file=output_file)


def extract_from_cli_bucket(bucket_id, output_file):
    bucket = dt_api.get_bucket(bucket_id)
    if not bucket:
        print("unknown bucket id")
        return

    print(f'Extracting from bucket {bucket_id}: {bucket["name"]}')

    print(f'writing file to: {output_file}')

    extract_and_save(0, "bucket", bucket_id,
                     bucket['name'], output_file=output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input credential file")
    parser.add_argument("-a", "--archive", help="archive to extract from")
    parser.add_argument("-b", "--bucket", help="bucket to extract from")
    parser.add_argument("-o", "--output", help="output file")
    args = parser.parse_args()

    if not args.input:
        raise "missing input credential file"

    dt_api = DiscoverTextApi(credential_file=args.input)

    dt_api.login()

    if args.archive and args.bucket:
        raise "cannot use --archive and --bucket flag at the same time"

    if args.archive:
        extract_from_cli_archive(args.archive, args.output)
    elif args.bucket:
        extract_from_cli_bucket(args.bucket, args.output)
    else:
        projects = dt_api.get_projects(limit=1000)
        project_list = sorted(map(lambda x: {
            "name": x["name"],
            "id": x["id"],
            "timestamp": x["timestamp"]
        }, projects["items"]),
            key=lambda x: x["timestamp"],
            reverse=True)

        do_project_select(project_list)
