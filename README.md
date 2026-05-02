<div align="center">

# 💰 FinYaar
### *Smart Campus Finance Tracker*

![Platform](https://img.shields.io/badge/Platform-Web%20App-blueviolet?style=for-the-badge)
![Stack](https://img.shields.io/badge/Stack-Flask%20%2B%20Vanilla%20JS-orange?style=for-the-badge)
![Database](https://img.shields.io/badge/Database-SQLite-blue?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Llama%203.1%20%7C%20HuggingFace-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-Academic-red?style=for-the-badge)

**Group CSD138 | Banasthali Vidyapith**

*Empowering students to master their money — one smart decision at a time.*

---

</div>

## 📌 What is FinYaar?

**FinYaar** is a full-stack, web-based personal finance management platform built **exclusively** for students of **Banasthali Vidyapith**. It is designed with a single goal in mind — to make financial literacy accessible, engaging, and actionable for every student on campus.

From tracking daily chai expenses to simulating real stock market trades, FinYaar brings **professional-grade financial tools** into the hands of students — completely free, and without risking a single rupee.

> 🔒 **Campus-Only Access** — Only `@banasthali.in` email addresses can register, keeping the platform trusted and exclusive to our community.

---

## ✨ Feature Highlights

<table>
  <thead>
    <tr>
      <th>Module</th>
      <th>Feature</th>
      <th>What it does</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🔐 <b>Auth System</b></td>
      <td>OTP Verification</td>
      <td>Secure login & registration using OTP sent to college email</td>
    </tr>
    <tr>
      <td>💸 <b>Expense Tracker</b></td>
      <td>Full CRUD + Analytics</td>
      <td>Add, edit, delete expenses with category-wise visual breakdown</td>
    </tr>
    <tr>
      <td>🎯 <b>Savings Goals</b></td>
      <td>Goal Engine</td>
      <td>Set financial goals with deadlines, track progress, auto-archive on completion</td>
    </tr>
    <tr>
      <td>📈 <b>Paper Trading</b></td>
      <td>Stock Simulator</td>
      <td>Practice real NSE stock trading with ₹1,00,000 virtual cash — zero real risk</td>
    </tr>
    <tr>
      <td>🤖 <b>FinBot AI</b></td>
      <td>AI Finance Assistant</td>
      <td>Powered by Llama 3.1 (HuggingFace) with 50+ topic rule-based fallback</td>
    </tr>
    <tr>
      <td>🔔 <b>Notifications</b></td>
      <td>Smart Alerts</td>
      <td>Real-time alerts for budget limits, goal milestones, and trade confirmations</td>
    </tr>
    <tr>
      <td>📊 <b>Analytics</b></td>
      <td>Visual Reports</td>
      <td>Expense trend graphs + category-wise spending charts</td>
    </tr>
    <tr>
      <td>🔑 <b>Password Reset</b></td>
      <td>OTP-based Recovery</td>
      <td>Secure forgot-password flow via college email OTP</td>
    </tr>
  </tbody>
</table>

---

## 🛠️ Technology Stack

### 🐍 Backend

| Technology | Version | Role |
|---|---|---|
| **Python** | 3.8+ | Core language |
| **Flask** | Latest | Web framework & REST API |
| **Flask-SQLAlchemy** | Latest | ORM & database management |
| **Flask-JWT-Extended** | Latest | JWT-based authentication |
| **Flask-CORS** | Latest | Cross-origin request handling |
| **SQLite** | Built-in | Lightweight embedded database |
| **yfinance** | Latest | Real-time NSE/BSE stock price data |
| **smtplib / Gmail SMTP** | Built-in | OTP email delivery service |
| **Hugging Face Inference API** | Latest | AI chatbot (Llama 3.1 8B Instruct) |
| **python-dotenv** | Latest | Secure environment variable management |
| **Werkzeug** | Latest | Bcrypt password hashing |

### 🌐 Frontend

| Technology | Role |
|---|---|
| **HTML5** | Semantic structure & markup |
| **CSS3** | Modern styling, animations & responsiveness |
| **Vanilla JavaScript** | Dynamic logic & AJAX API calls |
| **Single Page Application (SPA)** | All UI delivered via `FinYaar_Final.html` |

---

## 📁 Project Structure

```
FinYaarProj/
│
├── 📄 FinYaar_Backend_app.py     ← Main Flask backend (all API routes & logic)
├── 🌐 FinYaar_Final.html         ← Complete frontend SPA (no build step needed)
├── 🗃️  FinYaar_DB_Schema.sql     ← SQLite database schema reference
├── 📦 requirements.txt           ← Python package dependencies
├── 🔒 .env                       ← Environment variables (⚠️ never commit this)
│
├── instance/
│   └── 💾 finyaar.db             ← Auto-generated SQLite database (on first run)
│
└── 🔧 Utility Scripts/
    ├── show_db.py                 ← Inspect DB tables visually
    ├── test_db.py                 ← Verify database connection
    ├── test_db_dump.py            ← Dump DB table contents for debugging
    ├── test_hf.py                 ← Test Hugging Face API connectivity
    ├── test_hf_fixed.py           ← Fixed HF API test variant
    └── test_hf_url.py             ← Test HF API URL resolution
```

---

## 🗄️ Database Schema

FinYaar uses **SQLite** with **8 relational tables**, designed for clarity and scalability:

```
┌─────────────────┬──────────────────────────────────────────────────┐
│   Table Name    │   Description                                    │
├─────────────────┼──────────────────────────────────────────────────┤
│ users           │ Student accounts, profile, and balance data      │
│ expenses        │ Daily expense entries per user                   │
│ savings_goals   │ Goal tracker with amount, deadline & progress    │
│ portfolios      │ Current stock holdings (paper trading)           │
│ stock_trades    │ Complete buy/sell trade history & P&L            │
│ notifications   │ Smart alerts for budget, goals & trades          │
│ finbot_logs     │ AI chatbot conversation history per user         │
│ password_resets │ OTP records for secure password recovery         │
└─────────────────┴──────────────────────────────────────────────────┘
```

---

## ⚙️ Setup & Installation

Follow these steps to get FinYaar running on your local machine.

### ✅ Prerequisites

Before starting, make sure you have:
- [ ] **Python 3.8+** installed — [Download here](https://www.python.org/downloads/)
- [ ] **pip** (comes with Python)
- [ ] A **Gmail account** with [App Password](https://myaccount.google.com/apppasswords) enabled (for OTP emails)
- [ ] *(Optional)* A **Hugging Face account** with an API token (for FinBot AI)

---

### Step 1 — Get the Project

```bash
# Option A: Clone via Git
git clone <repository-url>
cd FinYaarProj

# Option B: Download ZIP and extract it, then open the folder
```

---

### Step 2 — Create a Virtual Environment

```bash
# Create the virtual environment
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on Mac/Linux
source .venv/bin/activate
```

> ✅ Your terminal prompt should now show `(.venv)` — you're inside the virtual environment.

---

### Step 3 — Install All Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, JWT, yfinance, and all other required packages in one shot.

---

### Step 4 — Configure Environment Variables

Create a file named `.env` in the project root with the following contents:

```env
# ─── Gmail SMTP (Required for OTP emails) ───────────────────────────
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASS=your-16-character-app-password

# ─── Security Keys (Required) ────────────────────────────────────────
JWT_SECRET=choose-a-long-random-secret-key
FLASK_SECRET=another-long-random-secret-key

# ─── Hugging Face API (Optional — for FinBot AI) ─────────────────────
HF_API_KEY=hf_your_token_here
```

> 💡 **Getting your Gmail App Password:**  
> Go to your Google Account → Security → 2-Step Verification → App Passwords → Generate one for "Mail".

---

### Step 5 — Start the Backend Server

```bash
python FinYaar_Backend_app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Database initialized successfully
```

---

### Step 6 — Open the Frontend

Simply **open `FinYaar_Final.html` in your browser** — no build tools, no separate frontend server needed.

```
📂 FinYaarProj/
   └── 🌐 FinYaar_Final.html   ← Double-click or open in browser
```

> 🎉 **That's it!** FinYaar is now fully running on your machine.

---

## 🔗 REST API Reference

All API endpoints are prefixed with `/api/`. JWT token is required for protected routes.

### 🔐 Authentication — `/api/auth`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|---|
| `POST` | `/api/auth/register` | ❌ | Register new student (sends OTP) |
| `POST` | `/api/auth/verify-otp` | ❌ | Verify OTP to activate account |
| `POST` | `/api/auth/login` | ❌ | Login (triggers OTP to email) |
| `POST` | `/api/auth/forgot-password` | ❌ | Request password reset OTP |
| `POST` | `/api/auth/reset-password` | ❌ | Set new password with OTP |
| `PUT`  | `/api/auth/profile` | ✅ | Update user profile details |

### 💸 Expenses — `/api/expenses`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|---|
| `GET`    | `/api/expenses` | ✅ | Fetch all expenses (optional category filter) |
| `POST`   | `/api/expenses` | ✅ | Add a new expense entry |
| `PUT`    | `/api/expenses/<id>` | ✅ | Edit an existing expense |
| `DELETE` | `/api/expenses/<id>` | ✅ | Remove an expense |
| `GET`    | `/api/expenses/summary` | ✅ | Get total & category-wise summary |

### 🎯 Savings Goals — `/api/savings`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|---|
| `GET`    | `/api/savings` | ✅ | Get all savings goals |
| `POST`   | `/api/savings` | ✅ | Create a new savings goal |
| `PUT`    | `/api/savings/<id>/add` | ✅ | Add funds towards a goal |
| `DELETE` | `/api/savings/<id>` | ✅ | Delete a savings goal |

### 📈 Paper Trading — `/api/trading`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|---|
| `GET`  | `/api/trading/market` | ✅ | Fetch live NSE stock prices |
| `POST` | `/api/trading/buy` | ✅ | Execute a buy order |
| `POST` | `/api/trading/sell` | ✅ | Execute a sell order |
| `GET`  | `/api/trading/portfolio` | ✅ | View current holdings & cash balance |
| `GET`  | `/api/trading/history` | ✅ | View complete trade history & P&L |

### 🤖 FinBot AI — `/api/finbot`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|---|
| `POST` | `/api/finbot/chat` | ✅ | Send a message, receive AI response |

### 🔔 Notifications — `/api/notifications`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|---|
| `GET` | `/api/notifications` | ✅ | Retrieve all notifications for the user |
| `PUT` | `/api/notifications/read-all` | ✅ | Mark all notifications as read |

---

## 🤖 FinBot — AI Financial Assistant

FinBot is built on a **two-layer intelligence architecture** to ensure it always gives a helpful response:

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  Layer 1: Hugging Face Router API   │   ← Primary (uses Llama 3.1 8B Instruct)
│  (requires HF_API_KEY in .env)      │
└──────────────────┬──────────────────┘
                   │ (if API fails or no key)
                   ▼
┌─────────────────────────────────────┐
│  Layer 2: Rule-Based Fallback       │   ← 50+ topic categories
│  (works 100% offline)               │   ← SIP, taxes, budgeting, stocks...
└─────────────────────────────────────┘
```

**FinBot can help students with:**
- 📊 Investment basics — SIP, mutual funds, stocks, PPF
- 🧾 Tax-related queries — ITR, TDS, deductions
- 💳 Budgeting & expense management advice
- 🌍 General knowledge questions (like ChatGPT)
- 🗣️ Conversations in **English, Hindi & Hinglish**

---

## 📈 Paper Trading System — How It Works

Every new student gets **₹1,00,000 in virtual cash** to practice real stock trading — zero financial risk, maximum learning.

| Feature | Detail |
|---|---|
| **Starting Balance** | ₹1,00,000 virtual cash |
| **Supported Stocks** | RELIANCE, TCS, HDFCBANK, INFY, ITC, WIPRO, ONGC, SBIN, BAJFINANCE, ZOMATO |
| **Price Data** | Real-time NSE prices via `yfinance` |
| **Trading Hours** | 9:15 AM – 3:30 PM IST, Monday to Friday |
| **Trade Types** | Long (Buy) & Short (Sell) positions |
| **Educational Mode** | Post-trade explanations of profit/loss logic |

---

## 🔒 Security Architecture

FinYaar is built with security-first principles:

| Security Layer | Implementation |
|---|---|
| **Domain Restriction** | Only `@banasthali.in` emails can register |
| **Password Hashing** | Bcrypt hashing via Werkzeug — passwords never stored in plaintext |
| **JWT Authentication** | Access tokens with 24-hour expiry |
| **OTP Verification** | 2-step verification for login, registration & password reset |
| **OTP Expiry** | OTPs expire automatically after 10 minutes |
| **CORS Policy** | Configured for local-only access during development |

---

## 👥 Team

<div align="center">

### 🎓 Group CSD138
#### Banasthali Vidyapith

*This project was developed as part of an academic course assignment to design and implement a real-world, production-grade full-stack web application.*

---

*We built FinYaar with the vision of making every student financially aware, empowered, and responsible.*

</div>

---

## 📄 License

This project is developed for **academic purposes** at Banasthali Vidyapith.  
All rights reserved by **Group CSD138**.

> This software is intended for educational use only and is not meant for commercial deployment.

---

<div align="center">

**Made with ❤️ by Group CSD138 | Banasthali Vidyapith**

*"Financial freedom begins with financial knowledge."*

</div>
