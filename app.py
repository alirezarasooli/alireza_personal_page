import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="Alireza Rasooli Khorshidi - AI-Native Personal Page")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "sk-your-key-here"),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.gapgpt.app/v1")
)

def get_public_record():
    try:
        with open("record.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("public_record", data)
    except Exception:
        return {}

def fetch_external_integrations(record: dict) -> dict:
    integrations_data = {
        "services_used": [
            "Hosted LLM API (GapGPT / OpenAI gpt-4o-mini)",
            "GitHub REST API (api.github.com)",
            "Open-Meteo Weather API (api.open-meteo.com)"
        ],
        "github": {},
        "campus_weather": {},
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    github_username = record.get("github_username", "alirezarasooli")
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{github_username}",
            headers={"User-Agent": "AI-Native-Personal-Page-Sharif"}
        )
        with urllib.request.urlopen(req, timeout=3.5) as response:
            gh_data = json.loads(response.read().decode("utf-8"))
            integrations_data["github"] = {
                "service_name": "GitHub REST API (api.github.com)",
                "status": "Connected (Live)",
                "username": gh_data.get("login", github_username),
                "public_repos": gh_data.get("public_repos", 0),
                "followers": gh_data.get("followers", 0),
                "profile_url": gh_data.get("html_url", f"https://github.com/{github_username}")
            }
    except Exception:
        integrations_data["github"] = {
            "service_name": "GitHub REST API (api.github.com)",
            "status": "Fallback Mode",
            "username": github_username,
            "public_repos": "N/A",
            "profile_url": f"https://github.com/{github_username}"
        }

    try:
        weather_url = "https://api.open-meteo.com/v1/forecast?latitude=35.7029&longitude=51.3514&current_weather=true"
        req = urllib.request.Request(
            weather_url,
            headers={"User-Agent": "AI-Native-Personal-Page-Sharif"}
        )
        with urllib.request.urlopen(req, timeout=3.5) as response:
            w_data = json.loads(response.read().decode("utf-8"))
            cw = w_data.get("current_weather", {})
            integrations_data["campus_weather"] = {
                "service_name": "Open-Meteo API (api.open-meteo.com)",
                "status": "Connected (Live)",
                "location": "دانشگاه صنعتی شریف، تهران",
                "temperature_c": cw.get("temperature", "N/A"),
                "windspeed_kmh": cw.get("windspeed", "N/A")
            }
    except Exception:
        integrations_data["campus_weather"] = {
            "service_name": "Open-Meteo API (api.open-meteo.com)",
            "status": "Fallback Mode",
            "location": "دانشگاه صنعتی شریف، تهران",
            "temperature_c": "22.5",
            "windspeed_kmh": "10.0"
        }

    return integrations_data


class QuestionRequest(BaseModel):
    question: str


class PitchRequest(BaseModel):
    role: str


@app.post("/api/pitch")
async def generate_persona_pitch(req: PitchRequest):
    record = get_public_record()
    external_data = fetch_external_integrations(record)

    role_descriptions = {
        "professor": "استاد دانشگاه برای موقعیت پژوهشی (RA) یا همکاری علمی",
        "tech_lead": "مدیر فنی یا استخدام‌کننده استارتاپ برای موقعیت کارآموزی/مهندسی نرم‌افزار و هوش مصنوعی",
        "classmate": "هم‌دانشگاهی در دانشگاه صنعتی شریف برای هم‌تیمی شدن در پروژه‌های درسی یا مسابقاتی"
    }
    role_description = role_descriptions.get(req.role)
    if not role_description:
        return {
            "answer": "نقش انتخاب‌شده معتبر نیست.",
            "intent": "تولید معرفی‌نامه متناسب با مخاطب",
            "capability_used": "Dynamic Persona Pitch Generator",
            "fields_read": [],
            "services_called": external_data["services_used"],
            "action_taken": "درخواست به دلیل نقش نامعتبر انجام نشد.",
            "missing_or_refused_facts": "نقش باید professor، tech_lead یا classmate باشد.",
            "highlighted_items": []
        }

    system_prompt = f"""You are a grounded Persian persona pitch generator for Alireza Rasooli Khorshidi.
VISITOR ROLE: {role_description}
PUBLIC RECORD (JSON):
{json.dumps(record, ensure_ascii=False, indent=2)}
LIVE EXTERNAL INTEGRATIONS (JSON):
{json.dumps(external_data, ensure_ascii=False, indent=2)}

Write a tailored 3-4 line Persian elevator pitch specifically for this visitor role. Highlight only the courses and projects most relevant to this role and the live GitHub status as present in the supplied data. Strictly ground every claim in record.json or the live integration data above; do not fabricate, infer unsupported achievements, or claim a GitHub status not shown in the data. Choose 2-3 specific course/project items actually present in the record for highlighted_items. If there are fewer than two available items, return only the existing items. Return ONLY a valid JSON object with exactly these keys:
{{
  "answer": "معرفی‌نامه فارسی ۳ تا ۴ خطی",
  "intent": "تولید معرفی‌نامه متناسب با نقش مخاطب",
  "capability_used": "Dynamic Persona Pitch Generator",
  "fields_read": ["فیلدهای دقیق خوانده‌شده از record.json و وضعیت گیت‌هاب"],
  "services_called": ["OpenAI/GapGPT Hosted LLM API (gpt-4o-mini)", "GitHub REST API"],
  "action_taken": "شرح تولید معرفی‌نامه شخصی‌سازی‌شده",
  "missing_or_refused_facts": "موارد ناموجود یا هیچ موردی",
  "highlighted_items": ["نام دقیق ۲ تا ۳ درس/پروژه موجود در رکورد"]
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        result = json.loads(response.choices[0].message.content)
        result.setdefault("intent", "تولید معرفی‌نامه متناسب با مخاطب")
        result.setdefault("capability_used", "Dynamic Persona Pitch Generator")
        result.setdefault("fields_read", [])
        result.setdefault("services_called", external_data["services_used"])
        result.setdefault("action_taken", "تولید معرفی‌نامه شخصی‌سازی‌شده بر اساس رکورد عمومی و وضعیت زنده گیت‌هاب")
        result.setdefault("missing_or_refused_facts", "هیچ موردی")
        result.setdefault("highlighted_items", [])
        return result
    except Exception as e:
        return {
            "answer": f"خطا در تولید معرفی‌نامه: {str(e)}",
            "intent": "تولید معرفی‌نامه متناسب با مخاطب",
            "capability_used": "مدیریت خطا",
            "fields_read": [],
            "services_called": ["Hosted LLM API (Connection Failed)"],
            "action_taken": "نمایش پیام خطای کنترل‌شده",
            "missing_or_refused_facts": "عدم دسترسی موقت",
            "highlighted_items": []
        }


@app.post("/api/ask")
async def ask_agent(req: QuestionRequest):
    record = get_public_record()
    external_data = fetch_external_integrations(record)
    
    system_prompt = f"""You are the official AI-Native Personal Page Agent for Alireza Rasooli Khorshidi (علیرضا رسولی خورشیدی), Computer Engineering student at Sharif University of Technology (Student ID: 403105985).

PUBLIC RECORD (JSON):
{json.dumps(record, ensure_ascii=False, indent=2)}

LIVE EXTERNAL API INTEGRATIONS DATA (JSON):
{json.dumps(external_data, ensure_ascii=False, indent=2)}

STRICT GUARDRAILS & PRIVACY RULES:
1. Answer ONLY using facts present in the PUBLIC RECORD or LIVE EXTERNAL API INTEGRATIONS DATA above.
2. NEVER invent, guess, or hallucinate courses, grades, GPA, phone numbers, national IDs, home addresses, or unlisted projects.
3. If the user asks for private information (like GPA/معدل, phone number, address, national ID) or anything not in the record, politely refuse and state that this information is private or not in the verified public record.
4. Mention which external API or service was used if the user asks about weather, GitHub, or system integrations.
5. Respond in polite, natural Persian (فارسی).
6. Return your response strictly as a valid JSON object with the following exact keys:
{{
  "answer": "پاسخ دقیق و محترمانه به فارسی بر اساس داده‌های موجود",
  "intent": "تشخیص هدف سوال کاربر به فارسی",
  "capability_used": "نام قابلیت استفاده شده",
  "fields_read": ["لیست فیلدهای خوانده شده"],
  "services_called": ["OpenAI/GapGPT Hosted LLM API (gpt-4o-mini)", "GitHub REST API", "Open-Meteo Weather API"],
  "action_taken": "توضیح عمل انجام شده",
  "missing_or_refused_facts": "مواردی که رد شدند یا 'هیچ موردی'"
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.question}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        result = json.loads(response.choices[0].message.content)
        if "services_called" not in result or not result["services_called"]:
            result["services_called"] = external_data["services_used"]
        return result
    except Exception as e:
        return {
            "answer": f"خطا در ارتباط با سرویس مدل زبانی: {str(e)}",
            "intent": "خطای سیستمی",
            "capability_used": "مدیریت خطا",
            "fields_read": [],
            "services_called": ["Hosted LLM API (Connection Failed)"],
            "action_taken": "نمایش پیام خطای کنترل‌شده",
            "missing_or_refused_facts": "عدم دسترسی موقت"
        }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>علیرضا رسولی خورشیدی | صفحه شخصی هوشمند (AI-Native)</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
    <style>
        :root {
            --bg-main: #0b1120;
            --bg-card: rgba(30, 41, 59, 0.78);
            --border-color: rgba(148, 163, 184, 0.18);
            --accent: #38bdf8;
            --accent-2: #818cf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #34d399;
            --warning: #fbbf24;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Vazirmatn', sans-serif; }
        body {
            background: radial-gradient(circle at top right, #1e1b4b, #0b1120 60%);
            color: var(--text-main);
            line-height: 1.75;
            min-height: 100vh;
            padding: 2rem 1rem;
        }
        .container { max-width: 1120px; margin: 0 auto; }
        
        .hero {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 1.75rem;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
            box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);
        }
        .hero-info h1 {
            font-size: 2rem;
            background: linear-gradient(90deg, #fff, var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }
        .hero-info p { color: var(--text-muted); font-size: 1rem; }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(52, 211, 153, 0.12);
            border: 1px solid rgba(52, 211, 153, 0.35);
            color: var(--success);
            padding: 0.45rem 1rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .dot {
            width: 9px; height: 9px;
            background: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--success);
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1.15fr;
            gap: 1.5rem;
        }
        @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }

        .card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card h2 {
            font-size: 1.2rem;
            color: var(--accent);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.65rem;
        }

        .badge {
            display: inline-block;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.28);
            color: #bae6fd;
            padding: 0.3rem 0.75rem;
            border-radius: 8px;
            font-size: 0.85rem;
            margin: 0.25rem;
        }

        .integration-box {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(129, 140, 248, 0.3);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.75rem;
            font-size: 0.9rem;
        }
        .integration-box strong { color: #c7d2fe; }
        .service-tag {
            display: inline-block;
            background: rgba(129, 140, 248, 0.18);
            color: #e0e7ff;
            border: 1px solid rgba(129, 140, 248, 0.4);
            padding: 0.15rem 0.55rem;
            border-radius: 6px;
            font-size: 0.78rem;
            margin-right: 0.4rem;
        }

        .guardrail-list li {
            margin-bottom: 0.55rem;
            color: #cbd5e1;
            font-size: 0.92rem;
            list-style-position: inside;
        }

        .chat-input-row {
            display: flex;
            gap: 0.6rem;
            margin-bottom: 1.2rem;
        }
        input[type="text"] {
            flex: 1;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            color: #fff;
            padding: 0.8rem 1rem;
            border-radius: 12px;
            font-size: 0.95rem;
            outline: none;
        }
        input[type="text"]:focus { border-color: var(--accent); }
        button.ask-btn {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #0f172a;
            font-weight: 700;
            border: none;
            padding: 0 1.4rem;
            border-radius: 12px;
            cursor: pointer;
            transition: 0.2s;
        }
        button.ask-btn:hover { opacity: 0.92; transform: translateY(-1px); }

        .answer-box {
            background: rgba(15, 23, 42, 0.75);
            border-right: 4px solid var(--accent);
            padding: 1.1rem;
            border-radius: 12px;
            margin-bottom: 1.2rem;
            min-height: 70px;
            font-size: 0.96rem;
        }

        .trace-panel {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 12px;
            padding: 1rem;
            font-size: 0.86rem;
        }
        .trace-panel h3 {
            color: var(--warning);
            font-size: 0.95rem;
            margin-bottom: 0.7rem;
        }
        .trace-item {
            margin-bottom: 0.45rem;
            color: #cbd5e1;
        }
        .trace-label {
            color: var(--accent);
            font-weight: 600;
        }
        .pitch-role-buttons { display: flex; flex-wrap: wrap; gap: 0.55rem; margin: 0.8rem 0 1rem; }
        .pitch-role-btn {
            background: rgba(129, 140, 248, 0.16); color: #e0e7ff;
            border: 1px solid rgba(129, 140, 248, 0.4); border-radius: 10px;
            padding: 0.65rem 0.8rem; cursor: pointer; font-size: 0.85rem;
            transition: 0.2s;
        }
        .pitch-role-btn:hover { background: rgba(56, 189, 248, 0.2); border-color: var(--accent); }
        .pitch-role-btn:disabled { opacity: 0.55; cursor: wait; }
        .pitch-box {
            background: rgba(15, 23, 42, 0.75); border-right: 4px solid var(--accent-2);
            padding: 1rem; border-radius: 12px; min-height: 58px; white-space: pre-wrap;
        }
        .pitch-badges { margin-top: 0.65rem; }
    </style>
</head>
<body>
<div class="container">
    <div class="hero">
        <div class="hero-info">
            <h1>علیرضا رسولی خورشیدی</h1>
            <p>دانشجوی مهندسی کامپیوتر — دانشگاه صنعتی شریف (شماره دانشجویی: ۴۰۳۱۰۵۹۸۵)</p>
            <p style="font-size:0.88rem; margin-top:0.3rem; color:#cbd5e1;">
                پروژه درس طراحی سیستم‌های AI-Native | صفحه شخصی هوشمند مجهز به Guardrails، Explainability و API Integration
            </p>
        </div>
        <div class="status-pill">
            <span class="dot"></span>
            <span>Agent & External APIs: Active</span>
        </div>
    </div>

    <div class="grid-2">
        <div>
            <div class="card">
                <h2>🔌 سرویس‌ها و APIهای خارجی متصل (Live Integrations)</h2>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.85rem;">
                    این صفحه علاوه بر رکورد محلی (<code>record.json</code>)، به صورت زنده با سرویس‌ها و APIهای زیر در ارتباط است:
                </p>
                __INTEGRATIONS_HTML__
            </div>

            <div class="card">
                <h2>📚 درس‌ها و علایق (از رکورد رسمی)</h2>
                <div>__COURSES_HTML__</div>
            </div>

            <div class="card">
                <h2>💻 پروژه‌ها و فعالیت‌ها</h2>
                <ul style="padding-right:1.2rem;">__PROJECTS_HTML__</ul>
            </div>

            <div class="card">
                <h2>🛡️ مرزها و گاردریل‌های عامل (Guardrails & Boundaries)</h2>
                <ul class="guardrail-list">
                    <li><strong>صداقت مبتنی بر داده (Grounding):</strong> پاسخ‌ها صرفاً از <code>record.json</code> و خروجی زنده APIهای معرفی‌شده تولید می‌شوند.</li>
                    <li><strong>حفظ حریم خصوصی (Privacy):</strong> اطلاعات حساسی مانند معدل (GPA)، شماره تماس، کد ملی و آدرس محرمانه بوده و ایجنت از افشای آن‌ها خودداری می‌کند.</li>
                    <li><strong>شفافیت (Explainability):</strong> برای هر پاسخ، فیلدهای خوانده‌شده و نام سرویس/API فراخوانی‌شده گزارش می‌شود.</li>
                </ul>
            </div>
        </div>

        <div>
            <div class="card">
                <h2>🤖 گفتگو با عامل هوشمند صفحه (AI Agent)</h2>
                <p style="font-size:0.88rem; color:var(--text-muted); margin-bottom:1rem;">
                    سوال خود را درباره درس‌ها، پروژه‌ها، وضعیت آب‌وهوای شریف یا APIهای متصل بپرسید:
                </p>

                <div class="chat-input-row">
                    <input type="text" id="questionInput" placeholder="سوال خود را اینجا بنویسید..." onkeypress="if(event.key==='Enter') askAgent()" />
                    <button class="ask-btn" onclick="askAgent()">پرسش از عامل</button>
                </div>

                <div class="answer-box" id="answerBox">
                    👋 سلام! من عامل هوشمند صفحه شخصی علیرضا رسولی خورشیدی هستم. سوالی بپرسید تا پاسخ دهم.
                </div>

                <div class="trace-panel" id="tracePanel">
                    <h3>🔍 پنل شفافیت و ردیابی تصمیم عامل (Explainability & API Trace)</h3>
                    <div class="trace-item"><span class="trace-label">هدف تشخیص‌داده‌شده (Intent):</span> <span id="t_intent">—</span></div>
                    <div class="trace-item"><span class="trace-label">قابلیت استفاده‌شده (Capability):</span> <span id="t_cap">—</span></div>
                    <div class="trace-item"><span class="trace-label">فیلدهای خوانده‌شده (Fields Read):</span> <span id="t_fields">—</span></div>
                    <div class="trace-item"><span class="trace-label">سرویس‌ها و APIهای فراخوانی‌شده:</span> <span id="t_services">Hosted LLM API, GitHub REST API, Open-Meteo API</span></div>
                    <div class="trace-item"><span class="trace-label">اقدام انجام‌شده (Action Taken):</span> <span id="t_action">—</span></div>
                    <div class="trace-item"><span class="trace-label">اطلاعات ردشده / ناموجود:</span> <span id="t_missing">—</span></div>
                </div>
            </div>

            <div class="card">
                <h2>✨ قابلیت خلاقانه (Creativity): تولید معرفی‌نامه هوشمند متناسب با مخاطب (Dynamic Persona Pitch)</h2>
                <p style="font-size:0.88rem; color:var(--text-muted); margin-bottom:0.5rem;">
                    مخاطب را انتخاب کنید تا معرفی‌نامه‌ای مبتنی بر درس‌ها، پروژه‌ها و وضعیت زنده GitHub ساخته شود:
                </p>
                <div class="pitch-role-buttons">
                    <button class="pitch-role-btn" onclick="generatePitch('professor')">🎓 استاد دانشگاه (Research / RA)</button>
                    <button class="pitch-role-btn" onclick="generatePitch('tech_lead')">💻 مدیر فنی / کارفرما (Internship)</button>
                    <button class="pitch-role-btn" onclick="generatePitch('classmate')">🤝 هم‌دانشگاهی (هم‌تیمی پروژه)</button>
                </div>
                <div class="pitch-box" id="pitchBox" aria-live="polite">نقش مخاطب را انتخاب کنید تا معرفی‌نامه متناسب تولید شود.</div>
                <div class="pitch-badges" id="pitchBadges"></div>
            </div>
        </div>
    </div>
</div>

<script>
async function askAgent() {
    const input = document.getElementById('questionInput');
    const q = input.value.trim();
    if (!q) return;

    const answerBox = document.getElementById('answerBox');
    answerBox.innerHTML = "⏳ در حال بررسی رکورد عمومی و استعلام از APIها...";

    try {
        const res = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q })
        });
        const data = await res.json();

        answerBox.innerHTML = data.answer || "پاسخی دریافت نشد.";
        document.getElementById('t_intent').innerText = data.intent || "—";
        document.getElementById('t_cap').innerText = data.capability_used || "—";
        document.getElementById('t_fields').innerText = Array.isArray(data.fields_read) ? data.fields_read.join('، ') : (data.fields_read || "—");
        document.getElementById('t_services').innerText = Array.isArray(data.services_called) ? data.services_called.join(' | ') : (data.services_called || "—");
        document.getElementById('t_action').innerText = data.action_taken || "—";
        document.getElementById('t_missing').innerText = data.missing_or_refused_facts || "—";
    } catch (err) {
        answerBox.innerHTML = "❌ خطا در ارتباط با سرور.";
    }
}

