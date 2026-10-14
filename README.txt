SHEHROAZ AI — LOCAL PERSONAL AI ASSISTANT
=========================================

WHAT'S INCLUDED
- Chat and coding assistant powered by Ollama
- Custom SHEHROAZ AI personality
- Conversation history saved locally in SQLite
- Saved notes/memory you can add and remove in the interface
- Upload readable TXT, MD, CSV, JSON, PDF, and DOCX documents for questions
- Optional web search (uses an online search provider; internet required)
- Optional local image generation connection (requires a separate image model/server)
- Responsive browser interface

IMPORTANT ABOUT "FREE"
Ollama and local model usage have no per-request API charge. Your computer,
electricity, storage, and internet downloads may still cost money. Local models
are limited by your computer's RAM and speed. This project does not train a
new foundation model from scratch; it configures an existing model.

WINDOWS QUICK START
1. Install Ollama: https://ollama.com/download
2. Install Python 3: https://www.python.org/downloads/
   During setup, tick "Add Python to PATH".
3. Extract this ZIP.
4. Double-click setup_windows.bat and wait for it to finish.
   It installs dependencies, downloads llama3.2, and creates shehroaz-ai.
5. Double-click start_windows.bat.
6. Open http://127.0.0.1:5000 in your browser.
7. Keep the terminal and Ollama running while using the AI.

MANUAL START
In the project folder:
  py -m pip install -r requirements.txt
  ollama pull llama3.2
  ollama create shehroaz-ai -f Modelfile
  py app.py

IMAGE GENERATION
The app now tries a public Pollinations image endpoint by default, so you can test
image generation without installing a local image model. This is a third-party service:
its access rules, availability, quality, and rate limits can change. It is NOT guaranteed
lifetime-free or unlimited. Do not send private/sensitive prompts to a third-party service.

Optional: if you run AUTOMATIC1111 Stable Diffusion WebUI with its API enabled, set
IMAGE_API_URL to your local WebUI base URL, for example:
  set IMAGE_API_URL=http://127.0.0.1:7860
  py app.py
This local option requires a suitable computer/GPU and disk space. Do not expose its API publicly.

WEB SEARCH
Web search needs internet. If the search provider changes or blocks requests, the
search feature may temporarily fail. The core local chatbot still works.

PRIVACY / SAFETY
- This app listens on 127.0.0.1 only (your own computer).
- Do not change it to public hosting without authentication, rate limits, and security.
- Uploaded files are stored in the local uploads folder. Delete them manually when
  no longer needed. Extracted text is sent to your local Ollama model.
- Conversation history and saved notes are stored in shehroaz_ai.db in this folder.
- Avoid uploading sensitive/private documents unless you understand the risks.


PUBLISHING ONLINE — IMPORTANT
This project currently uses Ollama at localhost for chat. That works on the computer
running the app, not for visitors on the public internet. To make it a public website,
you need a hosted backend and a hosted AI provider or a server that runs Ollama. Free
hosting often sleeps, has limited resources, or does not provide a GPU. The public image
provider is also third-party and may rate-limit requests. This ZIP is a project package;
it does not automatically publish itself or create a domain/hosting account.
Never put passwords, API keys, or private account credentials into source code.


Online deployment steps: README_ONLINE_ROMAN_URDU.txt
