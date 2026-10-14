import os
import sqlite3
import time
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "shehroaz_ai.db"
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "shehroaz-ai")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
# Optional: set IMAGE_API_URL to a local Stable Diffusion WebUI API endpoint.
IMAGE_API_URL = os.environ.get("IMAGE_API_URL", "").strip()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

SYSTEM_PROMPT = """You are SHEHROAZ AI, a helpful personal assistant created for the SHEHROAZ FAISAL project.
Reply in the language the user uses; Roman Urdu is welcome. Help with general questions, writing, learning,
brainstorming, and coding. Be clear and honest. Do not claim you performed actions you did not perform.
If the user provides document context, use it carefully and say when the answer is not in the document.
For coding, provide runnable examples and explain important setup steps.
"""

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )""")

def saved_memory():
    with db() as con:
        rows = con.execute("SELECT note FROM memory ORDER BY id DESC LIMIT 30").fetchall()
    return "\n".join("- " + r["note"] for r in reversed(rows))

def get_recent_messages(limit=16):
    with db() as con:
        rows = con.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def ollama_chat(messages):
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=240
    )
    if response.status_code == 404:
        raise RuntimeError(
            f"Model '{MODEL}' nahi mila. CMD mein 'ollama pull llama3.2' aur phir "
            "'ollama create shehroaz-ai -f Modelfile' chalao."
        )
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "").strip()


def gemini_chat(messages):
    """Use Gemini server-side; never expose the API key to browser JavaScript."""
    system_text = "\\n\\n".join(
        item["content"] for item in messages if item.get("role") == "system"
    )
    contents = []
    for item in messages:
        role = item.get("role")
        if role == "system":
            continue
        contents.append({
            "role": "model" if role == "assistant" else "user",
            "parts": [{"text": str(item.get("content", ""))}]
        })
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}
    response = requests.post(url, params={"key": GEMINI_API_KEY}, json=payload, timeout=120)
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", {}).get("message", "Gemini request failed")
        except Exception:
            detail = "Gemini request failed"
        raise RuntimeError(f"Gemini API error ({response.status_code}): {detail}")
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini ne is dafa koi jawab return nahi kiya.")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\\n".join(part.get("text", "") for part in parts).strip()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/history")
def history():
    with db() as con:
        rows = con.execute("SELECT id, role, content, created_at FROM messages ORDER BY id ASC LIMIT 300").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Pehle apna message likho."}), 400
    if len(message) > 20000:
        return jsonify({"error": "Message bohat lamba hai. Chhota message bhejo."}), 400

    with db() as con:
        con.execute("INSERT INTO messages(role,content,created_at) VALUES(?,?,?)",
                    ("user", message, int(time.time())))

    doc_context = str(body.get("document_context", "")).strip()[:12000]
    memory = saved_memory()
    system = SYSTEM_PROMPT
    if memory:
        system += "\n\nSaved user notes (use only if relevant):\n" + memory
    if doc_context:
        system += "\n\nUser-provided document context:\n" + doc_context

    messages = [{"role": "system", "content": system}]
    # Keep recent chat, and avoid adding the latest user message twice.
    recent = get_recent_messages(17)
    if recent and recent[-1]["role"] == "user" and recent[-1]["content"] == message:
        recent = recent[:-1]
    messages.extend(recent[-14:])
    messages.append({"role": "user", "content": message})

    try:
        answer = gemini_chat(messages) if GEMINI_API_KEY else ollama_chat(messages)
        if not answer:
            answer = "Model ne khaali jawab diya. Dobara try karo."
        with db() as con:
            con.execute("INSERT INTO messages(role,content,created_at) VALUES(?,?,?)",
                        ("assistant", answer, int(time.time())))
        return jsonify({"answer": answer})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Ollama se connection nahi ho raha. Ollama app start karo, phir CMD mein 'ollama pull llama3.2' chalao."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "AI ko jawab dene mein zyada waqt lag raha hai. Chhota sawal try karo."}), 504
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502

@app.post("/api/clear")
def clear_chat():
    with db() as con:
        con.execute("DELETE FROM messages")
    return jsonify({"ok": True})

@app.get("/api/memory")
def get_memory():
    with db() as con:
        rows = con.execute("SELECT id,note,created_at FROM memory ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/memory")
def add_memory():
    body = request.get_json(silent=True) or {}
    note = str(body.get("note", "")).strip()
    if not note:
        return jsonify({"error": "Memory note khaali hai."}), 400
    if len(note) > 1000:
        return jsonify({"error": "Memory note 1000 characters se chhota rakho."}), 400
    with db() as con:
        con.execute("INSERT INTO memory(note,created_at) VALUES(?,?)", (note, int(time.time())))
    return jsonify({"ok": True})

@app.delete("/api/memory/<int:memory_id>")
def delete_memory(memory_id):
    with db() as con:
        con.execute("DELETE FROM memory WHERE id=?", (memory_id,))
    return jsonify({"ok": True})

@app.post("/api/upload")
def upload():
    if "file" not in request.files:
        return jsonify({"error": "File select karo."}), 400
    f = request.files["file"]
    name = Path(f.filename or "upload").name
    ext = Path(name).suffix.lower()
    allowed = {".txt", ".md", ".csv", ".json", ".pdf", ".docx"}
    if ext not in allowed:
        return jsonify({"error": "Supported files: TXT, MD, CSV, JSON, PDF, DOCX."}), 400
    safe_name = str(int(time.time())) + "_" + name.replace(" ", "_")
    path = UPLOAD_DIR / safe_name
    f.save(path)
    try:
        if ext in {".txt", ".md", ".csv", ".json"}:
            content = path.read_text(encoding="utf-8", errors="replace")
        elif ext == ".pdf":
            if PdfReader is None:
                return jsonify({"error": "PDF reader installed nahi. Run: py -m pip install pypdf"}), 500
            reader = PdfReader(str(path))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            if Document is None:
                return jsonify({"error": "DOCX reader installed nahi. Run: py -m pip install python-docx"}), 500
            doc = Document(str(path))
            content = "\n".join(p.text for p in doc.paragraphs)
        content = content[:12000]
        if not content.strip():
            return jsonify({"error": "Is file se readable text nahi mila. Scanned PDF ke liye OCR chahiye."}), 400
        return jsonify({"filename": name, "content": content, "characters": len(content)})
    except Exception as exc:
        return jsonify({"error": f"File read nahi ho saki: {exc}"}), 400

@app.post("/api/search")
def web_search():
    body = request.get_json(silent=True) or {}
    query = str(body.get("query", "")).strip()
    if not query:
        return jsonify({"error": "Search query likho."}), 400
    if DDGS is None:
        return jsonify({"error": "Web search package missing. Run: py -m pip install ddgs"}), 500
    try:
        results = list(DDGS().text(query, max_results=5))
        return jsonify({"results": [
            {"title": x.get("title", ""), "url": x.get("href", ""), "snippet": x.get("body", "")}
            for x in results
        ]})
    except Exception as exc:
        return jsonify({"error": f"Web search abhi available nahi: {exc}"}), 502

@app.post("/api/image")
def generate_image():
    body = request.get_json(silent=True) or {}
    prompt = str(body.get("prompt", "")).strip()
    if not prompt:
        return jsonify({"error": "Image ka prompt likho."}), 400

    # Option 1: user's own local Stable Diffusion WebUI API.
    if IMAGE_API_URL:
        try:
            response = requests.post(
                IMAGE_API_URL.rstrip("/") + "/sdapi/v1/txt2img",
                json={"prompt": prompt, "steps": 20, "width": 768, "height": 768},
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            if data.get("images"):
                return jsonify({"image": "data:image/png;base64," + data["images"][0]})
            return jsonify({"error": "Local image model ne image return nahi ki."}), 502
        except Exception as exc:
            return jsonify({"error": f"Local image generation fail hui: {exc}"}), 502

    # Option 2: public hosted image endpoint. This is third-party, may be
    # rate-limited, change its access rules, or become unavailable; not guaranteed
    # lifetime-free. The request is made server-side to avoid browser CORS issues.
    try:
        from urllib.parse import quote
        import base64
        encoded_prompt = quote(prompt, safe="")
        image_url = (
            "https://image.pollinations.ai/prompt/" + encoded_prompt
            + "?width=768&height=768&model=flux&nologo=true"
        )
        response = requests.get(
            image_url,
            headers={"User-Agent": "SHEHROAZ-AI/1.0"},
            timeout=180
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg")
        if not content_type.startswith("image/"):
            return jsonify({"error": "Image provider ne image ke bajaye unexpected response diya. Baad mein try karo."}), 502
        encoded = base64.b64encode(response.content).decode("ascii")
        return jsonify({"image": f"data:{content_type};base64,{encoded}", "provider": "Pollinations (third-party)"})
    except requests.exceptions.Timeout:
        return jsonify({"error": "Image provider ka response slow tha. Dobara try karo."}), 504
    except Exception as exc:
        return jsonify({
            "error": "Free online image provider abhi available nahi ya uski limits khatam ho sakti hain. "
                     "Baad mein try karo. Public provider lifetime-free ya unlimited hone ki guarantee nahi deta. "
                     f"Technical detail: {str(exc)[:250]}"
        }), 502

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"SHEHROAZ AI running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
