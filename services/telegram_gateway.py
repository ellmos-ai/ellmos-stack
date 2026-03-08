#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Gateway -- Rezeption fuer den ellmos-stack.

Architektur:
    1. Server empfaengt ALLE Telegram-Nachrichten (einziger Polling-Endpoint)
    2. Prueft ob BACH erreichbar ist (Laptop-Heartbeat)
    3. JA  -> Leitet an BACH weiter, BACH antwortet via Telegram
    4. NEIN -> qwen3 antwortet direkt (mit Rinnsal Memory-Kontext)

Env-Variablen:
    RINNSAL_TELEGRAM_TOKEN  -- Bot-Token von @BotFather
    TELEGRAM_OWNER_CHAT_ID  -- Deine Chat-ID (nur du darfst schreiben)
    OLLAMA_MODEL            -- LLM-Modell (default: qwen3:4b)
    BACH_HEARTBEAT_URL      -- URL fuer BACH-Erreichbarkeit (optional, Stufe 2)

Usage:
    python telegram_gateway.py                # Starten
    python telegram_gateway.py --test         # Verbindungstest
    python telegram_gateway.py --send "Text"  # Einmalig senden
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# === Config ===
BOT_TOKEN = os.environ.get("RINNSAL_TELEGRAM_TOKEN", "")
OWNER_CHAT_ID = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
BACH_HEARTBEAT_URL = os.environ.get("BACH_HEARTBEAT_URL", "")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROMPT_FILE = Path(__file__).resolve().parent.parent / "config" / "system_prompt.txt"
MEMORY_FILE = DATA_DIR / "rinnsal" / "rinnsal.db"
HISTORY_FILE = DATA_DIR / "telegram_history.jsonl"

TG_API = "https://api.telegram.org/bot{token}/{method}"

# Conversation context (last N messages)
MAX_CONTEXT = 10
_context = []
_last_update_id = 0


# === Telegram API ===

