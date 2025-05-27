from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import init_db, get_user_by_username, create_user, get_contacts, add_contact
import uvicorn
import datetime
import random
import sqlite3

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_db()

BOT_NAMES = ["EchoBot", "TimeBot", "JokeBot"]
BOT_JOKES = [
    "Чому програмісти не ходять в ліс? — Бо бояться багів!",
    "Як називається улюблена команда хакера? — Ctrl+Alt+Del.",
    "Що сказав Python, коли його спитали про Java? — 'Who?'",
    "Яка улюблена страва ботів? — Мікросхеми з чіпсами!"
]

# Створюємо ботів при старті, якщо їх ще немає
for bot in BOT_NAMES:
    create_user(bot)

active_connections = {}

def get_all_users_except_self(current_username):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    # Отримуємо всіх користувачів, крім поточного і ботів
    placeholders = ', '.join('?' * len(BOT_NAMES))
    query = f"SELECT username FROM users WHERE username != ? AND username NOT IN ({placeholders})"
    cursor.execute(query, (current_username, *BOT_NAMES))
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": "",  # Порожній рядок для імені користувача на сторінці входу
        "contacts": []   # Порожній список для контактів на сторінці входу
    })

@app.post("/login")
async def login(username: str = Form(...)):
    user = get_user_by_username(username)
    if not user:
        create_user(username)
    response = RedirectResponse(f"/chat/{username}", status_code=302)
    return response

@app.get("/chat/{username}", response_class=HTMLResponse)
async def chat_interface(request: Request, username: str):
    if not get_user_by_username(username):
        create_user(username)

    user_contacts = get_contacts(username)

    for bot in BOT_NAMES:
        if bot not in user_contacts:
            add_contact(username, bot)
            user_contacts.append(bot)

    all_other_users = get_all_users_except_self(username)

    display_contacts = sorted(list(set(user_contacts + all_other_users)))

    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": username,
        "contacts": display_contacts
    })

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    print(f"DEBUG: Користувач {username} підключився до WebSocket.")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"DEBUG: Отримано від {username}: {data}")

            if ":" not in data:
                print(f"ERROR: Некоректний формат повідомлення від {username}: {data}")
                await websocket.send_text("Система: Некоректний формат повідомлення. Будь ласка, оберіть контакт і введіть повідомлення.")
                continue

            target, message = data.split(":", 1)
            target = target.strip()
            message = message.strip()

            if target in BOT_NAMES:
                print(f"DEBUG: Обробка повідомлення для бота: {target}, Повідомлення: '{message}'")
                reply = generate_bot_reply(target, message, username)
                print(f"DEBUG: Відповідь від {target}: {reply}")
                await websocket.send_text(f"{target}: {reply}")
            elif target in active_connections:
                print(f"DEBUG: Надсилання повідомлення від {username} до {target}: '{message}'")
                await active_connections[target].send_text(f"{username}: {message}")
            else:
                print(f"DEBUG: Користувач {target} не в мережі.")
                await websocket.send_text(f"Система: Користувач '{target}' зараз не в мережі або не знайдений.")
    except WebSocketDisconnect:
        print(f"INFO: Користувач {username} відключився від WebSocket.")
        if username in active_connections:
            del active_connections[username]
    except Exception as e:
        print(f"ERROR: Помилка WebSocket для {username}: {e}")
        import traceback
        traceback.print_exc() # Друкуємо повний стек помилок
        await websocket.send_text(f"Система: Виникла помилка: {e}")

def generate_bot_reply(bot_name, message, sender):
    if bot_name == "EchoBot":
        return f"Ти сказав: {message}"
    elif bot_name == "TimeBot":
        kyiv_time = datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=3)))
        return f"Зараз {kyiv_time.strftime('%H:%M:%S')} (Київський час)."
    elif bot_name == "JokeBot":
        message_lower = message.lower()
        if "розкажи" in message_lower or "жарт" in message_lower or "joke" in message_lower or "розкажи жарт" in message_lower:
            return random.choice(BOT_JOKES)
        elif "привіт" in message_lower or "добрий день" in message_lower or "hello" in message_lower or "hi" in message_lower:
            return "Привіт! Хочеш жарт?"
        elif "як справи" in message_lower or "як ти" in message_lower:
            return "Я робот, у мене завжди все чудово! Хочеш жарт, щоб і тобі було весело?"
        else:
            return "Я жартівливий бот. Якщо хочеш почути жарт, просто скажи 'розкажи жарт'!"
    return "Я бот і не розумію тебе."

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)