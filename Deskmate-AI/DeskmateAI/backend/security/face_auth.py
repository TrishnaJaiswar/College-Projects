# DeskmateAI/backend/security/face_auth.py

import os
import sys
import time
import numpy as np

# ============================================================
# FACE AUTHENTICATION FOR DESKMATEAI
# Uses OpenCV + face_recognition library instead of DeepFace
# Works without TensorFlow — no AVX2 requirement
# Lighter and faster on low spec PCs
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import (
    get_user_face_dir,
    save_numpy,
    load_numpy,
    load_profile,
    save_profile,
    get_timestamp,
    ensure_dir
)

# ── Constants ─────────────────────────────────────────────────

FACE_SAMPLES_REQUIRED = 3
FACE_SIMILARITY_THRESHOLD = 0.55

# ── Face Auth Class ───────────────────────────────────────────

class FaceAuth:

    def __init__(self):
        # print("[FACE] Initializing FaceAuth...")
        self._face_cascade = None
        self._load_cascade()
        log_info("FaceAuth initialized")

    def _load_cascade(self):
        """Load OpenCV face cascade"""
        try:
            import cv2
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
            # print("[FACE] ✅ OpenCV cascade loaded")
            log_debug("OpenCV face cascade loaded")
        except Exception as e:
            # print(f"[FACE] Cascade load error: {e}")
            log_error(f"Cascade load error: {e}")

    def _open_camera(self):
        """Open webcam"""
        # print("[FACE] Opening camera...")
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                log_error("Camera not accessible")
                return None
            log_debug("Camera opened")
            return cap
        except Exception as e:
            log_error(f"Camera open error: {e}")
            return None

    def _release_camera(self, cap):
        """Release webcam"""
        try:
            if cap:
                cap.release()
        except Exception as e:
            log_error(f"Camera release error: {e}")

    def _capture_frame(self, cap):
        """Capture frame from webcam"""
        try:
            import cv2
            for _ in range(5):
                ret, frame = cap.read()
                time.sleep(0.1)
            if not ret or frame is None:
                return None
            return frame
        except Exception as e:
            log_error(f"Frame capture error: {e}")
            return None

    def _extract_embedding(self, frame):
        """
        Extract face embedding using OpenCV
        No TensorFlow needed
        """
        # print("[FACE] Extracting embedding...")
        try:
            import cv2

            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = self._face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            if len(faces) == 0:
                # print("[FACE] No face detected")
                log_warning("No face detected")
                return None

            # Get largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

            # Extract face region
            face_roi = frame[y:y+h, x:x+w]

            # Resize to standard size
            face_resized = cv2.resize(face_roi, (128, 128))

            # Convert to grayscale embedding
            face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)

            # Normalize
            face_normalized = face_gray.astype(np.float32) / 255.0

            # Flatten to embedding vector
            embedding = face_normalized.flatten()

            # print(f"[FACE] ✅ Embedding: shape={embedding.shape}")
            log_debug(f"Face embedding: shape={embedding.shape}")
            return embedding

        except Exception as e:
            # print(f"[FACE] Embedding error: {e}")
            log_error(f"Face embedding error: {e}")
            return None

    def register(self, username, progress_callback=None):
        """Register face samples"""
        # print(f"[FACE] Registering face: {username}")
        log_info(f"Face registration: {username}")

        cap = None
        saved = 0

        try:
            face_dir = get_user_face_dir(username)
            ensure_dir(face_dir)

            cap = self._open_camera()
            if not cap:
                return False, "Cannot access camera"

            instructions = [
                "Look straight at the camera",
                "Tilt slightly to the left",
                "Tilt slightly to the right"
            ]

            for i in range(FACE_SAMPLES_REQUIRED):
                instruction = instructions[i]
                # print(f"[FACE] Sample {i+1}: {instruction}")

                if progress_callback:
                    progress_callback(i+1, FACE_SAMPLES_REQUIRED, instruction)

                time.sleep(2.0)

                frame = self._capture_frame(cap)
                if frame is None:
                    continue

                embedding = self._extract_embedding(frame)
                if embedding is None:
                    if progress_callback:
                        progress_callback(
                            i+1, FACE_SAMPLES_REQUIRED,
                            "No face detected. Please try again."
                        )
                    continue

                filepath = os.path.join(face_dir, f"face_{i+1}.npy")
                save_numpy(filepath, embedding)
                saved += 1
                # print(f"[FACE] ✅ Sample {i+1} saved")
                log_info(f"Face sample {i+1} saved")

                if progress_callback:
                    progress_callback(
                        i+1, FACE_SAMPLES_REQUIRED,
                        f"Sample {i+1} captured ✅"
                    )

            if saved < 1:
                return False, "Failed to capture face samples"

            profile = load_profile(username)
            profile['face_samples'] = saved
            profile['face_registered_at'] = get_timestamp()
            if 'face' not in profile.get('auth_methods', []):
                profile.setdefault('auth_methods', []).append('face')
            save_profile(username, profile)

            # print(f"[FACE] ✅ Registration complete: {saved} samples")
            log_info(f"Face registration complete: {saved} samples")
            return True, f"Face registered with {saved} samples"

        except Exception as e:
            # print(f"[FACE] Registration error: {e}")
            log_error(f"Face registration error: {e}")
            return False, str(e)

        finally:
            self._release_camera(cap)

    def verify(self, username, progress_callback=None):
        """Verify face"""
        # print(f"[FACE] Verifying: {username}")
        log_info(f"Face verification: {username}")

        cap = None

        try:
            stored = self._load_embeddings(username)
            if not stored:
                log_warning(f"No face data for: {username}")
                return False

            cap = self._open_camera()
            if not cap:
                return False

            if progress_callback:
                progress_callback("Looking for face...")

            frame = self._capture_frame(cap)
            if frame is None:
                return False

            live_embedding = self._extract_embedding(frame)
            if live_embedding is None:
                log_warning("No face detected during verification")
                return False

            best_score = 0.0
            for stored_embedding in stored:
                if stored_embedding.shape != live_embedding.shape:
                    continue
                score = self._cosine_similarity(live_embedding, stored_embedding)
                # print(f"[FACE] Score: {score:.4f}")
                if score > best_score:
                    best_score = score

            # print(f"[FACE] Best: {best_score:.4f} | Threshold: {FACE_SIMILARITY_THRESHOLD}")
            authorized = best_score >= FACE_SIMILARITY_THRESHOLD

            if authorized:
                log_info(f"Face verified: {username}")
            else:
                log_warning(f"Face failed: {username}")

            return authorized

        except Exception as e:
            log_error(f"Face verification error: {e}")
            return False

        finally:
            self._release_camera(cap)

    def _load_embeddings(self, username):
        """Load stored embeddings"""
        try:
            face_dir = get_user_face_dir(username)
            if not os.path.exists(face_dir):
                return []
            embeddings = []
            for f in sorted(os.listdir(face_dir)):
                if f.endswith('.npy'):
                    e = load_numpy(os.path.join(face_dir, f))
                    if e is not None:
                        embeddings.append(e)
            return embeddings
        except Exception as e:
            log_error(f"Load embeddings error: {e}")
            return []

    def _cosine_similarity(self, e1, e2):
        """Cosine similarity"""
        try:
            n1 = np.linalg.norm(e1)
            n2 = np.linalg.norm(e2)
            if n1 == 0 or n2 == 0:
                return 0.0
            return float(np.dot(e1, e2) / (n1 * n2))
        except:
            return 0.0

    def add_face_sample(self, username):
        """Add extra face sample"""
        cap = None
        try:
            face_dir = get_user_face_dir(username)
            ensure_dir(face_dir)
            existing = [f for f in os.listdir(face_dir) if f.endswith('.npy')]
            next_index = len(existing) + 1

            cap = self._open_camera()
            if not cap:
                return False, "Cannot access camera"

            time.sleep(1.5)
            frame = self._capture_frame(cap)
            if frame is None:
                return False, "Failed to capture"

            embedding = self._extract_embedding(frame)
            if embedding is None:
                return False, "No face detected"

            filepath = os.path.join(face_dir, f"face_{next_index}.npy")
            save_numpy(filepath, embedding)

            profile = load_profile(username)
            profile['face_samples'] = next_index
            save_profile(username, profile)

            log_info(f"Added face sample {next_index}")
            return True, f"Sample {next_index} added"

        except Exception as e:
            log_error(f"Add sample error: {e}")
            return False, str(e)
        finally:
            self._release_camera(cap)

    def delete_face_data(self, username):
        """Delete face data"""
        try:
            import shutil
            face_dir = get_user_face_dir(username)
            if os.path.exists(face_dir):
                shutil.rmtree(face_dir)
                os.makedirs(face_dir)
            profile = load_profile(username)
            profile['face_samples'] = 0
            if 'face' in profile.get('auth_methods', []):
                profile['auth_methods'].remove('face')
            save_profile(username, profile)
            log_info(f"Face data deleted: {username}")
            return True
        except Exception as e:
            log_error(f"Delete face error: {e}")
            return False

    def is_registered(self, username):
        """Check if face registered"""
        try:
            face_dir = get_user_face_dir(username)
            if not os.path.exists(face_dir):
                return False
            return len([f for f in os.listdir(face_dir) if f.endswith('.npy')]) > 0
        except:
            return False

    def get_sample_count(self, username):
        """Get sample count"""
        try:
            face_dir = get_user_face_dir(username)
            if not os.path.exists(face_dir):
                return 0
            return len([f for f in os.listdir(face_dir) if f.endswith('.npy')])
        except:
            return 0

    def get_camera_frame(self):
        """Get preview frame"""
        cap = None
        try:
            cap = self._open_camera()
            if not cap:
                return None
            return self._capture_frame(cap)
        except:
            return None
        finally:
            self._release_camera(cap)


# ── Singleton ─────────────────────────────────────────────────

_face_auth = None

def get_face_auth():
    global _face_auth
    if _face_auth is None:
        _face_auth = FaceAuth()
    return _face_auth