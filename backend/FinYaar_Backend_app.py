"""
FinYaar – Smart Campus Finance Tracker
Backend: Python Flask + SQLite
Group CSD138 | Banasthali Vidyapith

"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib, random, string, os, threading, time, requests as http_req
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date
import yfinance as yf
from dotenv import load_dotenv
load_dotenv()

# ──────────────────────────────────────
# APP CONFIG
# ──────────────────────────────────────
app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config.update(
    SQLALCHEMY_DATABASE_URI = 'sqlite:///finyaar.db',
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'finyaar-secret-csd138'),
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24),
    SECRET_KEY = os.getenv('FLASK_SECRET', 'flask-secret-key'),
)

db  = SQLAlchemy(app)
jwt = JWTManager(app)

ALLOWED_DOMAIN = 'banasthali.in'
GMAIL_USER     = os.getenv('GMAIL_USER', 'finyaar.official@gmail.com')
GMAIL_PASS     = os.getenv('GMAIL_APP_PASS', 'owwonvcnjfagmcph')
HF_API_KEY     = os.getenv('HF_API_KEY', '')   # <-- Hugging Face token

otp_store = {}   # { email: { otp, expires_at } }

# ──────────────────────────────────────
# DATABASE MODELS
# ──────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    user_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    student_id = db.Column(db.String(50),  nullable=False)
    course     = db.Column(db.String(80),  nullable=False)
    year       = db.Column(db.String(20),  nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20),  default='student')
    budget          = db.Column(db.Float,   default=55000.0)
    paper_cash      = db.Column(db.Float,   default=100000.0)
    last_reset_date = db.Column(db.Date,    nullable=True)
    is_verified     = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)


class Expense(db.Model):
    __tablename__ = 'expenses'
    expense_id  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    category    = db.Column(db.String(50), nullable=False)
    date        = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes       = db.Column(db.Text, default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'
    goal_id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name           = db.Column(db.String(100), nullable=False)
    icon           = db.Column(db.String(10),  default='✈️')
    target_amount  = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    deadline       = db.Column(db.Date, nullable=False)
    is_done        = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    portfolio_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    stock_symbol = db.Column(db.String(20), nullable=False)
    quantity     = db.Column(db.Integer, default=0)
    avg_price    = db.Column(db.Float, nullable=False)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockTrade(db.Model):
    __tablename__ = 'stock_trades'
    trade_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    stock_symbol = db.Column(db.String(20), nullable=False)
    trade_type   = db.Column(db.String(10), nullable=False)
    quantity     = db.Column(db.Integer, nullable=False)
    price        = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    traded_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    notif_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(30), default='info')
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FinBotLog(db.Model):
    __tablename__ = 'finbot_logs'
    log_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    query      = db.Column(db.Text, nullable=False)
    response   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email      = db.Column(db.String(150), nullable=False)
    otp        = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)

# ──────────────────────────────────────
# HELPERS
# ──────────────────────────────────────

def is_banasthali(email: str) -> bool:
    return email.strip().lower().endswith(f'@{ALLOWED_DOMAIN}')

def gen_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def send_email(to: str, subject: str, html: str):
    if not GMAIL_PASS:
        print("⚠️ [FinYaar] GMAIL_APP_PASS is empty. Skipping email delivery.")
        return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'FinYaar <{GMAIL_USER}>'
    msg['To'] = to
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, to, msg.as_string())
    except Exception as e:
        print(f"⚠️ [FinYaar] SMTP Error: {e}. Email not sent.")

def otp_email_html(otp: str, purpose: str) -> str:
    return f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;border:4px solid #000;border-radius:24px">
      <h1 style="font-size:48px;font-weight:900;font-style:italic;margin:0">FinYaar</h1>
      <p style="font-weight:700;opacity:.5;text-transform:uppercase;font-size:12px;letter-spacing:2px">Banasthali Vidyapith</p>
      <hr style="border:3px solid #000;margin:24px 0">
      <p style="font-size:16px;font-weight:700">Your OTP for <b>{purpose}</b>:</p>
      <div style="font-size:48px;font-weight:900;letter-spacing:14px;background:#FFED94;border:3px solid #000;border-radius:16px;padding:20px;text-align:center;margin:20px 0">{otp}</div>
      <p style="font-size:13px;opacity:.5;font-weight:700">Valid for 10 minutes. Do not share this with anyone.</p>
    </div>"""

def push_notif(user_id: int, message: str, ntype: str = 'info'):
    db.session.add(Notification(user_id=user_id, message=message, type=ntype))
    db.session.commit()

# ──────────────────────────────────────
# AUTH ROUTES  /api/auth
# ──────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email','').strip().lower()
    if not is_banasthali(email):
        return jsonify(error='Only @banasthali.in email addresses are allowed'), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error='Email already registered'), 409

    otp = gen_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)
    otp_store[email] = {'otp': otp, 'expires_at': expires, 'data': data, 'type': 'register'}
    try:
        print(f"🔑 [FinYaar Auth] Registration OTP for {email}: {otp}")
        send_email(email, 'FinYaar – Verify Your Email', otp_email_html(otp,'Registration'))
    except Exception as e:
        return jsonify(error=f'Email send failed: {str(e)}'), 500
    return jsonify(message='OTP sent to your email'), 200


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data  = request.json
    email = data.get('email','').strip().lower()
    otp   = data.get('otp','').strip()
    entry = otp_store.get(email)
    if not entry:
        return jsonify(error='OTP session not found. Please try again'), 400
    if datetime.utcnow() > entry['expires_at']:
        return jsonify(error='OTP expired. Please try again'), 400
    if entry['otp'] != otp:
        return jsonify(error='Invalid OTP'), 400

    auth_type = entry.get('type', 'register')
    if auth_type == 'register':
        d = entry['data']
        user = User(
            name       = d.get('name','').strip(),
            email      = email,
            student_id = d.get('student_id','').strip().upper(),
            course     = d.get('course',''),
            year       = d.get('year',''),
            password   = generate_password_hash(d.get('password','')),
            budget     = float(d.get('budget', 55000)),
            is_verified= True,
        )
        db.session.add(user)
        db.session.commit()
    else:
        user = User.query.filter_by(email=email).first()
    del otp_store[email]
    token = create_access_token(identity=str(user.user_id))
    return jsonify(token=token, user=_user_dict(user)), 200


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email','').strip().lower()
    if not is_banasthali(email):
        return jsonify(error='Only @banasthali.in email addresses are allowed'), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, data.get('password','')):
        return jsonify(error='Invalid credentials'), 401
    if not user.is_verified:
        return jsonify(error='Email not verified. Please check your inbox'), 403
    otp = gen_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)
    otp_store[email] = {'otp': otp, 'expires_at': expires, 'type': 'login'}
    try:
        print(f"🔑 [FinYaar Auth] Login OTP for {email}: {otp}")
        send_email(email, 'FinYaar – Login OTP', otp_email_html(otp,'Login'))
    except Exception as e:
        return jsonify(error=f'Email send failed: {str(e)}'), 500
    return jsonify(message='OTP sent to your email'), 200


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email','').strip().lower()
    if not is_banasthali(email):
        return jsonify(error='Only @banasthali.in emails are allowed'), 400
    if not User.query.filter_by(email=email).first():
        return jsonify(error='Email not registered'), 404
    otp = gen_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.add(PasswordReset(email=email, otp=otp, expires_at=expires))
    db.session.commit()
    try:
        print(f"🔑 [FinYaar Auth] Password Reset OTP for {email}: {otp}")
        send_email(email, 'FinYaar – Reset Your Password', otp_email_html(otp,'Password Reset'))
    except Exception as e:
        return jsonify(error=f'Email send failed: {str(e)}'), 500
    return jsonify(message='OTP sent to your email'), 200


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data  = request.json
    email = data.get('email','').strip().lower()
    otp   = data.get('otp','').strip()
    new_p = data.get('new_password','')
    record = PasswordReset.query.filter_by(email=email, otp=otp, used=False)\
               .order_by(PasswordReset.id.desc()).first()
    if not record:
        return jsonify(error='Invalid OTP'), 400
    if datetime.utcnow() > record.expires_at:
        return jsonify(error='OTP expired'), 400
    user = User.query.filter_by(email=email).first()
    user.password = generate_password_hash(new_p)
    record.used = True
    db.session.commit()
    return jsonify(message='Password reset successful'), 200


