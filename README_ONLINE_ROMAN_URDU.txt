SHEHROAZ AI — ONLINE DEPLOYMENT (Render + Gemini)
=================================================

Is ZIP mein online backend configuration shamil hai:
- Chat ke liye Gemini API (key server environment mein rakhi jati hai)
- Render par Flask app chalane ke liye gunicorn aur render.yaml
- Local use ke liye Ollama fallback
- Existing third-party image generation endpoint

PUBLISH KARNE KE STEPS

1) GitHub par sign in karo: https://github.com/
2) New repository banao, naam: shehroaz-ai
3) ZIP extract karke files repository ke root mein upload karo.
   app.py, requirements.txt, render.yaml aur templates folder root mein hon.
4) Gemini API key banao: https://aistudio.google.com/apikey
   API key ko chat ya GitHub code mein mat bhejna.
5) Render kholo: https://render.com/
   New > Web Service par jao aur GitHub repository connect karo.
6) Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   Free plan select karo.
7) Render ke Environment settings mein yeh values add karo:
   GEMINI_API_KEY = tumhari apni Google AI Studio API key
   GEMINI_MODEL = gemini-2.5-flash
8) Deploy karo. Build complete hone par Render ka *.onrender.com URL tumhari public website hoga.

AGAR Render Blueprint option de, repository se render.yaml import bhi kar sakte ho.
GEMINI_API_KEY ki value phir bhi Render Environment settings mein khud dalni hogi.

IMPORTANT
- Main tumhare personal GitHub/Render accounts mein login ya deploy khud nahi kar sakta.
- Gemini free quota aur free hosting ki limits/availability badal sakti hain; lifetime unlimited guarantee nahi.
- Render free services idle hone par sleep kar sakti hain.
- Free filesystem permanent nahi hota; SQLite history aur uploaded files restart/redeploy par reset ho sakte hain.
- Public users ke messages tumhare backend aur AI provider ko bheje jayenge. Sensitive/private files upload na karo.
- Image generation third-party service par depend karti hai; rate limits ya downtime mumkin hai.
- API key sirf Render Environment settings mein rakho, frontend ya GitHub par nahi.
- Is simple version mein conversation history shared hai. Broad public launch se pehle user accounts, rate limits aur per-user isolated history add karna behtar hai.

LOCAL USE
Windows par local Ollama mode ke liye setup_windows.bat aur start_windows.bat bhi included hain.
