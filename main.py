import os
import concurrent.futures
import httpx
import argparse
from AlistClient.AlistClient import AlistClient
from dotenv import load_dotenv

ENV_MISSING = False
dotenv_exists = os.path.exists(".env")
if not dotenv_exists:
    print("No .env file found.")
for env in ["ALIST_HOST", "ALIST_USERNAME", "ALIST_PASSWORD"]:
    if env not in os.environ:
        ENV_MISSING = True
        print(f"{env} is not found in the environment variables.")
load_dotenv()
if not ENV_MISSING:
    client = AlistClient(os.getenv("ALIST_HOST"), os.getenv("ALIST_USERNAME"), os.getenv("ALIST_PASSWORD"))
print("-" * 10)


def get_all_files(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            file_paths.append(os.path.join(root, f))
    return file_paths


def snap_static_upload_file_executor(local_file_path: str, target_path: str, client_instance: AlistClient, overwrite: bool = True):
    print(f"Starting snap.static upload task: {local_file_path} to remote path: {target_path}, overwrite: {overwrite}")
    this_subdir = (local_file_path.replace("Snap.Static-main/", "").
                   replace("Snap.Static.Zip-main", "").
                   replace(local_file_path.split("/")[-1], ""))
    this_subdir = "" if this_subdir == "/" else this_subdir
    while True:
        try:
            res = client_instance.stream_upload(local_file_path, target_path + this_subdir, overwrite)
            print(f"Upload {local_file_path} result: {res}")
            break
        except httpx.ReadTimeout:
            print(f"Upload {local_file_path} ReadTimeout. Please check this later.")


def generic_upload_file_executor(local_file_path: str, target_path: str, client_instance: AlistClient,
                                 overwrite: bool = True):
    print(f"Starting generic upload task: {local_file_path} to remote path: {target_path}, overwrite: {overwrite}")
    while True:
        try:
            res = client_instance.stream_upload(local_file_path, target_path, overwrite)
            print(f"Upload {local_file_path} result: {res}")
            break
        except httpx.ReadTimeout:
            print(f"Upload {local_file_path} ReadTimeout. Please check this later.")


def zip_resource_handler(remote_path: str = "/zip", overwrite: bool = True):
    result = client.create_dir(remote_path)
    print(f"Create {remote_path} result: {result}")

    list_dir = list(f"Snap.Static.Zip-main/{f}" for f in os.listdir("Snap.Static.Zip-main") if f.endswith(".zip"))

    cpu_count = 1 if os.cpu_count() > 1 else os.cpu_count()

    with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
        futures = {executor.submit(snap_static_upload_file_executor, file, remote_path, client, overwrite) for file in list_dir}
        done, not_done = concurrent.futures.wait(futures, timeout=None)


def raw_resource_handler(remote_path: str = "/raw", overwrite: bool = True):
    # list all files in folder and subdirectory under /Snap.Static-main
    raw_file = list(file.replace("\\", "/") for file in get_all_files("Snap.Static-main") if file.endswith(".png"))
    all_remote_sub_dirs = []
    for file in raw_file:
        file_name = file.split("/")[-1]
        subdir = file.replace("Snap.Static-main/", "").replace(file_name, "")
        file_remote_path = f'{remote_path}/{subdir}'
        all_remote_sub_dirs.append(file_remote_path)
    all_remote_sub_dirs = list(set(all_remote_sub_dirs))

    for sub_dir in all_remote_sub_dirs:
        result = client.list_path(sub_dir)
        if "not found" in result["message"]:
            print(f"{sub_dir} not found. Creating...")
            result = client.create_dir(sub_dir)
            print(f"Create {sub_dir} result: {result}")
        else:
            print(f"{sub_dir} found.")
            
    # remote_path needs end with /
    if not remote_path.endswith("/"):
        remote_path = remote_path + "/"

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(snap_static_upload_file_executor, file, remote_path, client, overwrite) for file in raw_file}
        done, not_done = concurrent.futures.wait(futures, timeout=120)


def generic_resource_handler(local_file_path: str, target_remote_path: str, overwrite: bool = True):
    result = client.list_path(target_remote_path)
    if "not found" in result["message"]:
        print(f"{target_remote_path} not found. Creating...")
        result = client.create_dir(target_remote_path)
        print(f"Create {target_remote_path} result: {result}")
    else:
        print(f"{target_remote_path} found.")
    generic_upload_file_executor(local_file_path, target_remote_path, client, overwrite)


def main():
    parser = argparse.ArgumentParser(description="Upload resource to Alist")
    # specify the type of files to upload
    parser.add_argument("--type", required=True, help="Specify the type of files to upload.")
    parser.add_argument("--file", help="Specify the file to upload, only used for 'generic' type.")
    parser.add_argument("--target", help="Specify the target remote path, only used for 'generic' and 'zip' type.")
    # overwrite Alist login
    parser.add_argument("--host", help="Alist host")
    parser.add_argument("--username", help="Alist username")
    parser.add_argument("--password", help="Alist password")
    # overwrite existing file
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file")
    args = parser.parse_args()

    if args.host and args.username and args.password:
        global client
        client = AlistClient(args.host, args.username, args.password)
    overwrite = args.overwrite
    if args.type == "zip":
        # Needs to set ALIST_HOST, ALIST_USERNAME, ALIST_PASSWORD in environment variables or .env file
        # Use 1Password to load it in the GitHub Actions
        if ENV_MISSING:
            print("Missing environment variables. Please check .env file or set environment variables.")
            return
        zip_resource_handler(args.target, overwrite)
    elif args.type == "raw":
        if ENV_MISSING:
            print("Missing environment variables. Please check .env file or set environment variables.")
            return
        raw_resource_handler(args.target, overwrite)
    elif args.type == "generic":
        local_file_path = args.file
        target_remote_path = args.target
        generic_resource_handler(local_file_path, target_remote_path, overwrite)
    else:
        print(f"Invalid type: {args.type}. Please specify 'zip' or 'raw'.")


if __name__ == "__main__":
    main()
