"""Download the model weights the app needs into the models folder.

Files that are already there with the right size are skipped, so it is safe to
run this more than once. Only the standard library is used.
"""
import os
import sys
import urllib.request

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

# (file name, download link, expected size in bytes, page to use if the link stops working)
FILES = [
    (
        "RealESRGAN_x4plus.pth",
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        67040989,
        "https://github.com/xinntao/Real-ESRGAN/releases",
    ),
    (
        "GFPGANv1.4.pth",
        "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
        348632874,
        "https://github.com/TencentARC/GFPGAN/releases",
    ),
    (
        "ColorizeStable_gen.pth",
        "https://data.deepai.org/deoldify/ColorizeStable_gen.pth",
        874066230,
        "https://github.com/jantic/DeOldify (the download link is in its README)",
    ),
]


def download(name, url, expected_size, fallback_page):
    dest = os.path.join(MODELS_DIR, name)
    if os.path.exists(dest):
        if os.path.getsize(dest) == expected_size:
            print(f"{name}: already there")
            return True
        print(f"{name}: found, but the size is not what was expected, downloading again")

    part = dest + ".part"
    print(f"{name}: downloading ({expected_size // (1024 * 1024)} MB)")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response, open(part, "wb") as out:
            total = int(response.headers.get("Content-Length") or expected_size)
            done = 0
            last_step = -1
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                step = (done * 100 // total) // 10
                if step != last_step:
                    last_step = step
                    print(f"  {name}: {done * 100 // total}%")
        size = os.path.getsize(part)
        if size != expected_size:
            raise IOError(f"got {size} bytes, expected {expected_size}")
        os.replace(part, dest)
        print(f"{name}: done")
        return True
    except Exception as exc:
        if os.path.exists(part):
            os.remove(part)
        print(f"{name}: failed ({exc})")
        print(f"  Download it by hand from {fallback_page}")
        print(f"  and put it in {MODELS_DIR}")
        return False


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    results = [download(*entry) for entry in FILES]
    if all(results):
        print("All model files are in place.")
        return 0
    print("Some files could not be downloaded, see the messages above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