def tg_call(method: str, params: dict = None, timeout: int = 15):
    """Telegram Bot API aufrufen."""
    url = TG_API.format(token=BOT_TOKEN, method=method)
    if params:
        data = json.dumps(params, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
    else:
        req = urllib.request.Request(url)

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        if body.get("ok"):
            return body.get("result")
    return None


def send_message(chat_id: str, text: str):
    """Nachricht senden mit Markdown-Fallback."""
    try:
        return tg_call("sendMessage", {
            "chat_id": chat_id, "text": text, "parse_mode": "Markdown"
        })
    except Exception:
        return tg_call("sendMessage", {"chat_id": chat_id, "text": text})


def send_typing(chat_id: str):
    """Typing-Indicator senden."""
    try:
        tg_call("sendChatAction", {"chat_id": chat_id, "action": "typing"})
    except Exception:
        pass


# === BACH Heartbeat (Stufe 2) ===

def bach_is_available() -> bool:
    """Prueft ob BACH (Laptop) erreichbar ist."""
    if not BACH_HEARTBEAT_URL:
        return False
    try:
        req = urllib.request.Request(BACH_HEARTBEAT_URL)
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def forward_to_bach(message: str, chat_id: str) -> bool:
    """Leitet Nachricht an BACH weiter. Returns True wenn erfolgreich."""
    # Stufe 2: Implementierung wenn BACH-Bridge steht
    # BACH verarbeitet und antwortet selbst via Telegram
    return False


# === Ollama (Lokaler Fallback) ===

def load_system_prompt() -> str:
    """System-Prompt laden."""
    base = ""
    if PROMPT_FILE.exists():
        base = PROMPT_FILE.read_text(encoding="utf-8").strip()

    # Telegram-spezifische Ergaenzung
    tg_addon = """
TELEGRAM-MODUS:
- Du antwortest auf Telegram-Nachrichten des Besitzers
- Halte Antworten kurz (max 2-3 Absaetze) -- Telegram ist kein Dokument
- Nutze Markdown sparsam (fett, kursiv, Code -- kein HTML)
- Bei Aufgaben: Bestaetigen und in Rinnsal-Tasks eintragen
- Bei Fragen die du nicht beantworten kannst: Ehrlich sagen
"""
    return f"{base}\n{tg_addon}" if base else tg_addon.strip()


def build_context_prompt(new_message: str) -> str:
    """Baut Prompt mit Konversations-Kontext."""
    parts = []
    if _context:
        parts.append("Bisheriger Verlauf:")
        for msg in _context[-MAX_CONTEXT:]:
            role = "User" if msg["role"] == "user" else "Du"
            parts.append(f"{role}: {msg['content']}")
        parts.append("")
    parts.append(f"User: {new_message}")
    return "\n".join(parts)


def ask_ollama(prompt: str, system: str = "") -> str:
    """Anfrage an Ollama."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"/no_think\n{prompt}" if "qwen" in OLLAMA_MODEL.lower() else prompt,
        "system": system or load_system_prompt(),
        "stream": False,
        "options": {"temperature": 0.5},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate", data=data,
        headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    text = result.get("response", "").strip()
    # Thinking-Tags entfernen
    if "<think>" in text:
        import re
        text = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
    return text


# === Memory Integration ===

def save_to_history(role: str, content: str, chat_id: str = ""):
    """Nachricht in History-File speichern."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content,
        "chat_id": chat_id,
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def try_rinnsal_memory(message: str):
    """Versucht relevanten Memory-Kontext aus Rinnsal zu laden."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from rinnsal import memory
        memory.init(str(MEMORY_FILE))
        results = memory.search(message, limit=3)
        if results:
            return "\n".join(f"- {r.get('content', '')[:200]}" for r in results)
    except Exception:
        pass
    return ""


# === Command Handling ===

def handle_command(text: str, chat_id: str) -> str:
    """Verarbeitet /commands."""
    cmd = text.strip().lower()

    if cmd == "/start":
        return ("ellmos-stack Telegram Gateway\n\n"
                "Ich bin dein KI-Assistent auf dem Server. "
                "Schreib mir einfach -- ich antworte mit qwen3.\n\n"
                "Befehle:\n"
                "/status -- Server-Status\n"
                "/queue -- KnowledgeDigest Queue\n"
                "/tasks -- Offene Tasks\n"
                "/help -- Diese Hilfe")

    elif cmd == "/status":
        try:
            r = urllib.request.urlopen(f"{OLLAMA_URL}/api/version", timeout=5)
            ollama_v = json.loads(r.read()).get("version", "?")
        except Exception:
            ollama_v = "offline"
        bach_status = "erreichbar" if bach_is_available() else "nicht erreichbar"
        return (f"*Server-Status*\n"
                f"Ollama: {ollama_v} ({OLLAMA_MODEL})\n"
                f"BACH: {bach_status}")

    elif cmd == "/queue":
        try:
            import sqlite3
            db = DATA_DIR / "knowledgedigest" / "knowledge.db"
            c = sqlite3.connect(str(db))
            c.row_factory = sqlite3.Row
            rows = c.execute("SELECT status, COUNT(*) as cnt FROM digest_queue GROUP BY status").fetchall()
            total = c.execute("SELECT COUNT(*) FROM summaries").fetchone()[0]
            c.close()
            lines = [f"*KnowledgeDigest Queue*"]
            for r in rows:
                lines.append(f"  {r['status']}: {r['cnt']}")
            lines.append(f"Summaries gesamt: {total}")
            return "\n".join(lines)
        except Exception as e:
            return f"Queue-Abfrage fehlgeschlagen: {e}"

    elif cmd == "/tasks":
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from rinnsal import tasks
            tasks.init(str(MEMORY_FILE))
            open_tasks = tasks.list(status="open", limit=10)
            if not open_tasks:
                return "Keine offenen Tasks."
            lines = ["*Offene Tasks:*"]
            for t in open_tasks:
                lines.append(f"  [{t.get('priority', '?')}] {t.get('title', '?')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Tasks-Abfrage fehlgeschlagen: {e}"

    elif cmd == "/help":
        return handle_command("/start", chat_id)

    return ""


# === Main Loop ===

def process_message(text: str, chat_id: str) -> str:
    """Verarbeitet eine eingehende Nachricht und gibt Antwort zurueck."""

    # Commands
    if text.startswith("/"):
        response = handle_command(text, chat_id)
        if response:
            return response

    # Stufe 2: BACH-Weiterleitung
    if bach_is_available():
        if forward_to_bach(text, chat_id):
            return ""  # BACH antwortet selbst

    # Kontext aus Rinnsal Memory
    memory_context = try_rinnsal_memory(text)
    prompt = build_context_prompt(text)
    if memory_context:
        prompt = f"Relevanter Kontext aus dem Gedaechtnis:\n{memory_context}\n\n{prompt}"

    # Ollama
    response = ask_ollama(prompt)

    # Kontext aktualisieren
    _context.append({"role": "user", "content": text})
    _context.append({"role": "assistant", "content": response})

    return response


def poll_loop():
    """Hauptschleife: Telegram Long-Polling."""
    global _last_update_id

    print(f"[Gateway] Gestartet -- Modell: {OLLAMA_MODEL}")
    print(f"[Gateway] Owner: {OWNER_CHAT_ID or 'alle'}")
    print(f"[Gateway] BACH Heartbeat: {BACH_HEARTBEAT_URL or 'deaktiviert'}")

    while True:
        try:
            updates = tg_call("getUpdates", {
                "offset": _last_update_id + 1,
                "limit": 10,
                "timeout": 30,
            }, timeout=40)

            if not updates:
                continue

            for update in updates:
                _last_update_id = max(_last_update_id, update.get("update_id", 0))
                msg = update.get("message")
                if not msg:
                    continue

                chat = msg.get("chat", {})
                chat_id = str(chat.get("id", ""))
                text = msg.get("text", "")

                # Owner-Filter
                if OWNER_CHAT_ID and chat_id != OWNER_CHAT_ID:
                    continue

                if not text:
                    continue

                sender = msg.get("from", {}).get("first_name", "?")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {sender}: {text[:80]}")

                # Typing anzeigen
                send_typing(chat_id)

                # History speichern
                save_to_history("user", text, chat_id)

                # Verarbeiten
                try:
                    response = process_message(text, chat_id)
                    if response:
                        send_message(chat_id, response)
                        save_to_history("assistant", response, chat_id)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot: {response[:80]}")
                except Exception as e:
                    error_msg = f"Fehler bei Verarbeitung: {type(e).__name__}"
                    send_message(chat_id, error_msg)
                    print(f"[ERROR] {e}", file=sys.stderr)

        except KeyboardInterrupt:
            print("\n[Gateway] Beendet")
            break
        except Exception as e:
            print(f"[Poll Error] {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(5)


def main():
    if not BOT_TOKEN:
        print("FEHLER: RINNSAL_TELEGRAM_TOKEN nicht gesetzt!", file=sys.stderr)
        print("  export RINNSAL_TELEGRAM_TOKEN='123456:ABC-DEF...'")
        sys.exit(1)

    if "--test" in sys.argv:
        result = tg_call("getMe")
        if result:
            print(f"Bot verbunden: @{result.get('username')} ({result.get('first_name')})")
        else:
            print("Verbindung fehlgeschlagen!")
        return

    if "--send" in sys.argv:
        idx = sys.argv.index("--send")
        if idx + 1 < len(sys.argv) and OWNER_CHAT_ID:
            send_message(OWNER_CHAT_ID, sys.argv[idx + 1])
            print("Gesendet.")
        else:
            print("Usage: --send 'Text' (TELEGRAM_OWNER_CHAT_ID muss gesetzt sein)")
        return

    # History-Dir sicherstellen
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    poll_loop()


if __name__ == "__main__":
    main()
