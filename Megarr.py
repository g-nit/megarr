import os
import sys
import base64
import platform
import tarfile
import tempfile
import requests
import shutil
import subprocess
import pexpect

os.system("")
C_YAN = "\033[36m"
RESET = "\033[0m"

CONFIG_FILE = os.path.expanduser("~/.megarr_config")

def save_path(path):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"download_path={path}")

def load_path():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if line.startswith("download_path="):
                return line.split("=", 1)[1].strip()
    return None

def multi_b64_decode(data):
    previous = None
    while True:
        try:
            decoded = base64.b64decode(data, validate=True)
            decoded = decoded.decode("utf-8")
            if decoded == previous:
                break
            previous = decoded
            data = decoded
        except Exception:
            break
    return data

def is_megatools_installed():
    """Check if `megatools` command is available on PATH."""
    return shutil.which("megatools") is not None or shutil.which("megatools.exe") is not None

def get_download_url():
    """Determine correct megatools build URL based on OS/arch."""
    base = "https://xff.cz/megatools/builds/builds/"
    system = platform.system().lower()
    arch = platform.machine().lower()

    # Map system + arch to correct filename
    # This is not exhaustive, adjust based on available builds from xff.cz
    if system == "linux":
        if arch in ("x86_64", "amd64"):
            return base + "megatools-1.11.5.20250706-linux-x86_64.tar.gz"
        elif "arm" in arch or "aarch64" in arch:
            return base + "megatools-1.11.5.20250706-linux-aarch64.tar.gz"
        # Add more architectures if needed
    elif system == "windows":
        # Note: build site has .zip for windows
        if arch in ("amd64", "x86_64"):
            return base + "megatools-1.11.5.20250706-win64.zip"
        elif arch in ("x86", "i386"):
            return base + "megatools-1.11.5.20250706-win32.zip"

    return None

def download_and_extract(url, dest_dir):
    """Download the megatools archive and extract it to dest_dir."""
    print(f"Downloading megatools from {url} …")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    with tmp_file as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    tmp_path = tmp_file.name

    # Handle .tar.gz or .zip
    if url.endswith(".tar.gz"):
        print("Extracting tar.gz …")
        with tarfile.open(tmp_path, "r:gz") as tar:
            # Use safe extract
            def is_within_directory(directory, target):
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
                return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

            def safe_extract(tar_obj, path=".", members=None):
                for member in tar_obj.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
                tar_obj.extractall(path, members)

            safe_extract(tar, path=dest_dir)
    elif url.endswith(".zip"):
        print("Extracting zip …")
        shutil.unpack_archive(tmp_path, dest_dir)
    else:
        print("Unknown archive format for megatools!")
        os.remove(tmp_path)
        return False

    os.remove(tmp_path)
    return True

def ensure_megatools():
    if is_megatools_installed():
        print("megatools is already installed.")
        return "megatools"  # we can just call `megatools`
    else:
        print("megatools is not installed or not on PATH.")
        url = get_download_url()
        if not url:
            print("Could not find a pre-built megatools binary for your OS/architecture.")
            return None

        choice = input(f"Do you want me to download megatools from {url}? (y/N): ").strip().lower()
        if choice != "y":
            print("Okay, you can install megatools manually from https://xff.cz/megatools/builds/builds/")
            return None

        # Download to a local folder, e.g. inside user home under `.megarr_tools`
        dest = os.path.expanduser("~/.megarr_tools")
        os.makedirs(dest, exist_ok=True)

        success = download_and_extract(url, dest)
        if not success:
            print("Failed to download or extract megatools.")
            return None

        # Find an executable inside dest
        # On Linux: might be `megatools` binary in extracted folder
        # On Windows: maybe `megatools.exe` in the zip
        for root, dirs, files in os.walk(dest):
            for fname in files:
                if fname.startswith("megatools"):
                    megatools_path = os.path.join(root, fname)
                    # Make it executable on Linux
                    try:
                        os.chmod(megatools_path, 0o755)
                    except Exception:
                        pass
                    print("Using megatools at:", megatools_path)
                    return megatools_path

        print("Could not find megatools executable after extraction.")
        return None


# -------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------

# ========== Main Script ==========

def main():
    megatools_path = ensure_megatools()

def is_megalink(data):
    """Simple check if input looks like a Mega link."""
    return data.startswith("https://mega.nz/") or "!" in data

while True:
    os.system("cls" if platform.system().lower().startswith("win") else "clear")

    # ASCII LOGO
    print(C_YAN + r"""
███╗   ███╗███████╗ ██████╗  █████╗ ██████╗ ██████╗
████╗ ████║██╔════╝██╔════╝ ██╔══██╗██╔══██╗██╔══██╗
██╔████╔██║█████╗  ██║  ██║ ███████║██████╔╝██████╔╝
██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║██╔══██╗██╔══██╗
██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║██║  ██║██║  ██║
╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
                 BASE64 → MEGATOOLS
""")

    print("0) Exit")
    print("1) Set Download Path")
    print("2) Download Megatools (if not installed)\n\n")

    user_input = input("Enter Base64 or Mega link (or 0 to exit): ").strip()
    if user_input == "0":
        print("Goodbye!")
        break
    elif user_input == "1":
        new_path = input("Enter new download path: ").strip()
        save_path(new_path)
        print("Saved!")
        continue
    elif user_input == "2":
        megatools_path = ensure_megatools()
        input("Press Enter to continue…")
        continue

    # Detect if it's a Mega link or Base64
    if is_megalink(user_input):
        megalink = user_input
        decoded = megalink  # no decoding needed
        print("\nDetected Mega link, proceeding directly…")
    else:
        decoded = multi_b64_decode(user_input)
        print("\nDecoded Base64:", decoded)

    current_path = load_path()
    print("Current download path:", current_path or "[Not set]")

    print("\nChoose action:")
    print("0) Exit")
    
    print("1) megatools dl")
    print("2) megatools dl --choose-files")
    print("3) Decode another input")
    print("4) Set Download Path")

    choice = input("Select 0-4: ").strip()
    if choice == "0":
        new_path = input("Enter new download path: ").strip()
        save_path(new_path)
        continue
    elif choice == "1":
        if not current_path:
            print("Error: no download path set.")
            continue
        cmd = f'"{megatools_path}" dl --path "{current_path}" "{decoded}"'
    elif choice == "2":
        if not current_path:
            print("Error: no download path set.")
            continue
        cmd = f'"{megatools_path}" dl --choose-files --path "{current_path}" "{decoded}"'
    elif choice == "3":
        continue
    elif choice == "0":
        print("Exiting...")
        break
    else:
        print("Invalid choice.")
        continue

    print("\nLaunching Megatools…\n")
    child = pexpect.spawn(cmd, echo=True)
    child.interact()

if __name__ == "__main__":
    main()