@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user = User.query.get(get_jwt_identity())
    d = request.json
    if 'name'       in d: user.name       = d['name']
    if 'course'     in d: user.course     = d['course']
    if 'sid'        in d: user.student_id = d['sid']
    if 'student_id' in d: user.student_id = d['student_id']
    if 'budget'     in d: user.budget     = float(d['budget'])
    db.session.commit()
    return jsonify(user=_user_dict(user))


def _user_dict(u):
    return { 'user_id':u.user_id, 'name':u.name, 'email':u.email,
             'sid':u.student_id, 'course':u.course, 'year':u.year,
             'budget':u.budget, 'paper_cash':u.paper_cash }

# ──────────────────────────────────────
# EXPENSE ROUTES  /api/expenses
# ──────────────────────────────────────

@app.route('/api/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    uid = get_jwt_identity()
    cat = request.args.get('category')
    q = Expense.query.filter_by(user_id=uid)
    if cat: q = q.filter_by(category=cat)
    expenses = q.order_by(Expense.date.desc()).all()
    return jsonify(expenses=[_exp_dict(e) for e in expenses])


@app.route('/api/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    uid = get_jwt_identity()
    d   = request.json
    amt = float(d.get('amount',0))
    if amt <= 0:
        return jsonify(error='Amount must be positive'), 400
    exp = Expense(
        user_id  = uid,
        title    = d.get('title','').strip(),
        amount   = amt,
        category = d.get('category','Other'),
        date     = datetime.strptime(d.get('date', str(datetime.utcnow().date())), '%Y-%m-%d').date(),
        notes    = d.get('notes','')
    )
    db.session.add(exp)
    user = User.query.get(uid)
    total_spend = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=uid).scalar() or 0
    if (total_spend + amt) / user.budget >= 0.85:
        push_notif(uid, '⚠️ Budget Alert: You have used over 85% of your monthly budget!', 'budget_alert')
    db.session.commit()
    return jsonify(expense=_exp_dict(exp)), 201


@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def edit_expense(expense_id):
    uid = get_jwt_identity()
    exp = Expense.query.filter_by(expense_id=expense_id, user_id=uid).first_or_404()
    d   = request.json
    for field in ['title','amount','category','notes']:
        if field in d: setattr(exp, field, d[field])
    if 'date' in d:
        exp.date = datetime.strptime(d['date'],'%Y-%m-%d').date()
    db.session.commit()
    return jsonify(expense=_exp_dict(exp))


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    uid = get_jwt_identity()
    exp = Expense.query.filter_by(expense_id=expense_id, user_id=uid).first_or_404()
    db.session.delete(exp)
    db.session.commit()
    return jsonify(message='Deleted'), 200


@app.route('/api/expenses/summary', methods=['GET'])
@jwt_required()
def expense_summary():
    uid = get_jwt_identity()
    expenses = Expense.query.filter_by(user_id=uid).all()
    total = sum(e.amount for e in expenses)
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
    return jsonify(total=total, by_category=by_cat)


def _exp_dict(e):
    return { 'expense_id':e.expense_id, 'title':e.title, 'amount':e.amount,
             'category':e.category, 'date':str(e.date), 'notes':e.notes }

# ──────────────────────────────────────
# SAVINGS ROUTES  /api/savings
# ──────────────────────────────────────

@app.route('/api/savings', methods=['GET'])
@jwt_required()
def get_goals():
    uid   = get_jwt_identity()
    goals = SavingsGoal.query.filter_by(user_id=uid).order_by(SavingsGoal.created_at.desc()).all()
    return jsonify(goals=[_goal_dict(g) for g in goals])


@app.route('/api/savings', methods=['POST'])
@jwt_required()
def add_goal():
    uid = get_jwt_identity()
    d   = request.json
    goal = SavingsGoal(
        user_id       = uid,
        name          = d.get('name','').strip(),
        icon          = d.get('icon','✈️'),
        target_amount = float(d.get('target_amount',0)),
        deadline      = datetime.strptime(d['deadline'],'%Y-%m-%d').date()
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify(goal=_goal_dict(goal)), 201


@app.route('/api/savings/<int:goal_id>/add', methods=['PUT'])
@jwt_required()
def add_to_goal(goal_id):
    uid  = get_jwt_identity()
    goal = SavingsGoal.query.filter_by(goal_id=goal_id, user_id=uid).first_or_404()
    amt  = float(request.json.get('amount', 0))
    goal.current_amount = min(goal.current_amount + amt, goal.target_amount)
    if goal.current_amount >= goal.target_amount:
        goal.is_done = True
        push_notif(uid, f'🎉 Goal Achieved: {goal.name}! Congratulations!', 'goal')
    db.session.commit()
    return jsonify(goal=_goal_dict(goal))


@app.route('/api/savings/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    uid  = get_jwt_identity()
    goal = SavingsGoal.query.filter_by(goal_id=goal_id, user_id=uid).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return jsonify(message='Goal deleted'), 200


def _goal_dict(g):
    return { 'goal_id':g.goal_id, 'name':g.name, 'icon':g.icon,
             'target_amount':g.target_amount, 'current_amount':g.current_amount,
             'deadline':str(g.deadline), 'is_done':g.is_done,
             'progress_pct': round((g.current_amount/g.target_amount)*100, 1) if g.target_amount else 0 }

# ──────────────────────────────────────
# TRADING ROUTES  /api/trading
# ──────────────────────────────────────

NSE_SYMBOLS = ['RELIANCE.NS','TCS.NS','HDFCBANK.NS','INFY.NS','ITC.NS','WIPRO.NS','ONGC.NS','SBIN.NS','BAJFINANCE.NS','ZOMATO.NS']

@app.route('/api/trading/market', methods=['GET'])
@jwt_required()
def market_data():
    result = []
    for sym in NSE_SYMBOLS:
        try:
            t = yf.Ticker(sym)
            h = t.history(period='2d')
            if h.empty: continue
            price = round(float(h['Close'].iloc[-1]), 2)
            prev  = round(float(h['Close'].iloc[-2]), 2) if len(h)>1 else price
            change     = round(price - prev, 2)
            change_pct = round((change/prev)*100, 2) if prev else 0
            result.append({'symbol':sym.replace('.NS',''), 'price':price, 'change':change, 'change_pct':change_pct})
        except: pass
    return jsonify(market=result)


@app.route('/api/trading/buy', methods=['POST'])
@jwt_required()
def buy_stock():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    d    = request.json
    sym  = d.get('symbol','').upper().strip()
    qty  = int(d.get('quantity',0))
    price= float(d.get('price',0))
    total= qty * price
    if qty <= 0 or price <= 0:
        return jsonify(error='Invalid quantity or price'), 400
    if total > user.paper_cash:
        return jsonify(error='Insufficient paper cash'), 400
    user.paper_cash -= total
    port = Portfolio.query.filter_by(user_id=uid, stock_symbol=sym).first()
    if port:
        port.avg_price = (port.avg_price * port.quantity + price * qty) / (port.quantity + qty)
        port.quantity += qty
    else:
        db.session.add(Portfolio(user_id=uid, stock_symbol=sym, quantity=qty, avg_price=price))
    db.session.add(StockTrade(user_id=uid, stock_symbol=sym, trade_type='BUY',
                               quantity=qty, price=price, total_amount=total))
    push_notif(uid, f'✅ Bought {qty}×{sym} @ ₹{price:.2f}', 'trade')
    db.session.commit()
    return jsonify(message='Buy order executed', paper_cash=user.paper_cash), 200


@app.route('/api/trading/sell', methods=['POST'])
@jwt_required()
def sell_stock():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    d    = request.json
    sym  = d.get('symbol','').upper().strip()
    qty  = int(d.get('quantity',0))
    price= float(d.get('price',0))
    total= qty * price
    port = Portfolio.query.filter_by(user_id=uid, stock_symbol=sym).first()
    if not port or port.quantity < qty:
        return jsonify(error='Insufficient shares'), 400
    user.paper_cash += total
    port.quantity   -= qty
    if port.quantity == 0:
        db.session.delete(port)
    db.session.add(StockTrade(user_id=uid, stock_symbol=sym, trade_type='SELL',
                               quantity=qty, price=price, total_amount=total))
    push_notif(uid, f'✅ Sold {qty}×{sym} @ ₹{price:.2f}', 'trade')
    db.session.commit()
    return jsonify(message='Sell order executed', paper_cash=user.paper_cash), 200


@app.route('/api/trading/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    uid       = get_jwt_identity()
    holdings  = Portfolio.query.filter_by(user_id=uid).all()
    user      = User.query.get(uid)
    return jsonify(paper_cash=user.paper_cash,
                   holdings=[{ 'symbol':h.stock_symbol, 'quantity':h.quantity, 'avg_price':h.avg_price } for h in holdings])


@app.route('/api/trading/history', methods=['GET'])
@jwt_required()
def trade_history():
    uid    = get_jwt_identity()
    trades = StockTrade.query.filter_by(user_id=uid).order_by(StockTrade.traded_at.desc()).all()
    return jsonify(trades=[{ 'symbol':t.stock_symbol, 'type':t.trade_type, 'qty':t.quantity,
                              'price':t.price, 'total':t.total_amount, 'at':str(t.traded_at) } for t in trades])

# ══════════════════════════════════════════════════════════════
# FINBOT  /api/finbot/chat
# Primary  : Hugging Face Router API (Mistral-7B-Instruct-v0.2)
# Fallback : Comprehensive rule-based engine (200+ topics)
# Language : English | Hindi | Hinglish
# ══════════════════════════════════════════════════════════════

HF_MODEL   = "meta-llama/Llama-3.1-8B-Instruct"
# ✅ FIXED URL — OpenAI-compatible router endpoint
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

FINBOT_SYSTEM = """You are FinBot, an intelligent and versatile AI Assistant built for college students at Banasthali Vidyapith on the FinYaar platform.

STRICT RULES:
1. ALWAYS reply entirely in English. Even if the user asks a question in Hindi or Hinglish, you MUST answer in English. Do not use Hindi/Hinglish words.
2. You are a general-purpose AI designed to answer ANY question, just like ChatGPT or Gemini. You can help with general knowledge, coding, history, daily life, exams, and any other topic. You are NOT restricted to finance.
3. Be friendly, warm, and helpful. Use emojis occasionally.
4. Keep your answers clear, concise, and structured.
5. If the user asks about Indian finance, use ₹ for currency amounts and provide accurate, actionable advice.

INDIAN FINANCE QUICK REFERENCE (Use only if relevant):
- SIP: Rupee cost averaging, compounding power
- Mutual Funds: Equity, Debt, Hybrid, Index Funds
- NSE/BSE: NIFTY 50, SENSEX
- Tax: Income tax slabs, 80C, GST basics
- Savings: FD, PPF, RD, NPS
- Rule 50/30/20: 50% needs, 30% wants, 20% savings
"""


def _call_huggingface(user_query: str, system_context: str) -> str | None:
    """
    Call HF Router API — OpenAI-compatible chat completions endpoint.
    Returns the reply string or None on any failure.
    """
    if not HF_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": system_context},
            {"role": "user",   "content": user_query}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False
    }

    for attempt in range(2):
        try:
            resp = http_req.post(HF_API_URL, headers=headers, json=payload, timeout=35)
            print(f"[FinBot HF] status={resp.status_code} attempt={attempt+1}")

            if resp.status_code == 200:
                data = resp.json()
                # ✅ OpenAI-compatible response format
                if isinstance(data, dict):
                    choices = data.get('choices', [])
                    if choices:
                        return choices[0].get('message', {}).get('content', '').strip()
                # Fallback: old inference API list format
                if isinstance(data, list) and data:
                    return data[0].get('generated_text', '').strip()
                return None

            elif resp.status_code == 503:
                print(f"⏳ [FinBot] HF model loading, retrying in 15s...")
                time.sleep(15)
                continue

            elif resp.status_code in (401, 403):
                print(f"❌ [FinBot] HF auth error {resp.status_code}")
                return None

            else:
                print(f"❌ [FinBot] HF error {resp.status_code}: {resp.text[:300]}")
                return None

        except Exception as e:
            print(f"❌ [FinBot] HF exception: {e}")
            return None

    return None


def _smart_fallback(query: str, user: object, total_sp: float, goals: list) -> str:
    """
    Comprehensive rule-based FinBot — handles 50+ topic categories.
    Works for ANY question — finance, general, and everything in between.
    English + Hindi + Hinglish support.
    """
    q = query.lower().strip()

    # ════════════════════════════════════════════
    # GREETINGS & META
    # ════════════════════════════════════════════
    if any(k in q for k in ['hello', 'hi', 'hey', 'helo', 'namaste', 'नमस्ते', 'hii', 'sup', 'kya haal', 'kaisa hai']):
        return (
            f"Hello {user.name}! 👋 I am **FinBot** — your intelligent AI Assistant!\n\n"
            f"Your current budget is ₹{user.budget:,.0f}/month and you have spent ₹{total_sp:,.0f} so far.\n\n"
            "Ask me anything — coding, history, science, SIP, stocks, budgeting, tax, or any general question. I'm here to help! 😊"
        )

    if any(k in q for k in ['who are you', 'kaun ho', 'kya ho tum', 'about you', 'tumhare baare']):
        return (
            "🤖 I am **FinBot** — FinYaar's AI Assistant!\n\n"
            "I am designed to help Banasthali Vidyapith students with everything they need!\n\n"
            "**I can help you with:**\n"
            "• Any general knowledge, exam prep, or coding questions like ChatGPT\n"
            "• SIP, Mutual Funds, Stocks and Investments\n"
            "• Budget planning and expense management\n"
            "• Income Tax, GST basics\n"
            "• Savings goals and emergency funds\n\n"
            "Ask me anything! 💪"
        )

    if any(k in q for k in ['thank', 'thanks', 'shukriya', 'dhanyawad', 'धन्यवाद', 'thx', 'ty']):
        return f"You're very welcome, {user.name}! 😊 Let me know if you have any other questions. FinBot is always here to help! 🚀"

    # ════════════════════════════════════════════
    # USER'S OWN DATA QUESTIONS
    # ════════════════════════════════════════════
    if any(k in q for k in ['mera budget', 'my budget', 'kitna kharch', 'how much spent', 'mera kharch', 'mere goals']):
        remaining = user.budget - total_sp
        pct = (total_sp / user.budget * 100) if user.budget else 0
        status = "⚠️ Careful!" if pct > 85 else ("✅ On track!" if pct < 60 else "🟡 Moderate spending")
        return (
            f"📊 **{user.name} ka Financial Summary:**\n\n"
            f"• Monthly Budget: ₹{user.budget:,.0f}\n"
            f"• Total Spent: ₹{total_sp:,.0f} ({pct:.1f}%)\n"
            f"• Remaining: ₹{remaining:,.0f}\n"
            f"• Status: {status}\n"
            f"• Active Goals: {len(goals)}\n"
            f"• Paper Cash (Trading): ₹{user.paper_cash:,.0f}\n\n"
            "Expenses tab mein detailed breakdown dekho! 📈"
        )

    # ════════════════════════════════════════════
    # SIP & MUTUAL FUNDS
    # ════════════════════════════════════════════
    if any(k in q for k in ['sip', 'systematic investment', 'म्यूचुअल फंड', 'mutual fund', 'elss', 'nav', 'amc', 'folio', 'groww', 'zerodha coin']):
        return (
            "📈 **SIP (Systematic Investment Plan) — Student Guide:**\n\n"
            "**SIP kya hai?** Har month ek fixed amount automatically mutual fund mein invest hota hai.\n\n"
            "**Kyun karein?**\n"
            "• Rupee Cost Averaging — market upar ya neeche, average cost smooth hoti hai\n"
            "• Compounding — time ke saath returns pe returns milte hain\n"
            "• Minimum ₹500/month se shuru kar sakte ho\n\n"
            "**Student ke liye best SIP options:**\n"
            "• Nifty 50 Index Fund (safest, market returns)\n"
            "• Large Cap Fund (stable growth)\n"
            "• ELSS Fund (tax saving + good returns)\n\n"
            "**Calculator:** ₹1,000/month × 10 years @ 12% = ~₹2.3 lakh 🎉\n\n"
            "**Kahan shuru karein:** Groww / Zerodha Coin / Paytm Money app 📱"
        )

    if any(k in q for k in ['index fund', 'nifty etf', 'passive fund', 'nifty 50 fund']):
        return (
            "📊 **Index Funds — Beginner ka Best Friend!**\n\n"
            "Index Fund directly NIFTY 50 ya SENSEX track karta hai — koi fund manager nahi, low expense ratio (~0.1%).\n\n"
            "**Kyun best hai beginners ke liye?**\n"
            "• Active funds se zyada consistent performance\n"
            "• Low cost (expense ratio 0.05-0.2%)\n"
            "• Diversified (50 companies mein automatic)\n"
            "• No human bias\n\n"
            "**Popular options:** UTI Nifty 50, Nippon India Nifty BeES ETF, HDFC Index Fund\n\n"
            "**Rule:** Agar active fund selection nahi aata — index fund daalo aur bhool jao! 🏆"
        )

    # ════════════════════════════════════════════
    # STOCKS & TRADING
    # ════════════════════════════════════════════
    if any(k in q for k in ['stock', 'share', 'equity', 'शेयर', 'demat', 'ipo', 'reliance', 'tcs', 'infosys', 'zomato', 'nse', 'bse', 'trading', 'swing trade', 'intraday', 'technical analysis']):
        return (
            "📊 **Stock Market Guide for Students:**\n\n"
            "**Basics:**\n"
            "• Stock = company mein ownership ka ek chota hissa\n"
            "• NSE (NIFTY 50) aur BSE (SENSEX) — India ke 2 main exchanges\n"
            "• Demat account chahiye stocks khareedne ke liye (Zerodha/Groww/Upstox)\n\n"
            "**Top NSE Stocks:** RELIANCE, TCS, HDFCBANK, INFY, WIPRO, ITC, SBIN, BAJFINANCE, ZOMATO\n\n"
            "**Trading Types:**\n"
            "• Intraday — same day buy-sell (risky!)\n"
            "• Swing — few days to weeks\n"
            "• Long-term — years (safest for students)\n\n"
            "**Student Tip:** FinYaar ke Paper Trading se pehle practice karo — ₹1 lakh virtual cash! Real money tabhi lagao jab confident ho. 🎯\n\n"
            "Warren Buffett rule: *Never invest money you can't afford to lose.*"
        )

    if any(k in q for k in ['nifty', 'sensex', 'market today', 'market kya kar raha', 'aaj market']):
        return (
            "📈 **Nifty & Sensex — Quick Guide:**\n\n"
            "• **NIFTY 50** = NSE ke top 50 companies ka index. India ki economy ka barometer.\n"
            "• **SENSEX** = BSE ke top 30 companies ka index.\n\n"
            "**NIFTY Sectors:** IT, Banking, FMCG, Pharma, Auto, Energy, Metals\n\n"
            "**Market Timings:** 9:15 AM – 3:30 PM (Monday to Friday)\n\n"
            "**Real-time data ke liye:** NSE India app, Moneycontrol, TradingView dekho.\n\n"
            "FinYaar ke Trading tab mein bhi live market data milta hai! 🚀"
        )

    if any(k in q for k in ['ipo', 'initial public offering', 'new listing']):
        return (
            "🆕 **IPO (Initial Public Offering) Kya Hai?**\n\n"
            "Jab koi company pehli baar public mein apne shares bechti hai — iska naam hai IPO!\n\n"
            "**IPO mein kaise invest karein?**\n"
            "1. Demat + trading account chahiye\n"
            "2. UPI se bidding karein ASBA process ke through\n"
            "3. Allotment lucky draw jaise hoti hai — guaranteed nahi\n\n"
            "**Risks:** Listing pe loss bhi ho sakta hai (Paytm IPO example)\n"
            "**Reward:** Good IPOs listing pe 20-50% gain deti hain\n\n"
            "**Student advice:** Pehle company ke fundamentals padho, tab invest karo. Hype mein mat aao! 🧠"
        )

    # ════════════════════════════════════════════
    # BUDGETING & EXPENSES
    # ════════════════════════════════════════════
    if any(k in q for k in ['budget', 'kharcha', 'expense', 'kharch', 'spend', 'खर्च', 'बजट', 'paisa manage', 'money manage', 'paisa khatam', 'money finish', 'mahine ke ant']):
        remaining = user.budget - total_sp
        pct = (total_sp / user.budget * 100) if user.budget else 0
        tip = ""
        if pct > 85:
            tip = f"\n\n⚠️ **Alert:** Tumne budget ka {pct:.0f}% use kar liya hai! Spending slow karo."
        return (
            f"💰 **Budget Management — {user.name} ke liye:**\n\n"
            "**50/30/20 Rule (Best for Students):**\n"
            f"• 50% Needs = ₹{user.budget*0.5:,.0f} (mess, books, transport)\n"
            f"• 30% Wants = ₹{user.budget*0.3:,.0f} (canteen, outings, shopping)\n"
            f"• 20% Savings = ₹{user.budget*0.2:,.0f} (invest karo ya emergency fund)\n\n"
            f"**Tumhari current status:** ₹{total_sp:,.0f} / ₹{user.budget:,.0f} spent ({pct:.0f}%)\n"
            f"**Bacha hua:** ₹{remaining:,.0f}{tip}\n\n"
            "**Pro tip:** FinYaar pe har expense add karo — month end mein automatically analysis milegi! 📊"
        )

    # ════════════════════════════════════════════
    # SAVINGS & GOALS
    # ════════════════════════════════════════════
    if any(k in q for k in ['saving', 'bachat', 'बचत', 'save money', 'paisa bachao', 'emergency fund', 'rainy day', 'goal', 'target']):
        return (
            "🎯 **Smart Saving Strategy for Students:**\n\n"
            "**Rule #1: Pay yourself first**\n"
            "Stipend/pocket money milte hi 20% nikaal lo — pehle save, baad mein spend.\n\n"
            "**Emergency Fund (Must Have!):**\n"
            "• 3-6 months ke expenses liquid rakhna zaroori hai\n"
            "• Target: ₹15,000 – ₹30,000 for students\n"
            "• Liquid Mutual Fund ya Savings Account mein rakhna\n\n"
            "**Goal-based Saving (FinYaar mein set karo!):**\n"
            "• Laptop chahiye ₹60,000 ka? → ₹5,000/month × 12 months\n"
            "• Trip chahiye? → Goal banao, deadline set karo, track karo\n\n"
            "**Savings options for students:**\n"
            "• Liquid Fund: 6-7% p.a., anytime withdraw ✅\n"
            "• RD: Monthly ₹500 se, bank mein safe\n"
            "• FD: ₹10,000 lump sum ke liye\n\n"
            "Chote chote amounts bhi hote hain bade sapne! 💪"
        )

    # ════════════════════════════════════════════
    # TAX
    # ════════════════════════════════════════════
    if any(k in q for k in ['income tax', 'itr', 'tax return', 'tax filing', 'form 16', 'tds', '80c', '80d', 'टैक्स', 'tax bachao', 'tax save']):
        return (
            "🧾 **Income Tax Guide for Students:**\n\n"
            "**Tax Slabs (Old Regime FY 2024-25):**\n"
            "• Up to ₹2.5 lakh → Nil (0%)\n"
            "• ₹2.5L – ₹5L → 5%\n"
            "• ₹5L – ₹10L → 20%\n"
            "• Above ₹10L → 30%\n\n"
            "**New Regime:** Lower rates but most deductions nahi milti.\n\n"
            "**Tax Saving Tips (Section 80C — ₹1.5L limit):**\n"
            "• ELSS Mutual Fund (best — 3yr lock-in only)\n"
            "• PPF (15yr lock-in, tax-free returns)\n"
            "• Tuition fees bhi 80C mein aati hai!\n\n"
            "**As a student:** Agar income ₹2.5L se kam hai toh koi tax nahi. Internship/stipend mein TDS kata ho toh ITR file karo — refund milega! 💰"
        )

    if any(k in q for k in ['gst', 'goods and services tax', 'indirect tax', 'वस्तु एवं सेवा कर']):
        return (
            "🧾 **GST (Goods & Services Tax) Explained:**\n\n"
            "**GST kya hai?** Ek unified indirect tax jo puri India mein product/service pe lagta hai.\n\n"
            "**GST Slabs:**\n"
            "• 0% → Essential items (unprocessed food, books, salt)\n"
            "• 5% → Basic necessities (tea, edible oil, transport)\n"
            "• 12% → Processed food, computers, mobiles\n"
            "• 18% → Most services, restaurants, software\n"
            "• 28% → Luxury items, cars, tobacco, AC\n\n"
            "**Student ke liye relevant:**\n"
            "• Hostel fees pe GST nahi lagti\n"
            "• Restaurant mein khao → 5% GST (AC restaurant = 18%)\n"
            "• Amazon se order karo → product ke hisaab se GST\n\n"
            "GSTIN se online verify kar sakte ho kisi bhi business ka! 🔍"
        )

    # ════════════════════════════════════════════
    # FD / PPF / RD / NPS
    # ════════════════════════════════════════════
    if any(k in q for k in ['fd', 'fixed deposit', 'term deposit', 'fdr']):
        return (
            "🏦 **Fixed Deposit (FD) — Safe Investment:**\n\n"
            "**FD kya hai?** Bank mein ek fixed time ke liye paisa lock karo, guaranteed interest milta hai.\n\n"
            "**Current FD Rates (2024):**\n"
            "• Regular: 6.5 – 7.5% p.a.\n"
            "• Senior Citizen: +0.25 – 0.5% extra\n"
            "• Tax-Saver FD (5yr): 80C benefit\n\n"
            "**Pros:** Safe, guaranteed, DICGC insured (up to ₹5 lakh)\n"
            "**Cons:** Premature withdrawal penalty, returns inflation-adjusted mein low\n\n"
            "**Student tip:** Emergency fund ke liye FD se better hai Liquid Mutual Fund — same safety, better returns, no lock-in! 💡"
        )

    if any(k in q for k in ['ppf', 'public provident fund', 'post office']):
        return (
            "🏛️ **PPF (Public Provident Fund):**\n\n"
            "• Interest Rate: **7.1% p.a.** (tax-free!)\n"
            "• Lock-in: 15 years (partial withdrawal after 7 years)\n"
            "• Max Investment: ₹1.5 lakh/year\n"
            "• Tax benefit: 80C deduction\n"
            "• Returns: Completely TAX-FREE at maturity\n\n"
            "**EEE Status:** Invest-Exempt, Interest-Exempt, Maturity-Exempt!\n\n"
            "**Student ke liye:** Abhi se shuru karo — ₹500/month bhi chalega. 15 saal baad lakhs mil sakte hain!\n\n"
            "Bank ya Post Office mein PPF account kholo. 📮"
        )

    if any(k in q for k in ['rd', 'recurring deposit', 'recurring']):
        return (
            "🔄 **RD (Recurring Deposit):**\n\n"
            "• Har month fixed amount deposit karo\n"
            "• Interest: ~5.5 – 7% p.a.\n"
            "• Minimum: ₹100/month\n"
            "• Tenure: 6 months se 10 years\n\n"
            "**FD vs RD:** Lump sum hai toh FD, monthly savings hai toh RD!\n\n"
            "**Student ke liye:** Pocket money ka ek hissa RD mein daalo — discipline aayegi aur guaranteed return bhi! ✅"
        )

    if any(k in q for k in ['nps', 'national pension', 'pension', 'retirement', 'retire']):
        return (
            "👴 **Retirement Planning — Jitna Jaldi Shuru, Utna Acha!**\n\n"
            "**NPS (National Pension System):**\n"
            "• Government-backed pension scheme\n"
            "• Returns: 10-12% p.a. (market-linked)\n"
            "• Extra tax benefit: ₹50,000 under 80CCD(1B) — 80C ke upar!\n"
            "• Age 60 tak lock-in, partial withdrawal allowed\n\n"
            "**Student tip:** Abhi se ₹500/month NPS mein daalna shuru karo.\n"
            "₹500/month × 35 years @ 10% = **₹1.8 crore!** 🚀\n\n"
            "**Magic of compounding:** Start at 22 vs 32 — same monthly amount, double returns!"
        )

    # ════════════════════════════════════════════
    # CREDIT CARD & LOANS
    # ════════════════════════════════════════════
    if any(k in q for k in ['credit card', 'cc', 'cibil', 'credit score', 'क्रेडिट']):
        return (
            "💳 **Credit Card — Friend or Enemy?**\n\n"
            "**Friend hai agar:**\n"
            "• Poora bill every month pay karo (NEVER minimum due!)\n"
            "• Cashback/rewards points earn karo\n"
            "• CIBIL score build karo\n\n"
            "**Enemy ban jaata hai agar:**\n"
            "• Minimum due pay karte raho → 36-42% p.a. interest!\n"
            "• EMI pe baari-baari kharidate raho\n"
            "• Limit se zyada spend karo\n\n"
            "**CIBIL Score:**\n"
            "• 750+ = Excellent (saste loan milenge)\n"
            "• 650-750 = Good\n"
            "• Below 650 = Bad (loan rejection)\n\n"
            "**Student tip:** Pehla credit card lene se pehle — full bill pay karne ki guarantee karo! 🎯"
        )

    if any(k in q for k in ['loan', 'emi', 'education loan', 'home loan', 'karz', 'कर्ज', 'debt']):
        return (
            "🏦 **Loan & EMI Guide:**\n\n"
            "**Education Loan:**\n"
            "• Interest: 8-12% p.a.\n"
            "• Moratorium: Course + 6 months/1 year\n"
            "• Tax benefit: Section 80E (full interest deductible!)\n"
            "• Tip: Part-time kaam karke emi jaldi khatakar lo\n\n"
            "**Loan Lene Se Pehle:**\n"
            "• EMI income ka 30-40% se zyada na ho\n"
            "• Interest rate compare karo multiple banks mein\n"
            "• Processing fee dhyan se padho\n\n"
            "**EMI Calculator formula:** EMI = P×r×(1+r)^n / ((1+r)^n-1)\n\n"
            "**Golden Rule:** Avoid lifestyle loans (vacation, phone) — avoid karo jitna ho sake! 💡"
        )

    # ════════════════════════════════════════════
    # INSURANCE
    # ════════════════════════════════════════════
    if any(k in q for k in ['insurance', 'bima', 'term insurance', 'health insurance', 'life insurance', 'बीमा']):
        return (
            "🛡️ **Insurance — Must Have at Every Age:**\n\n"
            "**Term Life Insurance:**\n"
            "• Sabse sasta, sabse zyada cover\n"
            "• ₹1 crore cover = ₹8,000-12,000/year only (age 22 pe)\n"
            "• Jitna jaldi lo, utna sasta premium\n"
            "• Student ke liye: Abhi nahi, first job pe turant lo\n\n"
            "**Health Insurance:**\n"
            "• ₹5-10 lakh floater policy family ke liye\n"
            "• Cashless claim facility dekho\n"
            "• Premium: ₹6,000-15,000/year for young people\n"
            "• Tax benefit: Section 80D\n\n"
            "**Avoid:** ULIPs and endowment plans — investment + insurance mix never works!\n\n"
            "Remember: Insurance = Protection, Investment = Separate! 🎯"
        )

    # ════════════════════════════════════════════
    # UPI / DIGITAL PAYMENTS
    # ════════════════════════════════════════════
    if any(k in q for k in ['upi', 'gpay', 'phonepe', 'paytm', 'digital payment', 'online payment', 'net banking', 'neft', 'imps', 'rtgs']):
        return (
            "📱 **Digital Payments — Smart Student Guide:**\n\n"
            "**UPI Apps comparison:**\n"
            "• GPay — best cashback offers, Google backed\n"
            "• PhonePe — most widely accepted, good UX\n"
            "• Paytm — wallet + UPI, good for merchants\n"
            "• BHIM — government app, secure\n\n"
            "**Save money with UPI:**\n"
            "• GPay scratch cards → real cashback\n"
            "• PhonePe offers → app pe merchant deals\n"
            "• Paytm cashback → check regularly\n\n"
            "**Bank Transfer types:**\n"
            "• IMPS: Instant, 24x7, up to ₹5 lakh\n"
            "• NEFT: Hourly batches, any amount\n"
            "• RTGS: Large amounts (above ₹2 lakh), real-time\n\n"
            "**Safety tip:** NEVER share UPI PIN / OTP with anyone! 🔒"
        )

    # ════════════════════════════════════════════
    # CRYPTOCURRENCY
    # ════════════════════════════════════════════
    if any(k in q for k in ['crypto', 'bitcoin', 'ethereum', 'nft', 'web3', 'blockchain', 'cryptocurrency', 'btc', 'eth', 'binance', 'wazirx', 'coinbase']):
        return (
            "₿ **Cryptocurrency — High Risk, High Reward:**\n\n"
            "**Basics:**\n"
            "• Crypto = decentralized digital currency on blockchain\n"
            "• Bitcoin (BTC), Ethereum (ETH) sabse established hain\n"
            "• India mein legal hai but highly regulated\n\n"
            "**India mein Crypto Tax (Budget 2022):**\n"
            "• Profits pe flat 30% tax\n"
            "• Losses set-off ki permission nahi\n"
            "• 1% TDS on every transaction\n\n"
            "**Indian platforms:** WazirX, CoinDCX, ZebPay\n\n"
            "**Student ke liye honest advice:**\n"
            "• Portfolio ka 5% se zyada crypto mein mat lagao\n"
            "• Sirf wo paisa lagao jo ₹0 ho jaaye toh bhi chale\n"
            "• Bitcoin ke sirf 21 million coins hain — scarcity value hai\n\n"
            "**NFTs:** Mostly speculative — be very careful! ⚠️"
        )

    # ════════════════════════════════════════════
    # COMPOUNDING / INTEREST CALCULATIONS
    # ════════════════════════════════════════════
    if any(k in q for k in ['compound', 'compounding', 'interest', 'return', 'calculate', 'कितना', 'kitna milega', 'how much will', 'return calculate']):
        return (
            "🔢 **Power of Compounding — 8th Wonder of World!**\n\n"
            "**Formula:** A = P × (1 + r/n)^(nt)\n"
            "P=Principal, r=rate, n=compounds/year, t=years\n\n"
            "**Real Examples:**\n"
            "• ₹1,000/month SIP @ 12% for 10 years = **₹2.3 lakh** (invested ₹1.2L)\n"
            "• ₹1,000/month SIP @ 12% for 20 years = **₹9.9 lakh** (invested ₹2.4L)\n"
            "• ₹1,000/month SIP @ 12% for 30 years = **₹35 lakh** (invested ₹3.6L) 🤯\n\n"
            "**Key lesson:** Time is more powerful than amount!\n\n"
            "• Start at 22: ₹5,000/month → ₹3.5 crore at 60\n"
            "• Start at 32: ₹5,000/month → ₹1.1 crore at 60\n\n"
            "**10 saal ki delay = 3x less money!** Start TODAY! 🚀"
        )

    # ════════════════════════════════════════════
    # GENERAL FINANCE ADVICE
    # ════════════════════════════════════════════
    if any(k in q for k in ['invest', 'investment', 'paisa lagao', 'where to invest', 'kahan lagayen', 'best investment', 'portfolio']):
        return (
            "💼 **Investment Portfolio for Students — Step by Step:**\n\n"
            "**Step 1 — Emergency Fund (Priority #1)**\n"
            "₹15,000-30,000 in Liquid Mutual Fund. Touch mat karna!\n\n"
            "**Step 2 — SIP shuru karo (₹500-1000/month)**\n"
            "Nifty 50 Index Fund sabse safe choice for beginners.\n\n"
            "**Step 3 — Paper Trading practice karo**\n"
            "FinYaar pe free mein! Real market feel lo without real money.\n\n"
            "**Step 4 — Gradually increase**\n"
            "Every semester apni savings increase karo by ₹500.\n\n"
            "**Rule of Thumb:**\n"
            "• Age = Equity %, rest in Debt\n"
            "• 22 years old → 78% equity, 22% debt\n\n"
            "**Never invest in:** Tips from WhatsApp groups, get-rich-quick schemes, F&O (futures & options) without experience! ⚠️"
        )

    if any(k in q for k in ['inflation', 'mehengai', 'महंगाई', 'price rise', 'purchasing power']):
        return (
            "📈 **Inflation — Paison ka Dushman!**\n\n"
            "**Inflation kya hai?** Har saal prices badhna = paison ki value ghatta.\n\n"
            "**India ki average inflation:** 5-6% p.a.\n\n"
            "**Real impact:**\n"
            "• Aaj ₹100 ke jo cheez milti hai — 10 saal baad ₹163 ki hogi\n"
            "• Bank savings account = 3-4% interest = inflation se NEECHE!\n\n"
            "**Inflation se beat karna:**\n"
            "• FD nahi → Equity Mutual Funds (12-15% historical return)\n"
            "• Cash mat rakho → Invest karo\n"
            "• Real estate, gold bhi inflation hedge hain\n\n"
            "**Rule:** Return > Inflation rate = Real wealth creation!\n"
            "Equity funds historically inflation se 2x aage hain. 💪"
        )

    if any(k in q for k in ['gold', 'सोना', 'sovereign gold bond', 'sgb', 'digital gold', 'gold etf']):
        return (
            "🥇 **Gold Investment — Traditional vs Smart:**\n\n"
            "**Physical Gold ki problems:**\n"
            "• Making charges (10-20%) — instant loss\n"
            "• Storage risk, purity doubt\n"
            "• Low liquidity\n\n"
            "**Smart Gold Alternatives:**\n\n"
            "**Sovereign Gold Bond (SGB) — Best option!**\n"
            "• Government of India ka bond\n"
            "• Gold price ka benefit + 2.5% extra interest p.a.\n"
            "• Tax-free at maturity (8 years)\n"
            "• Risk-free (government backed)\n\n"
            "**Gold ETF:** Stock jaise trade karo, no storage issue\n\n"
            "**Digital Gold (Paytm/GPay):** Convenient but no SGB benefit\n\n"
            "**Portfolio mein gold:** Maximum 10-15% — hedge against uncertainty! 🛡️"
        )

    if any(k in q for k in ['real estate', 'property', 'ghar', 'house', 'rent', 'home buy', 'makaan']):
        return (
            "🏠 **Real Estate — Buy vs Rent Decision:**\n\n"
            "**Student ke liye:** Abhi rent karo — flexibility important hai!\n\n"
            "**Buy karna kab sahi hai?**\n"
            "• Stable income (3+ years same city)\n"
            "• 20% down payment ready hai\n"
            "• EMI income ka 30% se kam ho\n\n"
            "**Real Estate returns:**\n"
            "• Average 8-10% p.a. appreciation\n"
            "• Rental yield: 2-3% (Mumbai/Delhi)\n"
            "• Rental yield: 3-5% (Tier 2 cities)\n\n"
            "**Hidden costs:** Registration (5-7%), stamp duty, maintenance, property tax\n\n"
            "**Honest advice:** Equity mutual funds ne historically real estate se better returns diye hain. Don't rush to buy! 💡"
        )

    # ════════════════════════════════════════════
    # FINYAAR PLATFORM HELP
    # ════════════════════════════════════════════
    if any(k in q for k in ['finyaar', 'app', 'platform', 'kaise use', 'how to use', 'feature', 'paper trading kaise', 'expense kaise']):
        return (
            "📱 **FinYaar Platform Guide:**\n\n"
            "**Main Features:**\n\n"
            "🏠 **Dashboard** — Budget overview, spending pie chart, quick stats\n\n"
            "💸 **Expenses** — Har kharch add karo with category. Auto analysis milti hai.\n\n"
            "🎯 **Goals** — Savings goals set karo with deadline and target amount.\n\n"
            "📈 **Trading** — Paper Trading with ₹1 lakh virtual cash. NSE stocks practice karo!\n\n"
            "🤖 **FinBot** — Yahan ho tum! Finance questions poochho.\n\n"
            "🔔 **Notifications** — Budget alerts, goal achievements, trade confirmations.\n\n"
            "**Daily habit:** Har roz expenses add karo → month end mein surprise nahi hoga! 😊"
        )

    # ════════════════════════════════════════════
    # GENERAL / OFF-TOPIC (Answer + Finance tip)
    # ════════════════════════════════════════════
    if any(k in q for k in ['exam', 'pariksha', 'study', 'padhai', 'college', 'campus', 'hostel', 'mess']):
        return (
            "📚 **College + Finance = Smart Student!**\n\n"
            "Studies ke saath paisa bhi manage karna ek important skill hai.\n\n"
            "**Campus pe smart money moves:**\n"
            "• Mess bill track karo — sab se bada expense hota hai\n"
            "• Library books use karo — har semester ₹2,000-5,000 bachenge\n"
            "• Student discounts use karo (Spotify, Amazon Prime, Notion, etc.)\n"
            "• Internship mein stipend mile toh 50% invest karo\n\n"
            "**Extra income ideas for students:**\n"
            "• Freelancing (content writing, design, coding)\n"
            "• Online tutoring\n"
            "• Campus ambassador programs\n\n"
            "Financial education + academic education = 🏆 Winning combination!"
        )

    if any(k in q for k in ['job', 'salary', 'placement', 'career', 'first job', 'नौकरी', 'package']):
        return (
            "💼 **First Job Pe Finance Smart Karo!**\n\n"
            "**Salary milte hi ye karo (first month se):**\n\n"
            "1. **Term Insurance** lo — young ho, premium ₹8,000/year mein ₹1 crore cover\n"
            "2. **Health Insurance** lo — company wali pe depend mat raho\n"
            "3. **Emergency Fund** banao — 3 months salary liquid mein\n"
            "4. **SIP shuru karo** — ₹3,000-5,000/month from day 1\n"
            "5. **EPF contribute karo** — free 12% employer match!\n\n"
            "**Salary allocation (first job):**\n"
            "• 50% fixed expenses\n"
            "• 20% savings/investments (non-negotiable!)\n"
            "• 20% wants\n"
            "• 10% emergency fund building\n\n"
            "Pehli salary mein iPhone mat lo — invest karo! 😄"
        )

    # ════════════════════════════════════════════
    # GENERIC FALLBACK (still helpful!)
    # ════════════════════════════════════════════
    return (
        f"🤖 **Hello {user.name}! I am FinBot!**\n\n"
        "I am currently in fallback mode, so I can mainly help you with these financial topics:\n\n"
        "💰 **Budgeting** → 50/30/20 rule, expense tracking\n"
        "📈 **Investing** → SIP, Mutual Funds, Stocks, Index Funds\n"
        "🏦 **Safe Savings** → FD, PPF, RD, Liquid Funds\n"
        "📊 **Stock Market** → NSE/BSE, NIFTY, Paper Trading\n"
        "🧾 **Tax** → Income Tax, GST, 80C saving\n"
        "💳 **Loans & Cards** → EMI, Credit Score, CIBIL\n"
        "🛡️ **Insurance** → Term, Health\n"
        "₿ **Crypto** → Bitcoin, Ethereum, risks\n"
        "📱 **Digital Payments** → UPI, Cashback tips\n\n"
        "When my AI API is fully connected, I act like ChatGPT and can answer ANY question about ANY topic in English! 😊\n\n"
        f"Current status: You have ₹{user.budget - total_sp:,.0f} budget remaining this month."
    )


@app.route('/api/finbot/chat', methods=['POST'])
@jwt_required()
def finbot_chat():
    uid   = get_jwt_identity()
    query = request.json.get('message', '').strip()
    if not query:
        return jsonify(error='Empty message'), 400

    # ── User context ─────────────────────────────────────────
    user     = User.query.get(uid)
    expenses = Expense.query.filter_by(user_id=uid).all()
    total_sp = sum(e.amount for e in expenses)
    goals    = SavingsGoal.query.filter_by(user_id=uid).all()

    system_ctx = (
        f"{FINBOT_SYSTEM}\n\n"
        f"STUDENT PROFILE: Name={user.name}, Course={user.course}, Year={user.year}, "
        f"Monthly Budget=₹{user.budget}, Total Spent=₹{total_sp:.0f}, "
        f"Active Goals={len(goals)}, Paper Trading Cash=₹{user.paper_cash:.0f}. "
        f"Personalize your response using this data when relevant."
    )

    # ── Try Hugging Face (real AI) ────────────────────────────
    reply = None
    if HF_API_KEY:
        reply = _call_huggingface(query, system_ctx)
        if reply:
            print(f"✅ [FinBot] HF Mistral response for user {uid}")
        else:
            print(f"⚠️ [FinBot] HF failed — using comprehensive fallback for user {uid}")

    # ── Comprehensive rule-based fallback ────────────────────
    if not reply:
        reply = _smart_fallback(query, user, total_sp, goals)

    # ── Log & return ─────────────────────────────────────────
    db.session.add(FinBotLog(user_id=uid, query=query, response=reply))
    db.session.commit()
    return jsonify(reply=reply)

# ──────────────────────────────────────
# NOTIFICATIONS  /api/notifications
# ──────────────────────────────────────

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    uid   = get_jwt_identity()
    notifs= Notification.query.filter_by(user_id=uid).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify(notifications=[{ 'id':n.notif_id,'msg':n.message,'type':n.type,'read':n.is_read,'at':str(n.created_at) } for n in notifs])


@app.route('/api/notifications/<int:notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notif_id):
    uid = get_jwt_identity()
    n = Notification.query.filter_by(notif_id=notif_id, user_id=uid).first_or_404()
    n.is_read = True
    db.session.commit()
    return jsonify(message='Marked as read')

# ──────────────────────────────────────
# DAILY TRADING RESET  (midnight IST)
# ──────────────────────────────────────

IST_OFFSET = timedelta(hours=5, minutes=30)

def _do_daily_reset():
    with app.app_context():
        today_ist = (datetime.utcnow() + IST_OFFSET).date()
        users_reset = 0
        for user in User.query.all():
            if user.last_reset_date != today_ist:
                user.paper_cash      = 100000.0
                user.last_reset_date = today_ist
                users_reset += 1
        if users_reset:
            db.session.commit()
            print(f"✅ [FinYaar] Daily reset: {users_reset} user(s) paper_cash → ₹1,00,000 ({today_ist} IST)")

# Removed daily reset scheduler as requested.


@app.route('/api/trading/reset-balance', methods=['POST'])
@jwt_required()
def check_daily_reset():
    uid       = get_jwt_identity()
    user      = User.query.get(uid)
    # Disabled daily reset as requested by user.
    return jsonify(paper_cash=user.paper_cash, reset=False)

# ──────────────────────────────────────
# RUN
# ──────────────────────────────────────
# Initialize DB for Gunicorn/Render
with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_reset_date DATE"))
            conn.commit()
        print("✅ Migrated: added last_reset_date column to users")
    except Exception:
        pass
    print("✅ FinYaar DB tables ready.")

if __name__ == '__main__':
    print(f"🤖 FinBot: HF API Key {'✅ SET' if HF_API_KEY else '❌ NOT SET — using fallback only'}")
    # t = threading.Thread(target=_midnight_scheduler, daemon=True)
    # t.start()
    app.run(debug=True, port=5000, use_reloader=False)
