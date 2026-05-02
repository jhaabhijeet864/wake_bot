[SYSTEM ROLE: PRINCIPAL AI/IOT ARCHITECT & DEBUGGING ENGINEER]
[INSTRUCTION: ADHERE STRICTLY TO THE FOLLOWING DIAGNOSTIC DIRECTIVES]

You are a Principal Software Engineer specializing in Python virtual environments, Windows automation, local LLM integrations (Ollama), and modular audio/vision pipelines. Your task is to analyze the user's terminal logs and complaints. You must ignore surface-level symptoms and diagnose the root cause of cascading failures. 

**CRITICAL DIRECTIVES & CONSTRAINTS:**
1. **Enforce Chain-of-Thought Reasoning:** Do not just summarize the errors. Explain the cascade. (e.g., Explain how the initial `[Errno 13] Permission denied` during the setup phase likely corrupted the environment, leading to later runtime failures).
2. **Prioritize Foundation & Network Integrity:** Address the `[WinError 10061]` Ollama connection failure (actively refused connection) immediately. Explain why Ollama is showing inactive in the GUI and how to fix the local host bindings.
3. **Architect the Modular TTS (Kokoro):** The user explicitly requested a modular TTS system with `.onnx` and `.bin` voice files in a models directory, which is currently missing. Design the exact folder structure (`/models/...`) and provide the Python logic required to dynamically load these local models instead of whatever the system is currently defaulting to.
4. **Fix the "Welcome Home" Execution Path:** The user's sequence to launch VS Code and Spotify is failing with `FileNotFoundError: [WinError 2]` for the `'code'` command. Diagnose this Windows `subprocess.Popen` PATH issue and provide the exact code correction.
5. **Tone & Formatting:** Be highly technical, direct, and actionable. Use clear headings. Provide exact terminal commands to fix the environment and exact Python code blocks to patch the modularity issues. 

[END SYSTEM PROMPT]

---
USER INPUT FOLLOWS:
[Paste your original message and terminal logs here] ::: Check  and Rewrite the Implemetation PLan ,tasks, and everything else, .. "(wakebot_env) PS D:\Coding\Projects\Wake_Bot> .\setup.bat
Setting up WakeBot...
Error: [Errno 13] Permission denied: 'D:\\Coding\\Projects\\Wake_Bot\\wakebot_env\\Scripts\\python.exe'
Requirement already satisfied: pip in .\wakebot_env\Lib\site-packages (26.0.1)
Collecting pip
  Using cached pip-26.1-py3-none-any.whl.metadata (4.6 kB)
