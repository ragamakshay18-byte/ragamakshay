# 🤖 CodeRefine — AI Code Review & Rewrite Agent

An AI-powered web app that reviews and rewrites your code using **Groq + Llama 3.3 70B**.

---

## 📁 Project Structure

```
CodeReviewAI/
├── backend/
│   ├── main.py            ← FastAPI backend (all your API logic)
│   ├── requirements.txt   ← Python dependencies
│   └── .env               ← Your API key goes here (never share this!)
└── frontend/
    ├── login.html         ← Login page
    └── index.html         ← Main tool UI
```

---

## ⚡ Setup Instructions (Step by Step)

### Step 1 — Add your Groq API key

Open `backend/.env` and replace the placeholder:

```
GROQ_API_KEY=your_groq_api_key_here
```

➡️ Get your key at: https://console.groq.com/keys

---

### Step 2 — Create a virtual environment

Open a terminal, navigate to the `backend/` folder:

```bash
cd CodeReviewAI/backend

# Create virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Run the server

```bash
python main.py
```

You should see:
```
✅ Login Page : http://localhost:8000
✅ Tool Page  : http://localhost:8000/app
✅ API Docs   : http://localhost:8000/docs
```

---

### Step 5 — Open the app

Go to: **http://localhost:8000**

Login with demo credentials:
- **Email:** demo@coderefine.ai
- **Password:** password123

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔍 Code Review | Analyzes bugs, security, performance, best practices |
| 📊 Severity Tags | Critical / High / Medium / Low counts |
| ✏️ Auto-Rewrite | Generates clean, production-ready code |
| 🔀 Side-by-side | Original vs rewritten code comparison |
| 📋 Copy buttons | One-click copy for review & rewritten code |
| 🌐 Multi-language | Python, JS, TS, Java, C++, Go, Rust, and more |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| AI Model | Llama 3.3 70B via Groq API |
| Frontend | HTML5 + Tailwind CSS + JavaScript |
| Rendering | Marked.js (markdown) + Highlight.js (syntax) |

---

## ❓ Troubleshooting

**"API Error" in status badge** → Check your GROQ_API_KEY in `.env`

**Port already in use** → Change port in `main.py`: `uvicorn.run("main:app", port=8001, ...)`

**Module not found** → Make sure your venv is activated and you ran `pip install -r requirements.txt`
