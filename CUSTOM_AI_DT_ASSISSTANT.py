"""Probitron: a voice-controlled assistant with web lookup and local tools."""

import datetime
import importlib.util
import os
import re
import shutil
import subprocess
import base64
import sys
import webbrowser
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from urllib.parse import parse_qs, quote, quote_plus, urlparse

import pyttsx3
import requests
import speech_recognition as sr
import wikipedia
from bs4 import BeautifulSoup


ASSISTANT_NAME = "Probitron"
MAX_FILE_SEARCH_DIRECTORIES = 5000
MAX_FILE_SEARCH_RESULTS = 40

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "maps": "https://maps.google.com",
    "spotify": "https://open.spotify.com",
    "twitter": "https://twitter.com",
    "facebook": "https://www.facebook.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "twitch": "https://www.twitch.tv",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "zomato": "https://www.zomato.com",
    "ebay": "https://www.ebay.com",
    "wikipedia": "https://www.wikipedia.org",
    "yahoo": "https://www.yahoo.com",
    "bing": "https://www.bing.com",
    "duckduckgo": "https://duckduckgo.com",
    "quora": "https://www.quora.com",
    "medium": "https://medium.com",
    "pinterest": "https://www.pinterest.com",
    "tumblr": "https://www.tumblr.com",
    "flickr": "https://www.flickr.com",
    "vimeo": "https://vimeo.com",
    "soundcloud": "https://soundcloud.com",
    "discord": "https://discord.com",
    "slack": "https://slack.com",
    "trello": "https://trello.com",
    "asana": "https://asana.com",
    "notion": "https://www.notion.so",
    "drive": "https://drive.google.com",
    "dropbox": "https://www.dropbox.com",
    "box": "https://www.box.com",
    "onedrive": "https://onedrive.live.com",
    "icloud": "https://www.icloud.com",
    "wordpress": "https://wordpress.com",
    "wix": "https://www.wix.com",
    "weebly": "https://www.weebly.com",
    "shopify": "https://www.shopify.com",
    "etsy": "https://www.etsy.com",
    "kickstarter": "https://www.kickstarter.com",
    "indiegogo": "https://www.indiegogo.com",
}

SYSTEM_APPS = {
    "calculator": ("calculator", ["calc"]),
    "notepad": ("notepad", ["notepad"]),
    "paint": ("paint", ["mspaint"]),
    "file explorer": ("file explorer", ["explorer"]),
    "task manager": ("task manager", ["taskmgr"]),
    "command prompt":("command prompt", ["cmd"]),
    "control panel": ("control panel", ["control"]),
    "settings": ("settings", ["ms-settings:"]),
    "snipping tool": ("snipping tool", ["snippingtool"]),
    "wordpad": ("wordpad", ["write"]),
    "windows media player": ("windows media player", ["wmplayer"]),
    "paint 3d": ("paint 3d", ["ms-paint:"]),
    "magnifier": ("magnifier", ["magnify"]),
    "snip & sketch": ("snip & sketch", ["ms-screenclip:"]),
    "drive": ("drive", ["ms-drive:"]),
    "voice recorder": ("voice recorder", ["soundrecorder"]),
    "windows security": ("windows security", ["windowsdefender:"]),
    "windows terminal": ("windows terminal", ["wt"]),
    "xbox game bar": ("xbox game bar", ["xboxgamebar:"]),
    "windows powershell": ("windows powershell", ["powershell"]),
    "windows subsystem for linux": ("windows subsystem for linux", ["wsl"]),
    "windows update": ("windows update", ["ms-settings:windowsupdate"]),
    "windows defender": ("windows defender", ["windowsdefender:"]),
    "windows firewall": ("windows firewall", ["mmc", "wf.msc"]),
    "vs code": ("Visual Studio Code", ["code"]),
    "microsoft edge": ("Microsoft Edge", ["msedge"]),
    "microsoft store": ("Microsoft Store", ["ms-windows-store:"]),
    "microsoft teams": ("Microsoft Teams", ["teams"]),
    "onenote": ("OneNote", ["onenote"]),
    "outlook": ("Outlook", ["outlook"]),
    "powerpoint": ("PowerPoint", ["powerpnt"]),
    "excel": ("Excel", ["excel"]),
    "word": ("Word", ["winword"]),
    "skype": ("Skype", ["skype"]),
}

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
preferred_voice = next(
    (voice for voice in voices if "george" in voice.name.lower()),
    voices[0] if voices else None,
)
if preferred_voice is not None:
    engine.setProperty('voice', preferred_voice.id)
