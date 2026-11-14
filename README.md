# Probitron Voice Assistant

Probitron is a Windows-focused Python assistant that accepts spoken commands
or typed commands in the terminal. It can speak responses, open supported
websites and Windows apps, search for files in a folder you choose, add
numbers, look up information on the web or Wikipedia, and inspect or install
Python packages.

## Requirements

- Windows with Python 3.9 or newer
- Internet access for online speech recognition, web searches, and lookups
- A microphone for voice input; without one, commands can be typed in the
  terminal
- Speakers or headphones for spoken responses

Install the Python dependencies from this directory:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`tkinter` is included with standard Windows Python installations and is used
to choose a folder for file searches. If it is missing, rerun the Python
installer and enable the Tcl/Tk component.

## Run

```powershell
.\.venv\Scripts\python.exe .\CUSTOM_AI_DT_ASSISSTANT.py
```

Probitron greets you and listens for one command at a time. Example requests:

- “What time is it?”
- “Open YouTube”
- “Open YouTube and GitHub”
- “Search for the latest Python release”
- “What is photosynthesis?”
- “Wikipedia Ada Lovelace”
- “Find files named report” (then choose a folder)
- “12 plus 5”
- “List voices” or “Change voice to 2”
- “Where is library requests?”
- “Install package rich” (installation requires typing `yes` to confirm)
- “Help”

File searches are limited to a selected folder and a bounded number of
directories and results. Say `exit` to stop the assistant, or press `Ctrl+C`
in the terminal.

## Microphone and speech

Speech recognition uses the online Google recognition service and requires an
internet connection. `PyAudio` enables microphone input; if it is unavailable,
Probitron falls back to typed commands in the terminal. The Windows `sapi5`
speech engine is used for spoken responses.

Web search and Wikipedia lookups also require an internet connection. If voice
input is unavailable, check Windows microphone permissions and the selected
input device. Reinstall the dependencies with the Python interpreter used to
run Probitron if imports are missing.
