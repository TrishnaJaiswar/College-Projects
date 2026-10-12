"""
Image restoration web app: DeOldify (colorize) + Real-ESRGAN (upscale) + GFPGAN (faces).

Start it with run.bat. The script switches to its own folder, so the relative
model paths (models/...) work no matter where it is launched from.
Settings you may want to tune are in the CONFIG block below.
"""
import logging
import os
import shutil
import threading
import time
import uuid
import warnings
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# ------------------------------- CONFIG -------------------------------
OUTPUT_SCALE = 4            # final size of "restore" results, relative to the input
MAX_INPUT_SIDE = 1600       # larger inputs are shrunk to this (longest side) before restoring; 0 = never shrink
TILE_SIZE = 400             # Real-ESRGAN works in tiles of this size so 4 GB of VRAM is enough; 0 = no tiling
RENDER_FACTORS = (45, 35, 25)  # DeOldify quality; later values are fallbacks if the GPU runs out of memory
JPEG_QUALITY = 95
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
VALID_PROCESS_TYPES = ("colorize", "restore", "colorize+restore")

MODELS_DIR = os.path.join(BASE_DIR, "models")
ESRGAN_WEIGHTS = os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth")
GFPGAN_WEIGHTS = os.path.join(MODELS_DIR, "GFPGANv1.4.pth")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "static", "results")
# ----------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("restoration")
warnings.filterwarnings("ignore", message="Your training set is empty")
warnings.filterwarnings("ignore", message="Your validation set is empty")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# One worker: there is a single GPU, so parallel jobs only compete for its memory.
executor = ThreadPoolExecutor(max_workers=1)


# ----------------------------------------------------------------------
# Model loading. Nothing heavy is imported or loaded until it is needed, and a
# background thread preloads everything right after the server starts, so the
# link appears immediately and the models are usually ready by the first upload.
# ----------------------------------------------------------------------
_load_lock = threading.RLock()
_models = {}
_runtime = {}


def _runtime_info():
    """Import torch once and record whether CUDA is usable.

    This must happen before DeOldify is imported: DeOldify's device module can
    hide the GPU from PyTorch if it is imported first.
    """
    with _load_lock:
        if not _runtime:
            import torch

            has_cuda = torch.cuda.is_available()
            _runtime["torch"] = torch
            _runtime["cuda"] = has_cuda
            _runtime["device"] = torch.device("cuda" if has_cuda else "cpu")
            gpu = torch.cuda.get_device_name(0) if has_cuda else "none"
            log.info("PyTorch %s | device: %s | GPU: %s", torch.__version__, _runtime["device"], gpu)
        return _runtime


def _free_gpu():
    if _runtime.get("cuda"):
        _runtime["torch"].cuda.empty_cache()


def _is_oom(exc):
    return isinstance(exc, RuntimeError) and "out of memory" in str(exc).lower()


def get_colorizer():
    with _load_lock:
        if "colorizer" not in _models:
            rt = _runtime_info()
            t0 = time.perf_counter()
            try:
                from deoldify import device as deoldify_device
                from deoldify.device_id import DeviceId

                deoldify_device.set(device=DeviceId.GPU0 if rt["cuda"] else DeviceId.CPU)
            except Exception as exc:
                log.warning("Could not set the DeOldify device explicitly: %s", exc)
            from deoldify.visualize import get_image_colorizer

            _models["colorizer"] = get_image_colorizer(artistic=False)
            log.info("DeOldify ready (%.1fs)", time.perf_counter() - t0)
        return _models["colorizer"]


def get_upscaler():
    with _load_lock:
        if "upscaler" not in _models:
            rt = _runtime_info()
            if not os.path.exists(ESRGAN_WEIGHTS):
                raise FileNotFoundError(f"Weight file not found: {ESRGAN_WEIGHTS}")
            t0 = time.perf_counter()
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            _models["upscaler"] = RealESRGANer(
                scale=4,
                model_path=ESRGAN_WEIGHTS,
                model=net,
                tile=TILE_SIZE,
                tile_pad=10,
                pre_pad=0,
                half=rt["cuda"],  # fp16 on the GPU: faster and about half the memory
                device=rt["device"],
            )
            log.info("Real-ESRGAN ready (%.1fs)", time.perf_counter() - t0)
        return _models["upscaler"]


def get_face_restorer():
    with _load_lock:
        if "face" not in _models:
            rt = _runtime_info()
            if not os.path.exists(GFPGAN_WEIGHTS):
                raise FileNotFoundError(f"Weight file not found: {GFPGAN_WEIGHTS}")
            upscaler = get_upscaler()
            t0 = time.perf_counter()
            from gfpgan import GFPGANer

            # Real-ESRGAN upsamples the background inside GFPGAN, so faces are
            # detected on the original image instead of an already 4x-enlarged copy.
            _models["face"] = GFPGANer(
                model_path=GFPGAN_WEIGHTS,
                upscale=OUTPUT_SCALE,
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=upscaler,
                device=rt["device"],
            )
            log.info("GFPGAN ready (%.1fs)", time.perf_counter() - t0)
        return _models["face"]


def _warm_up():
    start = time.perf_counter()
    for loader in (get_colorizer, get_face_restorer):
        try:
            loader()
        except Exception:
            log.exception("Preloading %s failed; it will be retried on first use", loader.__name__)
    log.info("Model preload finished (%.1fs)", time.perf_counter() - start)