current_voice = preferred_voice


def speak(audio):
    engine.say(audio)
    engine.runAndWait()


def list_voices():
    if not voices:
        message = "No text-to-speech voices are installed."
        print(message)
        speak(message)
        return
    print("Available Probitron voices:")
    for index, voice in enumerate(voices, start=1):
        language = ", ".join(
            item.decode("utf-8", errors="replace") if isinstance(item, bytes) else str(item)
            for item in getattr(voice, "languages", [])
        )
        print(f"{index}. {voice.name}" + (f" ({language})" if language else ""))
    speak(f"I found {len(voices)} installed voices. See the list in the console.")


def set_voice(target):
    global current_voice
    target = target.strip().lower()
    if target.isdigit():
        index = int(target) - 1
        if 0 <= index < len(voices):
            current_voice = voices[index]
            engine.setProperty("voice", current_voice.id)
            speak(f"Voice changed to {current_voice.name}.")
            return True

    exact_matches = [voice for voice in voices if voice.name.lower() == target]
    matches = exact_matches or [
        voice for voice in voices
        if target and target in voice.name.lower()
    ]
    if len(matches) == 1:
        current_voice = matches[0]
        engine.setProperty("voice", current_voice.id)
        speak(f"Voice changed to {current_voice.name}.")
        return True
    if len(matches) > 1:
        print("More than one voice matches. Say 'list voices' and choose its number.")
        speak("More than one voice matches. Please choose a voice number.")
        return False
    print(f"No installed voice matches '{target}'.")
    speak("I couldn't find that installed voice. Say list voices to hear the options.")
    return False


def console_safe(text):
    encoding = sys.stdout.encoding or "utf-8"
    text = text.replace("\ufffd", " ")
    return text.encode(encoding, errors="replace").decode(encoding).strip()


def parse_addition(query):
    """Return a precise Decimal sum only when the request contains addition."""
    number_pattern = r"(?<![\w.])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?![\w.])"
    values = re.findall(number_pattern, query)
    if not values:
        return None

    remainder = re.sub(number_pattern, " ", query.lower())
    remainder = re.sub(
        r"\b(?:please|add|sum|calculate|compute|what|is|the|total|of|numbers?|values?|and|plus)\b",
        " ",
        remainder,
    )
    if re.sub(r"[\s,+=?]", "", remainder):
        return None
    try:
        decimals = [Decimal(value) for value in values]
        precision = max(len(value.as_tuple().digits) for value in decimals)
        with localcontext() as context:
            context.prec = precision + len(str(len(decimals))) + 2
            return sum(decimals, Decimal(0))
    except InvalidOperation:
        return None


def format_decimal(value):
    if value == value.to_integral_value():
        return str(value.quantize(Decimal(1)))
    return format(value.normalize(), "f")


def choose_directory():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(
            parent=root,
            title="Choose one folder for Probitron to search",
            mustexist=True,
        )
    finally:
        root.destroy()
    return Path(selected) if selected else None


