# College Projects

A collection of academic and technical projects exploring **Artificial Intelligence, Deep Learning, Natural Language Processing, and Desktop Automation**.

This repository brings together two independent projects: an AI-powered image restoration application and a multilingual, voice-controlled desktop assistant. Each project has its own source code, dependencies, and setup instructions.

## 📚 Projects Overview

| Project | Description | Technologies |
|---|---|---|
| [Image Restoration](#1-image-restoration) | Restores, colorizes, and upscales old photographs using deep learning. | Python, Flask, PyTorch, DeOldify, Real-ESRGAN, GFPGAN |
| [DeskmateAI](#2-deskmateai) | A voice-controlled Windows assistant with multilingual commands and user authentication. | Python, Whisper, SBERT, Ollama, EasyOCR, PyAutoGUI |

---

## 1. Image Restoration

**An AI-powered web application for restoring and colorizing old photographs.**

Image Restoration is a Flask-based application that allows users to upload photographs through a browser and enhance them using deep-learning models.

### Features

- **Image Colorization:** Adds color to black-and-white photographs using DeOldify.
- **Image Upscaling:** Increases image resolution by up to 4× using Real-ESRGAN.
- **Face Restoration:** Enhances facial details using GFPGAN.
- **Combined Processing:** Colorizes and restores images in a single workflow.
- **Multiple Image Uploads:** Supports uploading multiple images through the web interface.
- **Memory-Aware Processing:** Uses image resizing and tiled processing to help manage GPU memory.

### Technology Stack

- Python and Flask
- PyTorch
- DeOldify
- Real-ESRGAN
- GFPGAN
- HTML and CSS

### How It Works

1. Upload one or more photographs through the web interface.
2. Choose **Colorize**, **Restore**, or **Colorize + Restore**.
3. The application processes the images using the selected deep-learning models.
4. View the processed results in the browser.

### Installation and Usage

**Requirements:** Windows, Git, Python 3.10, and compatible PyTorch/CUDA dependencies. A compatible NVIDIA GPU is recommended for acceleration.

```powershell
cd Image-Restoration/image-restoration-new
run.bat
```

On the first run, the setup script creates a virtual environment, installs dependencies, downloads the required model repositories and obtains model weights. This may require several gigabytes of storage.

Once the application starts, open:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

For manual installation, dependency versions, model setup, and hardware compatibility, refer to the project's original documentation.

### Important Notes

- The model weights and supporting model repositories are downloaded separately and are not included in this repository.
- The original implementation was tested with Windows, Python 3.10.0, PyTorch 1.11.0, CUDA 11.3, and an NVIDIA GeForce RTX 3050 with 4 GB VRAM.
- Newer Python, PyTorch, CUDA, or GPU configurations may require compatibility changes.

---

## 2. DeskmateAI

**A multilingual, voice-controlled desktop assistant for Windows.**

DeskmateAI enables users to control their computers using spoken commands in English, Hindi, or Marathi. It combines speech recognition, translation, natural-language intent classification, desktop automation, and user authentication to execute commands through voice.

Speech recognition, translation, and intent classification run locally after the required models are available, enabling offline operation for these functions.

### Features

- **Wake Word Detection:** Activates when the configured wake word is detected, with "Hey Deskmate" as the default.
- **Multilingual Voice Commands:** Supports English, Hindi, and Marathi commands.
- **Speech Recognition:** Uses a Whisper small model through faster-whisper.
- **Language Translation:** Translates Hindi and Marathi commands into English using Helsinki-NLP Opus-MT.
- **Intent Classification:** Uses Sentence-BERT for fast matching, with a local Phi-3.5 LLM through Ollama as a fallback.
- **Self-Learning Intent Memory:** Saves commands classified through the LLM for potential future matching through SBERT.
- **Desktop Automation:** Opens applications, switches windows, controls media, adjusts volume, types text, and performs other supported actions.
- **Screen Interaction:** Uses EasyOCR to locate and click described elements in the active window.
- **Dictation Mode:** Converts speech into longer blocks of text.
- **Undo and Redo:** Supports reversing and reapplying supported executed actions.
- **Voice Responses:** Provides spoken feedback through offline text-to-speech.
- **Multi-User Authentication:** Supports password, voice-passphrase, and face-recognition login, along with speaker verification.
- **System Tray Interface:** Includes login, registration, dashboard, and settings interfaces.

### Technology Stack

- **Language:** Python
- **Speech Recognition:** Whisper, faster-whisper
- **Natural Language Processing:** Sentence-BERT, all-MiniLM-L6-v2
- **Local LLM:** Phi-3.5 through Ollama
- **Translation:** Helsinki-NLP Opus-MT
- **OCR:** EasyOCR
- **Desktop Automation:** PyAutoGUI, pywinauto, ctypes
- **Text-to-Speech:** pyttsx3
- **Security:** Password hashing with bcrypt, voice and face authentication
- **Interface:** Python-based desktop UI and system tray

### How It Works

The assistant follows a multi-stage processing pipeline:

```text
Wake Word Detection
        ↓
Speech Recognition
        ↓
Hindi/Marathi Translation to English
        ↓
Intent Classification
(SBERT → Local LLM Fallback)
        ↓
Authentication and Speaker Verification
        ↓
Command Execution
        ↓
Spoken Response
```

1. **Wake word detection:** Listens for the configured activation phrase.
2. **Speech recognition:** Converts spoken commands into text using Whisper.
3. **Translation:** Translates Hindi or Marathi text into English when required.
4. **Intent classification:** Matches commands against stored intent examples using SBERT. If the similarity score is below the configured threshold of 0.50, the command is sent to the local LLM fallback.
5. **Authentication:** Verifies the registered speaker before executing protected commands.
6. **Command execution:** Routes the recognized intent to the appropriate automation handler.
7. **Response:** Announces the result through text-to-speech and updates the system tray status.

### Supported Command Categories

The project currently defines 39 intents across several categories.

| Category | Example Actions |
|---|---|
| Applications | Open applications, close applications, switch windows |
| Web Browsing | Search, open or close tabs, zoom in or out |
| Sound and Display | Adjust volume, mute or unmute, adjust brightness |
| Media | Play, pause, next track, previous track |
| System | Shutdown, restart, sleep, lock, take a screenshot |
| Window Management | Minimize, maximize, close, hide windows |
| Text Editing | Type text, copy, paste, select all, save, undo, redo |
| Navigation | Scroll and click screen elements |
| Assistant Controls | Open the dashboard and settings |

The complete intent list and example phrases are maintained in `NLP/nlp/intents/intent_examples.json`.

### Installation and Usage

**Requirements:**

- Windows 10 or Windows 11
- Python 3.10 or newer
- A microphone; a webcam for face authentication
- Ollama installed and available on the system PATH
- The Phi-3.5 model downloaded through Ollama
- Sufficient RAM; a compatible NVIDIA GPU is recommended for the current ASR configuration

Navigate to the project directory and create a virtual environment:

```powershell
cd Deskmate-AI/DeskmateAI
python -m venv venv
```

Run the Windows dependency installer:

```powershell
install.bat
```

Download the LLM used for fallback intent classification:

```powershell
ollama pull phi3.5
```

Ensure the required Whisper model files are available in `NLP/models/whisper/`. The SBERT model may be downloaded automatically if its model directory is empty; translation models are downloaded on first use.

Start the application:

```powershell
python main.py
```

Register a user through the login interface, then activate the assistant using the configured wake word and speak a supported command.

### Running Tests

DeskmateAI includes a test suite for checking module imports, class initialization, and core logic.

```powershell
python test_suite.py
```

The tests are designed to run without loading the models, accessing a microphone, or requiring a GPU.

### Privacy and Security

- Speech recognition, translation, and intent classification run locally after model setup.
- Voice and face representations are stored as embeddings rather than raw audio recordings or images.
- Passwords are hashed using bcrypt.
- Screenshots used for screen-element detection are held in memory rather than saved to disk.
- Session data is held in memory, so users must log in again after restarting the application.
- User profiles and logs are created at runtime and should remain excluded from version control.

### Known Limitations

- Windows only.
- Hindi and Marathi are the supported non-English languages.
- Screen-element clicking depends on OCR accuracy and the active window.
- Model loading can make the first startup slow.
- Whisper and Ollama can require substantial memory and compatible hardware.

---

## 🗂️ Repository Structure

```text
College-Projects/
│
├── README.md
│
├── Image-Restoration/
│   └── image-restoration-new/
│       ├── app.py
│       ├── download_models.py
│       ├── requirements.txt
│       ├── run.bat
│       ├── setup.bat
│       ├── templates/
│       └── static/
│
└── Deskmate-AI/
    └── DeskmateAI/
        ├── main.py
        ├── install.bat
        ├── requirements.txt
        ├── test_suite.py
        ├── NLP/
        ├── backend/
        └── ui/
```

*Note: Model weights, virtual environments, generated files, and runtime user data are not included in the repository.*

## 🎯 Academic Purpose

These projects provide practical exposure to AI and software engineering concepts, including deep-learning-based image processing, speech recognition, multilingual NLP, local LLM integration, desktop automation, and authentication.

Each project can be explored and executed independently using its own dependencies and setup instructions.

## 🙌 Credits and Acknowledgements

### Image Restoration

This project uses open-source tools and models from:

- [DeOldify](https://github.com/jantic/DeOldify) — image colorization
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) — image restoration and upscaling
- [GFPGAN](https://github.com/TencentARC/GFPGAN) — face restoration

### DeskmateAI

Original project repository: [Shubh-Pi/DeskmateAI](https://github.com/Shubh-Pi/DeskmateAI)

The project also uses third-party libraries and models, including Whisper, faster-whisper, Sentence-BERT, Helsinki-NLP Opus-MT, Ollama, EasyOCR, and other Python packages.

Please refer to the original repositories, package licenses, and model terms for their respective usage and distribution conditions. Credit for original implementations belongs to their respective authors and contributors.

## 📄 License

Refer to each project's original repository and included license information for applicable usage and distribution terms.
