@echo off
echo Installing DeskmateAI dependencies...

:: Activate venv
call venv\Scripts\activate

:: Pin numpy first
pip install numpy==1.26.4

:: Install torch CPU
pip install torch==2.2.2+cpu torchvision==0.17.2+cpu --index-url https://download.pytorch.org/whl/cpu

:: Install problematic packages without deps
pip install opencv-python==4.8.1.78 --no-deps
pip install deepface==0.0.79 --no-deps
pip install easyocr==1.7.1 --no-deps

:: Install rest
pip install ctranslate2==4.7.1
pip install faster-whisper==1.2.1
pip install transformers==4.40.0
pip install sentencepiece tokenizers huggingface_hub
pip install sentence-transformers
pip install sounddevice soundfile scipy
pip install scikit-learn PyQt6
pip install pyautogui pyperclip pywinauto
pip install resemblyzer
pip install noisereduce bcrypt
pip install screen-brightness-control
pip install pywin32 pyttsx3
pip install pycaw comtypes psutil
pip install requests ollama librosa
pip install Pillow tqdm retina-face fire gdown

:: Force numpy back to 1.26.4
pip install numpy==1.26.4 --force-reinstall --no-deps

echo.
echo Verifying installation...
python -c "import numpy; import torch; import ctranslate2; import faster_whisper; print('numpy:', numpy.__version__, '| torch:', torch.__version__, '| All OK!')"

echo.
echo Done! Run: python main.py
pause