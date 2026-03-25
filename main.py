"""
Dashboard Application Meme — A dashboard application for meme generation. It has a main control panel with a text input field for meme ideas, a file upload for a template image, and a huge Generate Meme button. Once generated, the meme appears in the dashboard center. Dark mode UI.
Built by Sheept 🐑💤 | Type: dashboard | Seed: e5471c276aa9
"""
import json, sqlite3, uuid, hashlib
from datetime import datetime, timezone
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Dashboard Application Meme", description="A dashboard application for meme generation. It has a main control panel with a text input field for meme ideas, a file upload for a template image, and a huge Generate Meme button. Once generated, the meme appears in the dashboard center. Dark mode UI.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
DB = "/tmp/dashboard_application_meme_e5471c.db"

@contextmanager
def db():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    try: yield conn.cursor(); conn.commit()
    finally: conn.close()

def uid(): return uuid.uuid4().hex[:12]
def now(): return datetime.now(timezone.utc).isoformat()
def hash_pw(pw: str) -> str: return hashlib.sha256(pw.encode()).hexdigest()

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS auth_users (id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT);
        CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, user_id TEXT, message TEXT, rating INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, data JSON, user_id TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS metrics (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, value REAL, unit TEXT, recorded_at TEXT);
        CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, user_id TEXT, title TEXT, data JSON, period TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS alerts (id TEXT PRIMARY KEY, user_id TEXT, metric_name TEXT, threshold REAL, direction TEXT DEFAULT 'above', active INTEGER DEFAULT 1, created_at TEXT);
        CREATE TABLE IF NOT EXISTS data_points (id TEXT PRIMARY KEY, metric_id TEXT, value REAL, timestamp TEXT);
        CREATE TABLE IF NOT EXISTS dashboards (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, layout JSON, created_at TEXT);
        """)
init()

def get_user(auth: Optional[str] = Header(None)):
    if not auth: raise HTTPException(401, "Missing Auth")
    with db() as c:
        c.execute("SELECT * FROM auth_users WHERE id=?", (auth.replace("Bearer ", ""),))
        u = c.fetchone()
        if not u: raise HTTPException(401, "Invalid token")
        return dict(u)

class RegisterReq(BaseModel): username: str; password: str
class LoginReq(BaseModel): username: str; password: str

@app.post("/register")
def register(r: RegisterReq):
    u = uid()
    with db() as c:
        try: c.execute("INSERT INTO auth_users VALUES (?,?,?,?,?)", (u, r.username, hash_pw(r.password), "user", now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "Username taken")
    return {"user_id": u, "token": u}

@app.post("/login")
def login(r: LoginReq):
    with db() as c:
        c.execute("SELECT * FROM auth_users WHERE username=? AND password_hash=?", (r.username, hash_pw(r.password)))
        u = c.fetchone()
        if not u: raise HTTPException(401, "Invalid credentials")
    return {"user_id": u["id"], "token": u["id"], "username": u["username"]}

class MetricsReq(BaseModel):
    name: str
    value: float

class ReportsReq(BaseModel):
    title: str

class AlertsReq(BaseModel):
    metric_name: str
    threshold: float

@app.get("/metrics")
def list_metrics(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM metrics ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/metrics")
def create_metrics(r: MetricsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO metrics ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/metrics/{id}")
def get_metrics(id: str):
    with db() as c: c.execute("SELECT * FROM metrics WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/metrics/{id}")
def delete_metrics(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM metrics WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/reports")
def list_reports(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/reports")
def create_reports(r: ReportsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO reports ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/reports/{id}")
def get_reports(id: str):
    with db() as c: c.execute("SELECT * FROM reports WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/reports/{id}")
def delete_reports(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM reports WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/alerts")
def list_alerts(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/alerts")
def create_alerts(r: AlertsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO alerts ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/alerts/{id}")
def get_alerts(id: str):
    with db() as c: c.execute("SELECT * FROM alerts WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/alerts/{id}")
def delete_alerts(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM alerts WHERE id=?", (id,))
    return {"id": id, "deleted": True}

@app.get("/metrics/summary")
def metrics_summary(auth: Optional[str] = Header(None)):
    u = get_user(auth)
    with db() as c: c.execute("SELECT name, AVG(value) as avg_val FROM metrics WHERE user_id=? GROUP BY name", (u["id"],)); return [dict(r) for r in c.fetchall()]

class FeedbackReq(BaseModel): message: str; rating: Optional[int] = None

@app.post("/feedback")
def submit_feedback(r: FeedbackReq, auth: Optional[str] = Header(None)):
    user_id = None
    if auth:
        try: user_id = get_user(auth)["id"]
        except Exception: pass
    with db() as c: c.execute("INSERT INTO feedback VALUES (?,?,?,?,?)", (uid(), user_id, r.message, r.rating, now()))
    return {"message": "Thanks! 🐑"}

@app.get("/stats")
def stats():
    with db() as c:
        c.execute("SELECT COUNT(*) as cnt FROM auth_users"); users = c.fetchone()["cnt"]
    return {"total_users": users, "built_with": "Sheept 🐑"}

@app.get("/health")
def health(): return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
def home(): return FRONTEND_HTML


FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Application Meme</title>
  <meta name="description" content="A dashboard application for meme generation. It has a main control panel with a text input field for meme ideas, a file upload for a template image, and a huge Generate Meme button. Once generated, the meme appears in the dashboard center. Dark mode UI.">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐑</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'] },
          colors: {
            primary: '#18181b',
            accent: '#00bed0',
            surface: '#27272a',
            cta: '#0891b2',
            'cta-text': '#ffffff',
            muted: '#71717a',
            'card-bg': '#27272a',
            'card-border': '#3f3f46',
            'alt-bg': '#18181b',
            'nav-bg': 'rgba(24,24,27,0.8)',
            'footer-bg': '#09090b',
          }
        }
      }
    }
  </script>
  <style>
    html { scroll-behavior: smooth; }
    body { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
    .reveal { opacity: 0; transform: translateY(30px); transition: all 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94); }
    .reveal.visible { opacity: 1; transform: translateY(0); }
    .reveal-delay-1 { transition-delay: 0.1s; }
    .reveal-delay-2 { transition-delay: 0.2s; }
    .reveal-delay-3 { transition-delay: 0.3s; }
    .reveal-delay-4 { transition-delay: 0.4s; }
    .reveal-delay-5 { transition-delay: 0.5s; }
    .gradient-text {
      background: linear-gradient(135deg, #00bed0, #0891b2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .hero-gradient {
      background: linear-gradient(135deg, #18181b, #164e63);
    }
    /* Toast notification */
    .toast { position: fixed; bottom: 2rem; right: 2rem; padding: 1rem 1.5rem; border-radius: 0.75rem; font-weight: 500; font-size: 0.875rem; z-index: 1000; transform: translateY(120%); opacity: 0; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
    .toast.show { transform: translateY(0); opacity: 1; }
    .toast-success { background: #059669; color: white; }
    .toast-error { background: #dc2626; color: white; }
    /* Loading spinner */
    .spinner { width: 1.25rem; height: 1.25rem; border: 2px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block; }
    @keyframes spin { to { transform: rotate(360deg); } }
    /* Skeleton loading */
    .skeleton { background: linear-gradient(90deg, #334155 25%, #475569 50%, #334155 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 0.5rem; }
    @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    /* Modal overlay */
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 100; display: none; align-items: center; justify-content: center; }
    .modal-overlay.active { display: flex; }
    /* Custom scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #71717a40; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #71717a80; }
  </style>
</head>
<body class="antialiased" style="background: #18181b; color: #fafafa;">
  <!-- Navigation -->
  <nav class="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b border-white/10" style="background: rgba(24,24,27,0.8);">
    <div class="max-w-6xl mx-auto px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <a href="#" class="flex items-center gap-2 text-white font-bold text-lg">
          <span>🐑</span> <span>Dashboard Application Meme</span>
        </a>
        <div class="hidden md:flex items-center gap-8">
          <a href="#overview" class="text-white/70 hover:text-gray-300 transition-colors text-sm font-medium">Overview</a>
            <a href="#charts" class="text-white/70 hover:text-gray-300 transition-colors text-sm font-medium">Charts</a>
            <a href="#reports" class="text-white/70 hover:text-gray-300 transition-colors text-sm font-medium">Reports</a>
            <a href="#settings" class="text-white/70 hover:text-gray-300 transition-colors text-sm font-medium">Settings</a>
            
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-3">
              <button onclick="showAuth('login')" class="text-white/70 hover:text-gray-300 transition-colors text-sm font-medium" id="nav-login-btn">Sign In</button>
              <button onclick="showAuth('register')" class="bg-cta text-cta-text px-4 py-2 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity" id="nav-register-btn">Get Started</button>
              <button onclick="logout()" class="hidden text-white/70 hover:text-gray-300 transition-colors text-sm font-medium" id="nav-logout-btn">Log Out</button>
            </div>
          <button onclick="document.getElementById('mobile-menu').classList.toggle('hidden')" class="md:hidden text-white/70">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
          </button>
        </div>
      </div>
      <!-- Mobile menu -->
      <div id="mobile-menu" class="hidden md:hidden pb-4 space-y-2">
        <a href="#overview" class="block py-2 text-white/70 hover:text-gray-300 text-sm font-medium">Overview</a><a href="#charts" class="block py-2 text-white/70 hover:text-gray-300 text-sm font-medium">Charts</a><a href="#reports" class="block py-2 text-white/70 hover:text-gray-300 text-sm font-medium">Reports</a><a href="#settings" class="block py-2 text-white/70 hover:text-gray-300 text-sm font-medium">Settings</a>
      </div>
    </div>
  </nav>
  <div class="h-16"></div>
  <div id="landing-content">
  <!-- Hero -->
  <section class="hero-gradient min-h-[90vh] flex items-center relative overflow-hidden">
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute -top-40 -right-40 w-80 h-80 rounded-full opacity-20" style="background: #00bed0; filter: blur(100px);"></div>
      <div class="absolute -bottom-40 -left-40 w-96 h-96 rounded-full opacity-10" style="background: #0891b2; filter: blur(120px);"></div>
    </div>
    <div class="max-w-6xl mx-auto px-6 lg:px-8 py-20 relative z-10">
      <div class="max-w-3xl">
        <div class="reveal">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium mb-8" style="background: #00bed015; color: #00bed0;">
            <span class="w-2 h-2 rounded-full" style="background: #00bed0;"></span>
            Now Live
          </div>
        </div>
        <h1 class="reveal text-5xl sm:text-6xl lg:text-7xl font-extrabold text-white tracking-tight leading-[1.1] mb-6">
          Dashboard Application Meme
        </h1>
        <p class="reveal reveal-delay-1 text-xl sm:text-2xl text-gray-300 leading-relaxed max-w-2xl mb-10">
          A dashboard application for meme generation. It has a main control panel with a text input field for meme ideas, a file upload for a template image, and a huge Generate Meme button. Once generated, the meme appears in the dashboard center. Dark mode UI.
        </p>
        <div class="reveal reveal-delay-2 flex flex-col sm:flex-row gap-4">
          <button onclick="showAuth('register')" class="inline-flex items-center justify-center px-8 py-4 bg-cta text-cta-text rounded-xl text-lg font-semibold hover:opacity-90 transition-all hover:shadow-lg hover:shadow-cta/25 hover:-translate-y-0.5">
            Get Started Free
            <svg class="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
          </button>
          <a href="#features" class="inline-flex items-center justify-center px-8 py-4 rounded-xl text-lg font-semibold text-white/80 hover:text-white transition-colors" style="border: 1px solid #3f3f46;">
            Learn More
          </a>
        </div>
      </div>
    </div>
  </section>
  <!-- Features -->
  <section id="features" class="py-24 lg:py-32" style="background: #18181b;">
    <div class="max-w-6xl mx-auto px-6 lg:px-8">
      <div class="text-center mb-16">
        <h2 class="reveal text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">Everything you need</h2>
        <p class="reveal reveal-delay-1 text-lg text-gray-400 max-w-2xl mx-auto">Powerful features designed to give you the best experience, right out of the box.</p>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
          <div class="reveal reveal-delay-1 group p-6 rounded-2xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-3xl mb-4">📈</div>
            <h3 class="text-lg font-semibold text-white mb-2">Live Charts</h3>
            <p class="text-gray-400 text-sm leading-relaxed">Beautiful, interactive charts that make your data tell a story.</p>
          </div>
          <div class="reveal reveal-delay-2 group p-6 rounded-2xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-3xl mb-4">📋</div>
            <h3 class="text-lg font-semibold text-white mb-2">Smart Reports</h3>
            <p class="text-gray-400 text-sm leading-relaxed">Auto-generated reports with key insights delivered on your schedule.</p>
          </div>
          <div class="reveal reveal-delay-3 group p-6 rounded-2xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-3xl mb-4">🔔</div>
            <h3 class="text-lg font-semibold text-white mb-2">Custom Alerts</h3>
            <p class="text-gray-400 text-sm leading-relaxed">Set thresholds and get notified the moment something needs attention.</p>
          </div>
          <div class="reveal reveal-delay-4 group p-6 rounded-2xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-3xl mb-4">📍</div>
            <h3 class="text-lg font-semibold text-white mb-2">Data Tracking</h3>
            <p class="text-gray-400 text-sm leading-relaxed">Track any metric with automatic data collection and trend analysis.</p>
          </div>
          <div class="reveal reveal-delay-5 group p-6 rounded-2xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-3xl mb-4">📤</div>
            <h3 class="text-lg font-semibold text-white mb-2">Easy Export</h3>
            <p class="text-gray-400 text-sm leading-relaxed">Export your data in any format — CSV, PDF, or via API.</p>
          </div>
      </div>
    </div>
  </section>
  <!-- How It Works -->
  <section id="how-it-works" class="py-24 lg:py-32" style="background: #18181b;">
    <div class="max-w-6xl mx-auto px-6 lg:px-8">
      <div class="text-center mb-16">
        <h2 class="reveal text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">How it works</h2>
        <p class="reveal reveal-delay-1 text-lg text-gray-400 max-w-2xl mx-auto">Get started in minutes with our simple, straightforward process.</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
        
        <div class="reveal reveal-delay-1 flex flex-col items-center text-center">
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold mb-5" style="background: #00bed020; color: #00bed0;">
            1
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Connect Data</h3>
          <p class="text-gray-400 text-sm leading-relaxed max-w-xs">Link your data sources or start tracking metrics manually.</p>
        </div>
        <div class="reveal reveal-delay-2 flex flex-col items-center text-center">
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold mb-5" style="background: #00bed020; color: #00bed0;">
            2
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Visualize</h3>
          <p class="text-gray-400 text-sm leading-relaxed max-w-xs">See your data come alive with beautiful, interactive charts.</p>
        </div>
        <div class="reveal reveal-delay-3 flex flex-col items-center text-center">
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold mb-5" style="background: #00bed020; color: #00bed0;">
            3
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Set Alerts</h3>
          <p class="text-gray-400 text-sm leading-relaxed max-w-xs">Configure thresholds and get notified when things change.</p>
        </div>
        <div class="reveal reveal-delay-4 flex flex-col items-center text-center">
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold mb-5" style="background: #00bed020; color: #00bed0;">
            4
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Take Action</h3>
          <p class="text-gray-400 text-sm leading-relaxed max-w-xs">Make data-driven decisions with clear, actionable insights.</p>
        </div>
      </div>
    </div>
  </section>
  <!-- CTA -->
  <section class="py-24 lg:py-32 relative overflow-hidden" style="background: #09090b;">
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10" style="background: #00bed0; filter: blur(150px);"></div>
    </div>
    <div class="max-w-4xl mx-auto px-6 lg:px-8 text-center relative z-10">
      <h2 class="reveal text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
        Ready to get started?
      </h2>
      <p class="reveal reveal-delay-1 text-lg text-gray-400 mb-10 max-w-2xl mx-auto">
        Join Dashboard Application Meme today and experience the difference. No credit card required.
      </p>
      <div class="reveal reveal-delay-2">
        <button onclick="showAuth('register')" class="inline-flex items-center justify-center px-10 py-4 bg-cta text-cta-text rounded-xl text-lg font-semibold hover:opacity-90 transition-all hover:shadow-lg hover:shadow-cta/25 hover:-translate-y-0.5">
          Start Free Now
          <svg class="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
        </button>
      </div>
    </div>
  </section>
  </div>
  <!-- App Dashboard (shown after login) -->
  <section id="app-dashboard" class="hidden py-12 min-h-screen" style="background: #18181b;">
    <div class="max-w-6xl mx-auto px-6 lg:px-8">
      <!-- Welcome -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-white" id="welcome-msg">Welcome back 👋</h1>
        <p class="text-gray-400 mt-1" id="welcome-sub">Here's what's happening today</p>
      </div>
      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        
          <div class="p-5 rounded-2xl transition-all hover:shadow-md" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-2xl mb-2">📊</div>
            <div class="text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">Metrics Tracked</div>
            <div class="text-white text-2xl font-bold" id="stat-metrics">--</div>
          </div>
          <div class="p-5 rounded-2xl transition-all hover:shadow-md" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-2xl mb-2">📋</div>
            <div class="text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">Reports</div>
            <div class="text-white text-2xl font-bold" id="stat-reports">--</div>
          </div>
          <div class="p-5 rounded-2xl transition-all hover:shadow-md" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-2xl mb-2">🔔</div>
            <div class="text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">Active Alerts</div>
            <div class="text-white text-2xl font-bold" id="stat-alerts">--</div>
          </div>
          <div class="p-5 rounded-2xl transition-all hover:shadow-md" style="background: #27272a; border: 1px solid #3f3f46;">
            <div class="text-2xl mb-2">📈</div>
            <div class="text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">Data Points</div>
            <div class="text-white text-2xl font-bold" id="stat-datapoints">--</div>
          </div>
      </div>
      <!-- Content -->
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        <div class="p-6 rounded-2xl" style="background: #27272a; border: 1px solid #3f3f46;">
          <h3 class="text-lg font-semibold text-white mb-4">📊 Metrics Summary</h3>
          <div id="metrics-summary" class="space-y-3">
            <div class="skeleton h-8 w-full"></div>
            <div class="skeleton h-8 w-3/4"></div>
            <div class="skeleton h-8 w-1/2"></div>
          </div>
        </div>
        <div class="p-6 rounded-2xl" style="background: #27272a; border: 1px solid #3f3f46;">
          <h3 class="text-lg font-semibold text-white mb-4">📍 Track New Metric</h3>
          <div class="space-y-3">
            <input id="metric-name" placeholder="Metric name" class="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-cta/30" style="background: #27272a; border: 1px solid #3f3f46; color: #fafafa;">
            <input id="metric-value" type="number" placeholder="Value" class="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-cta/30" style="background: #27272a; border: 1px solid #3f3f46; color: #fafafa;">
            <button onclick="addMetric()" class="w-full py-3 bg-cta text-cta-text rounded-xl text-sm font-semibold hover:opacity-90 transition-opacity">
              Track Metric
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
  <!-- Footer -->
  <footer class="py-12" style="background: #09090b; border-top: 1px solid rgba(255,255,255,0.05);">
    <div class="max-w-6xl mx-auto px-6 lg:px-8">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2 text-white/70 text-sm">
          <span>🐑</span> <span>Dashboard Application Meme</span>
        </div>
        <p class="text-gray-500 text-sm">
          Built with 🐑 <a href="https://shpt.ai" target="_blank" class="text-gray-400 hover:text-white transition-colors">Sheept</a>
        </p>
      </div>
    </div>
  </footer>
  <!-- Auth Modal -->
  <div id="auth-modal" class="modal-overlay" onclick="if(event.target===this)closeAuth()">
    <div class="w-full max-w-md mx-4 p-8 rounded-2xl shadow-2xl" style="background: #27272a; border: 1px solid #3f3f46;">
      <div class="text-center mb-8">
        <div class="text-4xl mb-3">🐑</div>
        <h2 class="text-2xl font-bold text-white" id="auth-title">Welcome Back</h2>
        <p class="text-sm mt-1" style="color: #71717a;" id="auth-subtitle">Sign in to your account</p>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-white mb-1.5">Username</label>
          <input id="auth-user" type="text" placeholder="Enter your username"
            class="w-full px-4 py-3 rounded-xl text-sm font-medium outline-none transition-all focus:ring-2 focus:ring-cta/30"
            style="background: #27272a; border: 1px solid #3f3f46; color: #fafafa;">
        </div>
        <div>
          <label class="block text-sm font-medium text-white mb-1.5">Password</label>
          <input id="auth-pass" type="password" placeholder="Enter your password"
            class="w-full px-4 py-3 rounded-xl text-sm font-medium outline-none transition-all focus:ring-2 focus:ring-cta/30"
            style="background: #27272a; border: 1px solid #3f3f46; color: #fafafa;">
        </div>
        <button id="auth-submit" onclick="doAuth()"
          class="w-full py-3.5 bg-cta text-cta-text rounded-xl font-semibold text-sm hover:opacity-90 transition-all mt-2">
          Sign In
        </button>
      </div>
      <div class="mt-6 text-center">
        <span class="text-sm" style="color: #71717a;" id="auth-switch-text">Don't have an account?</span>
        <button onclick="toggleAuthMode()" class="text-sm font-semibold ml-1" style="color: #00bed0;" id="auth-switch-btn">Sign Up</button>
      </div>
    </div>
  </div>
  <!-- Create Modal -->
  <div id="create-modal" class="modal-overlay" onclick="if(event.target===this)closeCreateModal()">
    <div class="w-full max-w-md mx-4 p-8 rounded-2xl shadow-2xl" style="background: #27272a; border: 1px solid #3f3f46;">
      <h2 class="text-xl font-bold text-white mb-6">Track Metric</h2>
      <div class="space-y-4">
        
          <div>
            <label class="block text-sm font-medium text-white mb-1.5">Metric Name</label>
            <input id="create-name" type="text" placeholder="Metric Name"
              class="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-cta/30"
              style="background: #27272a; border: 1px solid #3f3f46; color: #fafafa;">
          </div>
          <div>
            <label class="block text-sm font-medium text-white mb-1.5">Value</label>
            <input id="create-value" type="number" placeholder="Value"
              class="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-cta/30"
              style="background: #27272a; border: 1px solid #3f3f46; color: #fafafa;">
          </div>
        <button onclick="submitCreate()" class="w-full py-3.5 bg-cta text-cta-text rounded-xl font-semibold text-sm hover:opacity-90 transition-all mt-2">
          Create
        </button>
      </div>
    </div>
  </div>
  <!-- Toast -->
  <div id="toast" class="toast toast-success">Message</div>
<script>
  // ─── Core API ─────────────────────────────────────────────
  const API = window.location.origin;
  let TOKEN = localStorage.getItem('token');
  let AUTH_MODE = 'login';
  const accent = '#00bed0';
  const cardBg = '#27272a';
  const cardBorder = '#3f3f46';

  function v(id) { return document.getElementById(id)?.value || ''; }

  async function api(path, opts = {}) {
    const headers = {'Content-Type': 'application/json', ...opts.headers};
    if (TOKEN) headers['Authorization'] = 'Bearer ' + TOKEN;
    const r = await fetch(API + path, {...opts, headers});
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Request failed');
    }
    return r.json();
  }

  // ─── Toast ────────────────────────────────────────────────
  function toast(msg, type = 'success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast toast-' + type + ' show';
    setTimeout(() => t.classList.remove('show'), 3000);
  }

  // ─── Auth ─────────────────────────────────────────────────
  function showAuth(mode) {
    AUTH_MODE = mode;
    document.getElementById('auth-modal').classList.add('active');
    document.getElementById('auth-title').textContent = mode === 'register' ? 'Create Account' : 'Welcome Back';
    document.getElementById('auth-subtitle').textContent = mode === 'register' ? 'Start your journey today' : 'Sign in to your account';
    document.getElementById('auth-submit').textContent = mode === 'register' ? 'Create Account' : 'Sign In';
    document.getElementById('auth-switch-text').textContent = mode === 'register' ? 'Already have an account?' : "Don't have an account?";
    document.getElementById('auth-switch-btn').textContent = mode === 'register' ? 'Sign In' : 'Sign Up';
  }
  function closeAuth() { document.getElementById('auth-modal').classList.remove('active'); }
  function toggleAuthMode() { showAuth(AUTH_MODE === 'login' ? 'register' : 'login'); }

  async function doAuth() {
    const username = v('auth-user'), password = v('auth-pass');
    if (!username || !password) return toast('Please fill in all fields', 'error');
    try {
      const data = await api('/' + AUTH_MODE, {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      TOKEN = data.token;
      localStorage.setItem('token', TOKEN);
      closeAuth();
      toast(AUTH_MODE === 'register' ? 'Welcome! 🐑' : 'Welcome back!');
      updateUI();
    } catch(e) {
      toast(e.message || 'Authentication failed', 'error');
    }
  }

  function logout() {
    TOKEN = null;
    localStorage.removeItem('token');
    toast('Logged out');
    updateUI();
  }

  // ─── UI State ─────────────────────────────────────────────
  function updateUI() {
    const loggedIn = !!TOKEN;
    const landing = document.getElementById('landing-content');
    const app = document.getElementById('app-dashboard');
    const loginBtn = document.getElementById('nav-login-btn');
    const registerBtn = document.getElementById('nav-register-btn');
    const logoutBtn = document.getElementById('nav-logout-btn');

    if (landing) landing.style.display = loggedIn ? 'none' : 'block';
    if (app) app.classList.toggle('hidden', !loggedIn);
    if (loginBtn) loginBtn.classList.toggle('hidden', loggedIn);
    if (registerBtn) registerBtn.classList.toggle('hidden', loggedIn);
    if (logoutBtn) logoutBtn.classList.toggle('hidden', !loggedIn);

    if (loggedIn) loadAppData();
  }

  // ─── Data Loading ─────────────────────────────────────────
  async function loadAppData() {
    // Load primary data
    try {
      const items = await api('/metrics');
      const el = document.getElementById('data-grid');
      if (el) {
        el.innerHTML = items.length
          ? items.map(m => `<div class="flex items-center justify-between p-4 rounded-xl hover:shadow-md transition-all" style="background: ${cardBg}; border: 1px solid ${cardBorder};"><span class="font-semibold">${m.name}</span><span class="font-bold" style="color: ${accent};">${m.value} ${m.unit||''}</span></div>`).join('')
          : '<p class="text-sm opacity-60 py-4">Nothing here yet. Create your first item!</p>';
      }
    } catch(e) { console.log('Load error:', e); }

    // Load stats
    try {
      const stats = await api('/stats');
      Object.entries(stats).forEach(([k, val]) => {
        const el = document.getElementById('stat-' + k);
        if (el) el.textContent = val;
      });
    } catch(e) {}

    
    loadMetrics();
    
  }

  // ─── Create Modal ─────────────────────────────────────────
  function showCreateModal() { document.getElementById('create-modal').classList.add('active'); }
  function closeCreateModal() { document.getElementById('create-modal').classList.remove('active'); }

  async function submitCreate() {
    try {
      const body = { name: v('create-name'), value: parseFloat(v('create-value'))||0 };
      await api('/metrics', { method: 'POST', body: JSON.stringify(body) });
      closeCreateModal();
      toast('Created successfully!');
      loadAppData();
    } catch(e) {
      toast(e.message || 'Failed to create', 'error');
    }
  }

  
  async function addMetric() {
    const name = document.getElementById('metric-name')?.value;
    const value = parseFloat(document.getElementById('metric-value')?.value);
    if (!name || isNaN(value)) return;
    await api('/metrics', {method:'POST', body: JSON.stringify({name, value})});
    document.getElementById('metric-name').value = '';
    document.getElementById('metric-value').value = '';
    toast('Metric tracked!');
    loadAppData();
  }
  async function loadMetrics() {
    try {
      const data = await api('/metrics/summary');
      const el = document.getElementById('metrics-summary');
      if (el) el.innerHTML = data.length ? data.map(m => `<div class="flex justify-between py-2"><span class="font-medium">${m.name}</span><span class="font-bold" style="color: #00bed0;">${Math.round(m.avg_val*100)/100}</span></div>`).join('') : '<p class="text-sm opacity-60">No metrics yet</p>';
    } catch(e) {}
  }

  // ─── Scroll Reveal Animation ──────────────────────────────
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    updateUI();
  });

  // Keyboard support for auth
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { closeAuth(); closeCreateModal(); }
  });
</script>
</body>
</html>"""
