import argparse
import csv
import hashlib
import os
import shutil
import sys
from tempfile import TemporaryDirectory
import urllib.request


def validate_file(path, sha256_hash):
    hasher = hashlib.new("sha256")
    with open(path, "rb") as f:
        while chunk := f.read(65536):  # Read in 64KB chunks
            hasher.update(chunk)
        actual_hash = hasher.hexdigest()
        if sha256_hash != actual_hash:
            print(
                f"SHA256 hash for \"{path}\" does not match. "
                f"Expected: {sha256_hash}. "
                f"Actual: {actual_hash}",
                file=sys.stderr
            )
            return False
    return True


def get_sample_image_metadata(csv_file):
    image_metadata = []
    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=",")
        for row in reader:
            image_metadata.append(
                {
                    "file": row[0].strip(),
                    "url": row[1].strip(),
                    "sha256": row[2].strip()
                }
            )
    return image_metadata

def download_data(url, destination):
    base_name = os.path.basename(url)
    destination_file = os.path.join(destination, base_name)
    if os.path.exists(destination_file):
        return

    with TemporaryDirectory() as download_path:

        # if not os.path.exists()
        print("Downloading {}".format(url))
        test_file_path = os.path.join(download_path, base_name)

        urllib.request.urlretrieve(url, filename=test_file_path)
        if not os.path.exists(test_file_path):
            raise FileNotFoundError(
                "Failure to download file from {}".format(url))

        shutil.move(test_file_path, destination)

        print("{} successfully downloaded".format(
            os.path.split(test_file_path)[-1]))



def download_sample_files(download_path, csv_file):
    test_images_data = get_sample_image_metadata(csv_file)

    if not os.path.exists(download_path):
        os.makedirs(download_path)
    errors = []
    for test_image_record in test_images_data:
        url = test_image_record["url"]
        test_image = os.path.join(download_path, test_image_record["file"])
        if not os.path.exists(test_image):
            download_data(url, destination=download_path)
            if not os.path.exists(test_image):
                raise FileNotFoundError("Something happened when trying to download sample image")
        else:
            print(f"Skipping: \"{test_image_record['file']}\". Reason: Already downloaded.", file=sys.stderr)
        if not validate_file(test_image, test_image_record["sha256"]):
            errors.append("Expected hash value does not match")
    return errors

def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download_path", type=str, default=os.path.join(os.getcwd(), "sample_files"))
    script_path: str = os.path.dirname(__file__)
    parser.add_argument(
        "--csv_metadata",
        type=str,
        default=os.path.join(script_path, "samplefiles.csv")
    )
    return parser

def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    if errors := download_sample_files(args.download_path, args.csv_metadata):
        for error in errors:
            print(error, file=sys.stderr)
        sys.exit(1)
    print(f'Successfully downloaded sample files to "{args.download_path}"', file=sys.stderr)

if __name__ == '__main__':
    main()