def find_files(pattern, root):
    """Search file and folder names under one explicitly selected directory."""
    root = root.expanduser()
    if not root.is_dir():
        print(f"Folder not found: {root}")
        return []
    if root.parent == root:
        print("For safety, choose a specific folder instead of an entire drive.")
        return []

    target = pattern.casefold()
    found = []
    visited_directories = 0
    search_limited = False

    def report_walk_error(error):
        print(f"Could not inspect {error.filename}: {error}")

    for current, directories, filenames in os.walk(
        root, topdown=True, followlinks=False, onerror=report_walk_error
    ):
        visited_directories += 1
        directories[:] = [
            name for name in directories
            if not (Path(current) / name).is_symlink()
        ]
        for name in filenames:
            if target in name.casefold():
                found.append(Path(current) / name)
                if len(found) >= MAX_FILE_SEARCH_RESULTS:
                    search_limited = True
                    break
        if search_limited:
            break
        if visited_directories >= MAX_FILE_SEARCH_DIRECTORIES:
            search_limited = bool(directories)
            break

    if search_limited:
        print(
            f"Search limit reached ({visited_directories} folders or "
            f"{MAX_FILE_SEARCH_RESULTS} results). Choose a narrower folder."
        )
    if found:
        print("Matching paths:")
        for path in found:
            print(console_safe(str(path)))
        speak(f"I found {len(found)} matching file names.")
    else:
        print(f"No file names containing '{pattern}' were found under {root}.")
        speak("I couldn't find a matching file name in that folder.")
    return found


def locate_library(module_name):
    if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module_name):
        print("Use a Python module name, for example 'numpy' or 'PIL.Image'.")
        return
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, ModuleNotFoundError, ValueError) as error:
        print(f"Could not inspect module '{module_name}': {error}")
        return
    if spec is None:
        message = (
            f"Module '{module_name}' was not found for {sys.executable}. "
            f"To install it, say: install package {module_name}"
        )
        print(message)
        speak(message)
        return
    location = spec.origin or (
        ", ".join(str(path) for path in spec.submodule_search_locations or [])
    )
    print(f"{module_name} is available at: {location}")
    speak(f"{module_name} is installed.")