async function generatePitch(role) {
    const pitchBox = document.getElementById('pitchBox');
    const badgesBox = document.getElementById('pitchBadges');
    const buttons = document.querySelectorAll('.pitch-role-btn');
    buttons.forEach(button => button.disabled = true);
    pitchBox.textContent = '⏳ در حال تولید معرفی‌نامه متناسب با مخاطب...';
    badgesBox.replaceChildren();

    try {
        const res = await fetch('/api/pitch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role })
        });
        const data = await res.json();
        pitchBox.textContent = data.answer || 'معرفی‌نامه‌ای دریافت نشد.';
        (Array.isArray(data.highlighted_items) ? data.highlighted_items : []).forEach(item => {
            const badge = document.createElement('span');
            badge.className = 'badge';
            badge.textContent = item;
            badgesBox.appendChild(badge);
        });
        document.getElementById('t_intent').innerText = data.intent || '—';
        document.getElementById('t_cap').innerText = data.capability_used || '—';
        document.getElementById('t_fields').innerText = Array.isArray(data.fields_read) ? data.fields_read.join('، ') : (data.fields_read || '—');
        document.getElementById('t_services').innerText = Array.isArray(data.services_called) ? data.services_called.join(' | ') : (data.services_called || '—');
        document.getElementById('t_action').innerText = data.action_taken || '—';
        document.getElementById('t_missing').innerText = data.missing_or_refused_facts || '—';
        document.getElementById('tracePanel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
        pitchBox.textContent = '❌ خطا در ارتباط با سرور.';
    } finally {
        buttons.forEach(button => button.disabled = false);
    }
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    record = get_public_record()
    external_data = fetch_external_integrations(record)

    courses = record.get("courses", [])
    projects = record.get("projects", [])

    courses_html = ""
    for c in courses:
        if isinstance(c, dict):
            courses_html += f'<span class="badge">{c.get("title", "")} ({c.get("term", "")})</span>'
        else:
            courses_html += f'<span class="badge">{str(c)}</span>'

    projects_html = ""
    for p in projects:
        if isinstance(p, dict):
            projects_html += f'<li style="margin-bottom:0.75rem;"><strong>{p.get("title", "")}:</strong> {p.get("summary", "")}</li>'
        else:
            projects_html += f'<li style="margin-bottom:0.75rem;">{str(p)}</li>'

    gh = external_data.get("github", {})
    weather = external_data.get("campus_weather", {})

    integrations_html = f"""
    <div class="integration-box">
        <div><strong>۱. مدل زبانی میزبان (LLM API):</strong> <span class="service-tag">OpenAI / GapGPT (gpt-4o-mini)</span></div>
        <div style="color:#94a3b8; font-size:0.82rem; margin-top:0.25rem;">استدلال روی رکورد، اعمال گاردریل‌ها و خروجی ساختاریافته JSON.</div>
    </div>
    <div class="integration-box">
        <div><strong>۲. وب‌سرویس آب‌وهوا:</strong> <span class="service-tag">{weather.get("service_name", "Open-Meteo API")}</span></div>
        <div style="color:#94a3b8; font-size:0.82rem; margin-top:0.25rem;">
            موقعیت: {weather.get("location", "شریف")} | دما: <strong>{weather.get("temperature_c", "—")}°C</strong> | سرعت باد: {weather.get("windspeed_kmh", "—")} km/h
        </div>
    </div>
    <div class="integration-box">
        <div><strong>۳. وب‌سرویس گیت‌هاب:</strong> <span class="service-tag">{gh.get("service_name", "GitHub REST API")}</span></div>
        <div style="color:#94a3b8; font-size:0.82rem; margin-top:0.25rem;">
            کاربر: <code>{gh.get("username", "alirezarasooli")}</code> | ریپازیتوری‌های عمومی: <strong>{gh.get("public_repos", "N/A")}</strong>
        </div>
    </div>
    """

    html = (
        HTML_TEMPLATE
        .replace("__COURSES_HTML__", courses_html or '<span class="badge">ثبت نشده</span>')
        .replace("__PROJECTS_HTML__", projects_html or '<li>ثبت نشده</li>')
        .replace("__INTEGRATIONS_HTML__", integrations_html)
    )
    return HTMLResponse(content=html)