# ----------------------------------------------------------------------
# Image helpers
# ----------------------------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_grayscale(image_path, threshold=10):
    try:
        with Image.open(image_path) as img:
            small = np.array(img.resize((100, 100)).convert("RGB")).astype(np.int32)
        diff = np.abs(small[:, :, 0] - small[:, :, 1]) + np.abs(small[:, :, 1] - small[:, :, 2])
        return float(np.mean(diff)) < threshold
    except Exception as exc:
        log.error("Error in is_grayscale: %s", exc)
        return False


def _limit_size(img_bgr):
    longest = max(img_bgr.shape[:2])
    if MAX_INPUT_SIDE and longest > MAX_INPUT_SIDE:
        scale = MAX_INPUT_SIDE / longest
        h, w = img_bgr.shape[:2]
        log.info("Input %dx%d is larger than %d px, shrinking before restoring", w, h, MAX_INPUT_SIDE)
        img_bgr = cv2.resize(img_bgr, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    return img_bgr


def _pil_to_bgr(pil_img):
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _write_jpg(path, img_bgr):
    if not cv2.imwrite(path, img_bgr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]):
        raise IOError(f"Could not write {path}")


def colorize_pil(image_path):
    """Colorize with DeOldify, retrying at lower quality if the GPU runs out of memory."""
    colorizer = get_colorizer()
    for i, factor in enumerate(RENDER_FACTORS):
        try:
            return colorizer.get_transformed_image(image_path, render_factor=factor, watermarked=False)
        except RuntimeError as exc:
            if not _is_oom(exc) or i == len(RENDER_FACTORS) - 1:
                raise
            log.warning("GPU out of memory at render_factor=%d, retrying at %d", factor, RENDER_FACTORS[i + 1])
            _free_gpu()


def restore_array(img_bgr):
    """Real-ESRGAN upscaling plus GFPGAN face restoration in a single pass (BGR in, BGR out)."""
    img_bgr = _limit_size(img_bgr)
    _, _, restored = get_face_restorer().enhance(
        img_bgr, has_aligned=False, only_center_face=False, paste_back=True
    )
    return restored


def _read_bgr(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"Unable to read image {path}")
    return img


# ----------------------------------------------------------------------
# Jobs
# ----------------------------------------------------------------------
def _failed_copy(file_path, name):
    out = os.path.join(RESULT_FOLDER, name + "_failed" + os.path.splitext(file_path)[1])
    shutil.copy(file_path, out)
    return out


def process_image(file_path, process_type):
    """Run one job. Always returns (result_path, message); on failure the result is a copy of the input."""
    name = os.path.splitext(os.path.basename(file_path))[0]
    t0 = time.perf_counter()
    try:
        if process_type == "colorize":
            if not is_grayscale(file_path):
                out = os.path.join(RESULT_FOLDER, name + "_already_colored" + os.path.splitext(file_path)[1])
                shutil.copy(file_path, out)
                return out, "Already colored"
            out = os.path.join(RESULT_FOLDER, name + "_colorized.jpg")
            colorize_pil(file_path).save(out, quality=JPEG_QUALITY)
            message = "Colorized"

        elif process_type == "restore":
            out = os.path.join(RESULT_FOLDER, name + "_restored.jpg")
            _write_jpg(out, restore_array(_read_bgr(file_path)))
            message = "Restored"

        else:  # colorize+restore
            if is_grayscale(file_path):
                log.info("Grayscale image: colorizing before restoring (%s)", name)
                img = _pil_to_bgr(colorize_pil(file_path))  # stays in memory, no JPEG round trip
            else:
                log.info("Already in color: skipping colorization (%s)", name)
                img = _read_bgr(file_path)
            out = os.path.join(RESULT_FOLDER, name + "_colorized_restored.jpg")
            _write_jpg(out, restore_array(img))
            message = "Colorized & Restored"

        log.info("%s finished in %.1fs: %s", process_type, time.perf_counter() - t0, out)
        return out, message

    except Exception as exc:
        log.exception("Processing failed for %s", file_path)
        label = "GPU out of memory (try a smaller image)" if _is_oom(exc) else "Processing failed"
        return _failed_copy(file_path, name), label
    finally:
        _free_gpu()


# ----------------------------------------------------------------------
# Web app
# ----------------------------------------------------------------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def _unique_upload_name(original):
    stem, ext = os.path.splitext(original)
    return f"{uuid.uuid4().hex[:8]}_{secure_filename(stem) or 'image'}{ext.lower()}"


@app.route("/download/<path:filename>")
def download_image(filename):
    return send_from_directory(RESULT_FOLDER, filename, as_attachment=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    try:
        process_type = request.form.get("process_type", "").lower()
        if process_type not in VALID_PROCESS_TYPES:
            return jsonify({"error": "Invalid process type. Use 'colorize', 'restore', or 'colorize+restore'."}), 400

        futures = []
        for file in request.files.getlist("files"):
            if not file or file.filename == "" or not allowed_file(file.filename):
                continue
            filepath = os.path.join(UPLOAD_FOLDER, _unique_upload_name(file.filename))
            file.save(filepath)
            futures.append(executor.submit(process_image, filepath, process_type))

        results = []
        for future in futures:
            processed_path, message = future.result()
            if processed_path:
                results.append({"path": "results/" + os.path.basename(processed_path), "message": message})
        return jsonify({"result_images": results})
    except Exception as exc:
        log.exception("Error processing images")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    threading.Thread(target=_warm_up, name="model-preload", daemon=True).start()
    # use_reloader=False: the reloader ran this whole script twice, loading every model twice.
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