def install_package(package_name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", package_name):
        print("That package name is not valid.")
        return
    print(
        f"This will install '{package_name}' into the current Python environment:\n"
        f"  {sys.executable} -m pip install {package_name}"
    )
    try:
        answer = input("Type 'yes' to confirm the installation: ").strip().lower()
    except EOFError:
        print("Installation cancelled because confirmation was unavailable.")
        return
    if answer != "yes":
        print("Installation cancelled.")
        return
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            check=False,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Package installation could not be completed: {error}")
        return
    if result.returncode == 0:
        print(f"Installed '{package_name}'.")
        speak(f"Installed {package_name}.")
    else:
        print(
            f"pip failed to install '{package_name}' "
            f"(exit code {result.returncode})."
        )
        speak(f"I could not install {package_name}. See the console for details.")


def wish_me():
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning, boss."
    elif hour < 18:
        greeting = "Good afternoon, boss."
    else:
        greeting = "Good evening, boss."
    speak(f"{greeting} {ASSISTANT_NAME} is online.")


def take_command():
    """Listen for one spoken command and return recognized text."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            r.pause_threshold = 1
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
    except sr.WaitTimeoutError:
        print("No speech detected.")
        return ""
    except (AttributeError, OSError) as error:
        print(f"Microphone unavailable: {error}")
        print("Install PyAudio to enable voice input. Enter a command below instead.")
        try:
            return input("Command: ").strip().lower()
        except EOFError:
            return "exit"

    try:
        query = r.recognize_google(audio, language="en-in")
        print(f"You said: {query}\n")
        return query.strip().lower()
    except sr.UnknownValueError:
        print("I couldn't understand that. Please try again.")
    except sr.RequestError as error:
        print(f"Speech recognition service error: {error}")
    return ""


def open_website(name):
    url = WEBSITES[name]
    webbrowser.open(url)
    speak(f"Opening {name}.")


def resolve_search_url(url):
    parsed_url = urlparse(url)
    if parsed_url.netloc.endswith("bing.com") and parsed_url.path.startswith("/ck/a"):
        encoded_url = parse_qs(parsed_url.query).get("u", [""])[0]
        if encoded_url.startswith("a1"):
            encoded_url = encoded_url[2:]
            padding = "=" * (-len(encoded_url) % 4)
            try:
                url = base64.urlsafe_b64decode(encoded_url + padding).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                return ""
    if url.startswith(("http://", "https://")) and "bing.com/ck/a" not in url:
        return url
    return ""


def search_web(query, max_results=5):
    response = requests.get(
        "https://www.bing.com/search",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=12,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select("li.b_algo"):
        title_link = item.select_one("h2 a")
        if title_link is None:
            continue
        url = resolve_search_url(title_link.get("href", ""))
        if not url:
            continue
        snippet_element = item.select_one(".b_caption p") or item.select_one("p")
        results.append({
            "title": title_link.get_text(" ", strip=True),
            "url": url,
            "snippet": snippet_element.get_text(" ", strip=True).replace("\ufffd", " ") if snippet_element else "",
        })
        if len(results) >= max_results:
            break

    return results


def definition_topic(query):
    match = re.match(
        r"^(?:what is|what are|what's|define)\s+(?:(?:a|an|the)\s+)?(.+?)[?.!]*$",
        query.strip(),
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def fetch_definition(topic):
    page_title = quote(topic.replace(" ", "_"), safe="()")
    response = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}",
        headers={"User-Agent": f"{ASSISTANT_NAME}/1.0 (educational project)"},
        timeout=8,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("type") != "standard":
        return None
    extract = data.get("extract", "").strip()
    source_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
    if not extract:
        return None
    return extract, data.get("title", topic), source_url


def fetch_page_text(url, max_bytes=500_000):
    with requests.get(
        url,
        headers={"User-Agent": f"Mozilla/5.0 (compatible; {ASSISTANT_NAME}/1.0)"},
        timeout=8,
        stream=True,
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            return ""

        page_bytes = bytearray()
        for chunk in response.iter_content(chunk_size=16_384):
            if not chunk:
                continue
            remaining = max_bytes - len(page_bytes)
            page_bytes.extend(chunk[:remaining])
            if len(chunk) >= remaining:
                break

    soup = BeautifulSoup(bytes(page_bytes), "html.parser")
    for element in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        element.decompose()
    paragraphs = []
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True).replace("\ufffd", " ")
        words = text.split()
        linked_words = sum(len(link.get_text(" ", strip=True).split()) for link in paragraph.find_all("a"))
        if len(words) >= 8 and linked_words / len(words) < 0.5:
            paragraphs.append(text)
    return " ".join(dict.fromkeys(paragraphs))


def normalize_search_word(word):
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("s"):
        return word[:-1]
    return word


def summarize_search_results(query, results):
    ignored_words = {"a", "an", "are", "about", "can", "could", "did", "do", "does", "for", "how", "i", "is", "me", "of", "on", "or", "please", "tell", "that", "the", "to", "what", "when", "where", "which", "who", "why"}
    query_words = {
        normalize_search_word(word)
        for word in re.findall(r"[a-z0-9]+", query.lower())
    } - ignored_words
    ranked_evidence = []

    for result_index, result in enumerate(results[:3]):
        try:
            page_text = fetch_page_text(result["url"])
        except requests.RequestException:
            page_text = ""

        ranked_sentences = []
        for text, source_bonus in ((result["snippet"], 2), (page_text, 0)):
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                sentence = re.sub(r"\s+", " ", sentence.replace("\ufffd", " ")).strip()
                if len(sentence) < 35:
                    continue
                words = {
                    normalize_search_word(word)
                    for word in re.findall(r"[a-z0-9]+", sentence.lower())
                }
                score = len(query_words & words)
                minimum_score = 2 if len(query_words) >= 3 else 1
                if score >= minimum_score:
                    ranked_sentences.append((score + source_bonus, sentence))

        ranked_sentences.sort(key=lambda item: item[0], reverse=True)
        fallback_text = result["snippet"] or page_text
        if ranked_sentences:
            ranked_evidence.extend(
                (score, result_index, sentence)
                for score, sentence in ranked_sentences[:2]
            )
        elif fallback_text:
            ranked_evidence.append((0, result_index, fallback_text[:350].rsplit(" ", 1)[0]))

    selected_evidence = sorted(ranked_evidence, key=lambda item: item[0], reverse=True)[:5]
    unique_evidence = list(dict.fromkeys(
        sentence.rstrip(" .") for _, _, sentence in selected_evidence
    ))
    source_indexes = {source_index for _, source_index, _ in selected_evidence}
    sources = [result for index, result in enumerate(results[:3]) if index in source_indexes]
    return " ".join(unique_evidence), sources


def answer_web_question(query):
    print(console_safe(f"Searching the web for: {query}"))

    topic = definition_topic(query)
    if topic:
        try:
            definition = fetch_definition(topic)
        except requests.RequestException as error:
            print(f"Definition lookup failed: {error}")
            definition = None
        if definition:
            answer, title, source_url = definition
            print("\nAnswer:")
            print(console_safe(answer))
            if source_url:
                print(console_safe(f"Source: {title} - {source_url}"))
            speak(console_safe(answer[:500]))
            return

    try:
        results = search_web(query)
    except requests.RequestException as error:
        print(f"Web search failed: {error}")
        webbrowser.open(f"https://www.bing.com/search?q={quote_plus(query)}")
        speak("I couldn't fetch search results. I opened the search in your browser.")
        return

    if not results:
        webbrowser.open(f"https://www.bing.com/search?q={quote_plus(query)}")
        speak("I couldn't read the search results, so I opened them in your browser.")
        return

    answer, sources = summarize_search_results(query, results)
    if not answer:
        answer = "I found search results, but couldn't retrieve readable page text."

    print("\nSummary from web results:")
    print(console_safe(answer))
    if sources:
        print("\nSources:")
        for index, source in enumerate(sources, start=1):
            print(console_safe(f"{index}. {source['title']} - {source['url']}"))
    speak(console_safe(answer[:500]))


def open_system_app(name):
    display_name, command = SYSTEM_APPS[name]
    try:
        if name == "vs code":
            executable = shutil.which("code")
            if executable is None:
                executable_path = Path.home() / "AppData/Local/Programs/Microsoft VS Code/Code.exe"
                if not executable_path.is_file():
                    raise FileNotFoundError("Visual Studio Code was not found.")
                executable = str(executable_path)
            command = [executable]
        if ":" in command[0]:
            os.startfile(command[0])
        else:
            subprocess.Popen(command)
        speak(f"Opening {display_name}.")
    except OSError as error:
        print(f"Could not open {display_name}: {error}")
        speak(f"I couldn't open {display_name}.")


def handle_command(query):
    """Run a supported command. Return False when the user asks to quit."""
    if not query:
        return True

    if query in {
        "exit", "quit", "stop", "goodbye", "shut down assistant",
        f"shut down {ASSISTANT_NAME.lower()}",
    }:
        speak("Goodbye.")
        return False

    if query.startswith("& ") or re.match(r"^(?:python(?:\.exe)?|py)\s", query) or (
        "python.exe" in query and ".py" in query
    ):
        print(f"That looks like a PowerShell launch command. {ASSISTANT_NAME} is already running; enter a question or type exit.")
        speak(f"{ASSISTANT_NAME} is already running. Enter a question or say exit.")
        return True

    if query in {"help", "what can you do", "list commands"}:
        print(
            "Commands: add <numbers>; open a website or app; search for <topic>; "
            "wikipedia <topic>; list voices; change voice to <name or number>; "
            "where is library <module>; install package <name> (asks for confirmation); "
            "find file <name> (choose a folder); what time is it; date; help; exit."
        )
        speak(
            "I can add numbers, open websites and Windows apps, search the web, "
            "look up Wikipedia, switch voices, find files in a folder you choose, "
            "and locate Python libraries."
        )
        return True

    if query in {"list voices", "show voices", "what voices are available"}:
        list_voices()
        return True

    voice_match = re.match(
        r"^(?:change|set|use)\s+voice(?:\s+to)?\s+(.+)$|^voice\s+(.+)$",
        query,
    )
    if voice_match:
        set_voice(voice_match.group(1) or voice_match.group(2))
        return True

    addition = parse_addition(query)
    if addition is not None:
        result = format_decimal(addition)
        response = f"The sum is {result}."
        print(response)
        speak(response)
        return True

    library_match = re.match(
        r"^(?:where is|find|locate)\s+(?:the\s+)?(?:python\s+)?library\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)$",
        query,
    )
    if library_match:
        locate_library(library_match.group(1))
        return True

    install_match = re.match(r"^install\s+package\s+([a-zA-Z0-9._-]+)$", query)
    if install_match:
        install_package(install_match.group(1))
        return True

    file_match = re.match(r"^(?:find|search for)\s+file\s+(.+)$", query)
    if file_match:
        request = file_match.group(1).strip()
        pattern, separator, directory = request.rpartition(" in ")
        if not separator:
            pattern = request
            root = choose_directory()
        else:
            root = Path(directory.strip().strip("\"'")).expanduser()
        pattern = pattern.strip().strip("\"'")
        if not pattern:
            print("Say a file name or part of a name to search for.")
            return True
        if root is None:
            print("File search cancelled; no folder was selected.")
            return True
        find_files(pattern, root)
        return True
    if query.startswith("open ") and " and " in query:
        site_names = [name.strip() for name in query[5:].split(" and ")]
        site_names = ["chatgpt" if name == "chat gpt" else name for name in site_names]
        if len(site_names) > 1 and all(name in WEBSITES for name in site_names):
            for name in site_names:
                open_website(name)
            return True

    for name in WEBSITES:
        if query in {f"open {name}", name} or (name == "chatgpt" and query == "open chat gpt"):
            open_website(name)
            return True

    if query in {"open browser", "open web browser", "browser"}:
        webbrowser.open("https://www.google.com")
        speak("Opening your browser.")
        return True

    if query in {"play music", "play spotify"}:
        open_website("spotify")
        return True

    if query.startswith("search for ") or query.startswith("google "):
        search_term = query.removeprefix("search for ").removeprefix("google ").strip()
        if search_term:
            answer_web_question(search_term)
        return True

    if "wikipedia" in query:
        topic = query.replace("wikipedia", "").replace("search", "").strip()
        if not topic:
            speak("Please say a topic to look up on Wikipedia.")
            return True
        try:
            result = wikipedia.summary(topic, sentences=2)
            print(result)
            speak(f"According to Wikipedia: {result}")
        except wikipedia.exceptions.DisambiguationError:
            speak("That topic has several results. Please be more specific.")
        except wikipedia.exceptions.PageError:
            speak("I couldn't find that topic on Wikipedia.")
        except wikipedia.exceptions.WikipediaException as error:
            print(f"Wikipedia lookup failed: {error}")
            speak("The Wikipedia lookup failed.")
        except requests.exceptions.RequestException as error:
            print(f"Wikipedia request failed: {error}")
            speak("Wikipedia is unavailable. Searching the web instead.")
            answer_web_question(topic)
        return True

    if query in {"the time", "what time is it", "tell me the time"}:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}.")
        return True

    if query in {"the date", "what is today's date", "what is the date", "tell me the date"}:
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {current_date}.")
        return True

    if query in {"open settings", "settings"}:
        open_system_app("settings")
        return True

    for alias in SYSTEM_APPS:
        if query in {alias, f"open {alias}", f"start {alias}"} or (
            alias == "vs code" and query in {"open code", "start code"}
        ):
            open_system_app(alias)
            return True

    answer_web_question(query)
    return True


if __name__ == "__main__":
    wish_me()
    try:
        while handle_command(take_command()):
            pass
    except KeyboardInterrupt:
        print("Probitron stopped.")