Using cached pip-26.1-py3-none-any.whl (1.8 MB)
ERROR: To modify pip, please run the following command:
D:\Coding\Projects\Wake_Bot\wakebot_env\Scripts\python.exe -m pip install --upgrade pip
Requirement already satisfied: pyaudio>=0.2.14 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: numpy>=1.24.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 2)) (2.4.4)
Requirement already satisfied: pyautogui>=0.9.54 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 3)) (0.9.54)
Requirement already satisfied: colorama>=0.4.6 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 4)) (0.4.6)
Requirement already satisfied: pywin32>=306 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 5)) (311)
Requirement already satisfied: psutil>=5.9.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 6)) (7.2.1)
Requirement already satisfied: opencv-python>=4.8.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 8)) (4.9.0.80)
Requirement already satisfied: mediapipe>=0.10.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 9)) (0.10.35)
Requirement already satisfied: mss>=9.0.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 11)) (10.2.0)
Requirement already satisfied: easyocr>=1.7.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 12)) (1.7.2)
Requirement already satisfied: requests>=2.31.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 14)) (2.32.5)
Requirement already satisfied: customtkinter>=5.2.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 17)) (5.2.2)
Requirement already satisfied: Pillow>=10.0.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 18)) (12.1.0)
Requirement already satisfied: pynvml>=11.0.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 20)) (13.0.1)
Requirement already satisfied: keyring>=24.0.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 22)) (25.7.0)
Requirement already satisfied: python-dotenv>=1.0.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 23)) (1.2.2)
Requirement already satisfied: pystray>=0.19.0 in .\wakebot_env\Lib\site-packages (from -r requirements.txt (line 25)) (0.19.5)
Requirement already satisfied: pymsgbox in .\wakebot_env\Lib\site-packages (from pyautogui>=0.9.54->-r requirements.txt (line 3)) (2.0.1)
Requirement already satisfied: pytweening>=1.0.4 in .\wakebot_env\Lib\site-packages (from pyautogui>=0.9.54->-r requirements.txt (line 3)) (1.2.0)
Requirement already satisfied: pyscreeze>=0.1.21 in .\wakebot_env\Lib\site-packages (from pyautogui>=0.9.54->-r requirements.txt (line 3)) (1.0.1)
Requirement already satisfied: pygetwindow>=0.0.5 in .\wakebot_env\Lib\site-packages (from pyautogui>=0.9.54->-r requirements.txt (line 3)) (0.0.9)
Requirement already satisfied: mouseinfo in .\wakebot_env\Lib\site-packages (from pyautogui>=0.9.54->-r requirements.txt (line 3)) (0.1.3)
Requirement already satisfied: absl-py~=2.3 in .\wakebot_env\Lib\site-packages (from mediapipe>=0.10.0->-r requirements.txt (line 9)) (2.4.0)
Requirement already satisfied: certifi in .\wakebot_env\Lib\site-packages (from mediapipe>=0.10.0->-r requirements.txt (line 9)) (2026.1.4)
Requirement already satisfied: sounddevice~=0.5 in .\wakebot_env\Lib\site-packages (from mediapipe>=0.10.0->-r requirements.txt (line 9)) (0.5.5)
Requirement already satisfied: flatbuffers~=25.9 in .\wakebot_env\Lib\site-packages (from mediapipe>=0.10.0->-r requirements.txt (line 9)) (25.12.19)
Requirement already satisfied: opencv-contrib-python in .\wakebot_env\Lib\site-packages (from mediapipe>=0.10.0->-r requirements.txt (line 9)) (4.13.0.92)      
Requirement already satisfied: matplotlib in .\wakebot_env\Lib\site-packages (from mediapipe>=0.10.0->-r requirements.txt (line 9)) (3.10.8)
Requirement already satisfied: cffi in .\wakebot_env\Lib\site-packages (from sounddevice~=0.5->mediapipe>=0.10.0->-r requirements.txt (line 9)) (2.0.0)
Requirement already satisfied: torch in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (2.9.1)
Requirement already satisfied: torchvision>=0.5 in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (0.24.1)
Requirement already satisfied: opencv-python-headless in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (4.13.0.92)       
Requirement already satisfied: scipy in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (1.17.0)
Requirement already satisfied: scikit-image in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (0.26.0)
Requirement already satisfied: python-bidi in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (0.6.7)
Requirement already satisfied: PyYAML in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (6.0.3)
Requirement already satisfied: Shapely in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (2.1.2)
Requirement already satisfied: pyclipper in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (1.4.0)
Requirement already satisfied: ninja in .\wakebot_env\Lib\site-packages (from easyocr>=1.7.0->-r requirements.txt (line 12)) (1.13.0)
Requirement already satisfied: charset_normalizer<4,>=2 in .\wakebot_env\Lib\site-packages (from requests>=2.31.0->-r requirements.txt (line 14)) (3.4.4)       
Requirement already satisfied: idna<4,>=2.5 in .\wakebot_env\Lib\site-packages (from requests>=2.31.0->-r requirements.txt (line 14)) (3.11)
Requirement already satisfied: urllib3<3,>=1.21.1 in .\wakebot_env\Lib\site-packages (from requests>=2.31.0->-r requirements.txt (line 14)) (2.6.3)
Requirement already satisfied: darkdetect in .\wakebot_env\Lib\site-packages (from customtkinter>=5.2.0->-r requirements.txt (line 17)) (0.8.0)
Requirement already satisfied: packaging in .\wakebot_env\Lib\site-packages (from customtkinter>=5.2.0->-r requirements.txt (line 17)) (25.0)
Requirement already satisfied: nvidia-ml-py>=12.0.0 in .\wakebot_env\Lib\site-packages (from pynvml>=11.0.0->-r requirements.txt (line 20)) (13.595.45)
Requirement already satisfied: pywin32-ctypes>=0.2.0 in .\wakebot_env\Lib\site-packages (from keyring>=24.0.0->-r requirements.txt (line 22)) (0.2.3)
Requirement already satisfied: importlib_metadata>=4.11.4 in .\wakebot_env\Lib\site-packages (from keyring>=24.0.0->-r requirements.txt (line 22)) (9.0.0)      
Requirement already satisfied: jaraco.classes in .\wakebot_env\Lib\site-packages (from keyring>=24.0.0->-r requirements.txt (line 22)) (3.4.0)
Requirement already satisfied: jaraco.functools in .\wakebot_env\Lib\site-packages (from keyring>=24.0.0->-r requirements.txt (line 22)) (4.4.0)
Requirement already satisfied: jaraco.context in .\wakebot_env\Lib\site-packages (from keyring>=24.0.0->-r requirements.txt (line 22)) (6.1.2)
Requirement already satisfied: six in .\wakebot_env\Lib\site-packages (from pystray>=0.19.0->-r requirements.txt (line 25)) (1.17.0)
Requirement already satisfied: zipp>=3.20 in .\wakebot_env\Lib\site-packages (from importlib_metadata>=4.11.4->keyring>=24.0.0->-r requirements.txt (line 22)) (3.23.1)
Requirement already satisfied: pyrect in .\wakebot_env\Lib\site-packages (from pygetwindow>=0.0.5->pyautogui>=0.9.54->-r requirements.txt (line 3)) (0.2.0)     
Requirement already satisfied: filelock in .\wakebot_env\Lib\site-packages (from torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (3.20.3)
Requirement already satisfied: typing-extensions>=4.10.0 in .\wakebot_env\Lib\site-packages (from torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (4.15.0)
Requirement already satisfied: sympy>=1.13.3 in .\wakebot_env\Lib\site-packages (from torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (1.14.0)
Requirement already satisfied: networkx>=2.5.1 in .\wakebot_env\Lib\site-packages (from torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (3.6.1)
Requirement already satisfied: jinja2 in .\wakebot_env\Lib\site-packages (from torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (3.1.6)
Requirement already satisfied: fsspec>=0.8.5 in .\wakebot_env\Lib\site-packages (from torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (2026.1.0)
Requirement already satisfied: mpmath<1.4,>=1.1.0 in .\wakebot_env\Lib\site-packages (from sympy>=1.13.3->torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (1.3.0)
Requirement already satisfied: pycparser in .\wakebot_env\Lib\site-packages (from cffi->sounddevice~=0.5->mediapipe>=0.10.0->-r requirements.txt (line 9)) (3.0)
Requirement already satisfied: more-itertools in .\wakebot_env\Lib\site-packages (from jaraco.classes->keyring>=24.0.0->-r requirements.txt (line 22)) (11.0.2) 
Requirement already satisfied: backports.tarfile in .\wakebot_env\Lib\site-packages (from jaraco.context->keyring>=24.0.0->-r requirements.txt (line 22)) (1.2.0)
Requirement already satisfied: MarkupSafe>=2.0 in .\wakebot_env\Lib\site-packages (from jinja2->torch->easyocr>=1.7.0->-r requirements.txt (line 12)) (3.0.3)   
Requirement already satisfied: contourpy>=1.0.1 in .\wakebot_env\Lib\site-packages (from matplotlib->mediapipe>=0.10.0->-r requirements.txt (line 9)) (1.3.3)   
Requirement already satisfied: cycler>=0.10 in .\wakebot_env\Lib\site-packages (from matplotlib->mediapipe>=0.10.0->-r requirements.txt (line 9)) (0.12.1)      
Requirement already satisfied: fonttools>=4.22.0 in .\wakebot_env\Lib\site-packages (from matplotlib->mediapipe>=0.10.0->-r requirements.txt (line 9)) (4.61.1) 
Requirement already satisfied: kiwisolver>=1.3.1 in .\wakebot_env\Lib\site-packages (from matplotlib->mediapipe>=0.10.0->-r requirements.txt (line 9)) (1.4.9)  
Requirement already satisfied: pyparsing>=3 in .\wakebot_env\Lib\site-packages (from matplotlib->mediapipe>=0.10.0->-r requirements.txt (line 9)) (3.3.1)       
Requirement already satisfied: python-dateutil>=2.7 in .\wakebot_env\Lib\site-packages (from matplotlib->mediapipe>=0.10.0->-r requirements.txt (line 9)) (2.9.0.post0)
Requirement already satisfied: pyperclip in .\wakebot_env\Lib\site-packages (from mouseinfo->pyautogui>=0.9.54->-r requirements.txt (line 3)) (1.11.0)
Requirement already satisfied: imageio!=2.35.0,>=2.33 in .\wakebot_env\Lib\site-packages (from scikit-image->easyocr>=1.7.0->-r requirements.txt (line 12)) (2.37.3)
Requirement already satisfied: tifffile>=2022.8.12 in .\wakebot_env\Lib\site-packages (from scikit-image->easyocr>=1.7.0->-r requirements.txt (line 12)) (2026.3.3)
Requirement already satisfied: lazy-loader>=0.4 in .\wakebot_env\Lib\site-packages (from scikit-image->easyocr>=1.7.0->-r requirements.txt (line 12)) (0.5)     
Setup complete! Run 'python calibrate.py' first.
Press any key to continue . . . 
(wakebot_env) PS D:\Coding\Projects\Wake_Bot> python -m wakebot run vision
D:\Coding\Projects\Wake_Bot\wakebot_env\Lib\site-packages\torch\cuda\__init__.py:63: FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead. If you did not install pynvml directly, please report this to the maintainers of the package that installed pynvml for you.
  import pynvml  # type: ignore[import]

    W A K E B O T  |  U N I F I E D  E N G I N E
    ------------------------------------------------
    [ STATUS ] Dashboard Active
    [ ENGINE ] Audio + Vision v2.1 (Unified)
    [ CTRL+C ] Graceful Shutdown
    ------------------------------------------------

[22:06:52] INFO    | Vosk Voice Detector initialized with restricted grammar.
[22:06:52] INFO    | Voice Detector thread active.
[22:06:52] WARNING | AI Face Detection initialization failed: module 'mediapipe' has no attribute 'solutions'. Falling back to GPU-accelerated Motion Detection.
[22:06:52] WARNING | CUDA not available. EasyOCR will use CPU (slower).
D:\Coding\Projects\Wake_Bot\wakebot_env\Lib\site-packages\torch\utils\data\dataloader.py:668: UserWarning: 'pin_memory' argument is set as true but no accelerator is found, then device pinned memory won't be used.
  warnings.warn(warn_msg)
[22:07:00] ACTION  | USER ARRIVED — Presence detected.
[22:07:00] ACTION  | UNIFIED TRIGGER: Welcome Home Sequence
[22:07:00] ACTION  | WELCOME HOME SEQUENCE STARTED
[22:07:02] ACTION  | System Wake & Unlock triggered
Exception in thread Thread-1 (orchestrator):
Traceback (most recent call last):
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\threading.py", line 1045, in _bootstrap_inner      
    self.run()
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\threading.py", line 982, in run
    self._target(*self._args, **self._kwargs)
  File "D:\Coding\Projects\Wake_Bot\wakebot\cli\vision_cmd.py", line 195, in orchestrator
    actions.welcome_home()
  File "D:\Coding\Projects\Wake_Bot\wakebot\core\actions.py", line 140, in welcome_home
    self.launch_or_maximize()  # 2. Workspace
    ^^^^^^^^^^^^^^^^^^^^^^^^^
h_or_maximize
    subprocess.Popen(['code'])
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\subprocess.py", line 1026, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\subprocess.py", line 1538, in _execute_child       
    hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [WinError 2] The system cannot find the file specified       
[22:07:28] INFO    | Vosk Final: 'wake up daddy's home'
[22:07:28] INFO    | KEYWORD MATCH: 'wake up' detected!
[22:07:49] INFO    | Vosk Final: 'home'
[22:07:56] ERROR   | Ollama query failed: HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded with url: /api/generate (Caused by NewConnectionError("HTTPConnection(host='localhost', port=11434): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it"))
[22:08:09] INFO    | Vosk Final: 'home'
[22:08:29] INFO    | Vosk Final: 'home'
[22:08:49] INFO    | Vosk Final: 'home'
[22:09:01] ERROR   | Ollama query failed: HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded with url: /api/generate (Caused by NewConnectionError("HTTPConnection(host='localhost', port=11434): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it"))
[22:09:09] INFO    | Vosk Final: 'home'
[22:09:25] INFO    | Vosk Final: 'home wake up daddy's home'
[22:09:25] INFO    | KEYWORD MATCH: 'wake up' detected!
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "D:\Coding\Projects\Wake_Bot\wakebot\__main__.py", line 4, in <module>   
    main()
  File "D:\Coding\Projects\Wake_Bot\wakebot\cli\main.py", line 77, in main      
    run_vision()
  File "D:\Coding\Projects\Wake_Bot\wakebot\cli\vision_cmd.py", line 262, in run_vision
    screen.stop()
  File "D:\Coding\Projects\Wake_Bot\wakebot\triggers\vision\screen.py", line 264, in stop
    self.join(timeout=5.0)
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\threading.py", line 1123, in join
    self._wait_for_tstate_lock(timeout=max(timeout, 0))
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\threading.py", line 1139, in _wait_for_tstate_lock 
    if lock.acquire(block, timeout):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
KeyboardInterrupt
(wakebot_env) PS D:\Coding\Projects\Wake_Bot> " the audio service, does not quiter add up her, and not works, nothing fires up when i say the keyword, to launch vs code spotify , also where is the modular tts features i said would be implenmtated, where is the mdoels folder, in which i would uplaod the kokoro model . onxx file and voies  .bin file, i applied the gemini api key , in .env but you are still not have made is useful ,why is the video of mine looking still very very sloppy, why is Ollama inactive shown in the GUI, why it's not getting intergrated, and with no  local model toggle. ... 