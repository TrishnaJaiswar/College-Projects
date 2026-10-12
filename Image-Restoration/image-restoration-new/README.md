# Image Restoration

A small Flask web app for restoring old photos. You upload one or more images in the browser and pick one of three options:

- **colorize** adds color to a black and white photo (DeOldify)
- **restore** upscales the image 4x and repairs faces (Real-ESRGAN and GFPGAN)
- **colorize+restore** does both in one go

The app itself is only `app.py`, a page template and a stylesheet. The models come from three other projects, which are not included in this repository:

- DeOldify: https://github.com/jantic/DeOldify
- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN
- GFPGAN: https://github.com/TencentARC/GFPGAN (installed through pip)

## What it was tested on

Windows, Python 3.10.0, PyTorch 1.11.0 with CUDA 11.3, and an NVIDIA GeForce RTX 3050 with 4 GB of memory.

Two limits come from that setup. PyTorch 1.11 has no builds for newer Python versions, so Python 3.10 is required. And the CUDA 11.3 build of PyTorch supports NVIDIA GPUs up to the RTX 30 series. Newer cards will probably need a newer PyTorch, which I have not tried, and the older libraries used here may not work with it.

## Quick start

You need Windows, Git, and Python 3.10 (installed with the `py` launcher, which is the default on python.org).

```
git clone <this repository>
cd <the folder>
run.bat
```

The first time, `run.bat` notices that things are missing and runs `setup.bat`, which creates a virtual environment, installs the packages, clones DeOldify and Real-ESRGAN at the versions the app was built with, and downloads the model weights. This is several GB of downloads and takes a while. After that, `run.bat` just starts the app.

Then open http://127.0.0.1:5000 in a browser.

## Manual setup

If `setup.bat` fails, or you prefer to do it step by step:

```
py -3.10 -m venv venv
venv\Scripts\activate
python -m pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
python -m pip install -r requirements.txt

git clone https://github.com/jantic/DeOldify.git
git -C DeOldify checkout 5f86c28
git clone https://github.com/xinntao/Real-ESRGAN.git
git -C Real-ESRGAN checkout a4abfb2
python -m pip install --no-deps -e Real-ESRGAN

python download_models.py
```

Real-ESRGAN has to be installed once because it creates its `version.py` file during installation, and that file is not part of its repository.

`download_models.py` puts three files in a `models` folder: `RealESRGAN_x4plus.pth`, `GFPGANv1.4.pth` and `ColorizeStable_gen.pth`. They come from the release pages of those projects and are large (the DeOldify one is over 800 MB), which is why they are not in this repository. If a link stops working, the script says which file to download by hand.

On the first run a few more files download automatically: a ResNet-101 checkpoint from PyTorch (about 170 MB) and the face detection models, which go into a `gfpgan\weights` folder.

## Running

```
run.bat
```

or, with the environment activated:

```
set PYTHONPATH=DeOldify;Real-ESRGAN
python app.py
```

The models load in the background after start-up, so the first upload can take a little longer than later ones. The console prints which device is in use (cuda or cpu) when PyTorch loads.

Uploaded images go to `static/uploads` and results to `static/results`. Neither folder is tracked by git.

## Settings

A few values at the top of `app.py` can be changed:

- `OUTPUT_SCALE`: how much larger the restored image is (4 by default)
- `MAX_INPUT_SIDE`: images with a longer side than this are shrunk before restoring (1600 by default), which keeps memory use reasonable
- `TILE_SIZE`: Real-ESRGAN processes the image in tiles of this size so it fits on a small GPU
- `RENDER_FACTORS`: DeOldify quality, with lower fallback values if the GPU runs out of memory

## Folder layout

```
app.py               the web app
run.bat              starts it (runs setup.bat first if needed)
setup.bat            one-time setup
download_models.py   downloads the model weights
requirements.txt     Python packages
templates/           index.html
static/css/          style.css
models/              weights, downloaded by the script (not in the repo)
DeOldify/            cloned by setup (not in the repo)
Real-ESRGAN/         cloned by setup (not in the repo)
```

## Credits

All of the image processing is done by DeOldify, Real-ESRGAN and GFPGAN. The model weights are distributed by those projects under their own terms.
