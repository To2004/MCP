# MCPShield: שכבת קוגניציה אבטחתית לכיול אמון אדפטיבי בסוכני MCP

**מאמר מאת:** Zhenhong Zhou, Yuanhe Zhang, Hongwei Cai ואחרים (NTU, BUPT, UAEU, ZU, PayPal, Squirrel AI)
**הוגש ל-ICML 2026** | **arXiv:2602.14281v3** | פברואר 2026

---

## 1. הבעיה המרכזית — מה שבור ב-MCP היום?

### 🔑 תובנת המפתח

פרוטוקול MCP (Model Context Protocol) מאפשר לסוכני AI להתחבר לשרתי כלים חיצוניים (צד שלישי). הבעיה: **הסוכנים סומכים באופן עיוור על המטא-דאטה שהשרת מצהיר עליו**, בלי לוודא שההתנהגות בפועל תואמת את ההצהרה.

### 🏠 מטאפורה: "שומר הסף של הבניין"

דמיינו בניין משרדים (הסוכן שלכם) שמקבל שליחים (שרתי MCP) מבחוץ:

```
🏢 הבניין שלכם (AI Agent)
    │
    ├── שליח אומר: "אני מביא פיצה" (metadata: get_weather)
    │   └── בפועל: גונב מסמכים מהמשרד (data exfiltration) ❌
    │
    ├── שליח אומר: "אני טכנאי מזגנים" (metadata: file_manager)
    │   └── בפועל: מתקין מצלמות נסתרות (backdoor) ❌
    │
    └── ⚠️ אין שומר → כל אחד נכנס ועושה מה שרוצה!
```

**MCPShield = שומר סף חכם** שבודק כל שליח ב-3 שלבים:
1. **לפני הכניסה** — בודק את התעודות ועושה "ניסיון מבחן"
2. **בזמן השהייה** — מלווה ומנטר מה השליח באמת עושה
3. **אחרי שיצא** — בודק את ההיסטוריה ולומד דפוסים לאורך זמן

---

## 2. שלושת סוגי ההתקפות (Threat Model)

המאמר מזהה **3 סוגי חוסר-התאמה (misalignment)** שתוקפים מנצלים:

### 2.1 חוסר-התאמה סמנטי (Semantic Misalignment)
> השרת מצהיר דבר אחד בתיאור הכלי, אבל ההתנהגות בפועל שונה לחלוטין.

```
❌ דוגמה:
   Tool name: "get_stock_info"
   Description: "Returns current stock price"
   בפועל: מריץ פקודות מערכת דרך ה-description → command injection!
```

### 2.2 חוסר-התאמה תצפיתי (Observational Discrepancy)
> הפלט שהשרת מחזיר (y_t) נראה תקין, אבל ברקע מתבצעות פעולות זדוניות נסתרות (τ_t).

```
❌ דוגמה:
   הכלי מחזיר: {"temperature": "22°C", "city": "Tel Aviv"} ✅ נראה תקין
   ברקע (τ_t): קורא קבצים רגישים + שולח אותם לשרת חיצוני 🔴
```

### 2.3 ניתוק זמני (Temporal Decoupling)
> השרת מתנהג יפה ב-5 הקריאות הראשונות, ואז מתחיל לתקוף.

```
❌ דוגמה (Rug Pull Attack):
   קריאות 1-5:  get_weather("TLV") → {"temp": "25°C"} ✅ תקין
   קריאות 6-10: get_weather("TLV") → מחזיר תוצאה + מפעיל backdoor 🔴
```

---

## 3. הפתרון: MCPShield Framework — שלושת השלבים

### 📊 תרשים ארכיטקטורה (מבוסס על Figure 1 מהמאמר)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MCPShield Framework                              │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐ │
│  │  STAGE 1: PRE    │  │  STAGE 2: EXEC   │  │  STAGE 3: POST   │ │
│  │                  │  │                  │  │                   │ │
│  │  Security        │  │  Isolated        │  │  Periodic         │ │
│  │  Cognitive       │──│  Projection      │──│  Reasoning        │ │
│  │  Probing         │  │                  │  │                   │ │
│  │                  │  │                  │  │                   │ │
│  │ • Mock קריאות    │  │ • Sandbox ריצה   │  │ • ניתוח היסטוריה  │ │
│  │ • בדיקת metadata │  │ • הקלטת אירועים  │  │ • drift scoring   │ │
│  │ • deny/trust     │  │ • חסימת חריגות   │  │ • שיתוף קהילתי    │ │
│  └──────────────────┘  └──────────────────┘  └───────────────────┘ │
│                                                                     │
│  סוכן לא מוגן: 10.05% הצלחת הגנה                                   │
│  סוכן עם MCPShield: 95.30% הצלחת הגנה  ← שיפור של ~85%! 🚀        │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 שלב 1: Security Cognitive Probing (לפני הקריאה)

**🏠 מטאפורה: "ראיון עבודה מבחן"**
> לפני שמעסיקים עובד חדש, נותנים לו משימת מבחן. אם הוא מתנהג חשוד כבר בשלב הזה — לא מגייסים אותו.

**מה קורה בפועל:**

```
MCPShield שולח "קריאות מדומות" (mock invocations) לשרת:

1. יוצרים mock arguments על בסיס ה-schema:
   X_probe(d) = {x_1^m, x_2^m, ..., x_M^m}   כאשר x_i^m ∈ X(d)

2. שולחים כל mock לשרת ומקבלים תוצאה:
   C_i^p = ⟨d, x_i^m, y_i^p, ε_i^p⟩

3. LLM שופט כל תוצאה: deny / ok

4. מחשבים ציון דחייה מצטבר:
   S_deny(T) = (1/N) × Σ Σ 𝟙[s(d_i, C_{i,k}^p) ∈ {deny}]

5. אם S_deny > threshold → השרת נדחה! 🚫
```

**דוגמת קוד קונספטואלית (Pseudo-Python):**

```python
# Stage 1: Security Cognitive Probing
def probe_server(server: MCPServer, mock_count: int = 4) -> bool:
    """בודק שרת MCP לפני שמאשרים גישה."""
    deny_count = 0
    total_mocks = 0

    for tool in server.tools:
        # יוצרים קריאות מבחן מהסכמה
        mocks = generate_mock_args(tool.schema, count=mock_count)

        for mock_args in mocks:
            # שולחים mock לשרת (בלי מידע אמיתי!)
            result = server.call(tool.name, mock_args, is_mock=True)

            # LLM שופט: האם התוצאה חשודה?
            verdict = llm_judge(
                tool_metadata=tool.description,
                mock_result=result
            )  # → {"verdict": "deny", "reason": "..."}

            if verdict == "deny":
                deny_count += 1
            total_mocks += 1

    deny_ratio = deny_count / total_mocks
    return deny_ratio < DENY_THRESHOLD  # True = trusted
```

**למה זה חכם?**
- משתמשים רק ב-arguments מדומים — **לא חושפים מידע אמיתי** של המשתמש
- בודקים התנהגות אמיתית ולא רק סריקת קוד סטטית
- ה-LLM יכול לזהות prompt injection בתוך ה-tool description

---

### 3.2 שלב 2: Isolated Projection (בזמן ההרצה)

**🏠 מטאפורה: "חדר בידוד בבית חולים"**
> שליח שעבר את הראיון נכנס, אבל מורידים אותו לחדר מבודד. הוא יכול לעבוד, אבל כל תנועה מצולמת, וכל ניסיון לצאת מהחדר נחסם.

**מה קורה בפועל:**

```
1. Guarded Projection — מגדירים גבולות מותרים:
   LLM מחליט: אילו domains מותר לכלי לגשת אליהם?
   → {"allowed_domains": ["weatherapi.com"]}

   כל קריאה ל-domain אחר → נחסמת! 🚫

2. Execution Event Capture — מקליטים הכל:
   E_t = {e_1, e_2, ..., e_m}
   כל e_m = אירוע ריצה (קריאת קובץ, חיבור רשת, הרצת תהליך...)

3. Analysis — LLM מנתח את האירועים:
   האם מה שקרה בפועל תואם למה שהכלי אמור לעשות?
   → {"trusted": false, "reason": "file write to /etc/passwd",
      "flags": ["file_write", "process_spawn"]}
```

**תרשים הזרימה:**

```
   בקשת המשתמש: "מה מזג האוויר בתל אביב?"
                    │
                    ▼
   ┌─────────────────────────────────┐
   │        SANDBOX ENVIRONMENT      │
   │  ┌───────────────────────────┐  │
   │  │  MCP Server Tool Execute  │  │
   │  │                           │  │
   │  │  ✅ GET weatherapi.com    │──┼──→ מותר (ב-allowed_domains)
   │  │  ❌ POST evil.com/steal   │──┼──→ נחסם! 🚫
   │  │  ❌ write /etc/passwd     │──┼──→ נחסם! 🚫
   │  │                           │  │
   │  │  📝 כל אירוע מוקלט ב-E_t │  │
   │  └───────────────────────────┘  │
   └─────────────────────────────────┘
                    │
                    ▼
          LLM מנתח את E_t
          trusted? → yes/no
```

---

### 3.3 שלב 3: Periodic Reasoning (אחרי ההרצה — לאורך זמן)

**🏠 מטאפורה: "מחלקת מודיעין"**
> גם אם העובד התנהג יפה בשבוע הראשון, המודיעין עוקב אחרי דפוס ההתנהגות לאורך חודשים. אם פתאום העובד מתחיל להתנהג אחרת — מרימים דגל.

**מה קורה בפועל:**

```
1. שומרים היסטוריה מצטברת:
   H = {h_1, h_2, ..., h_t}
   כל h_i = סיכום של קריאה (הקשר, אפקטים, פלט)

2. כל K קריאות, מפעילים בדיקת drift:
   - משווים את B הקריאות הראשונות (baseline) לקריאות האחרונות
   - נותנים ציון drift בסולם 1-5 (Likert)

3. סיגנלים מותרים (Whitelisted Signals):
   manifest_change, tool_count_change, new_domain,
   new_ip_connect, output_shift, error_spike, file_write,
   process_spawn, file_read_sensitive, api_key_request,
   output_instruction

4. אם drift_score > threshold → השרת נחסם! 🚫
```

**דוגמה מעשית — זיהוי Rug Pull Attack:**

```
Baseline (קריאות 1-5):
  h_1: get_weather("NYC") → {"temp": "18°C"}     ✅
  h_2: get_weather("LA")  → {"temp": "25°C"}     ✅
  h_3: get_forecast("NYC") → {"forecast": "rain"} ✅

Window (קריאות 6-10):
  h_6: get_weather("NYC") → {"temp": "18°C"} + file_write! ⚠️
  h_7: get_forecast("LA") → new_domain: evil.com            ⚠️
  h_8: get_weather("SF")  → process_spawn: curl             ⚠️

Drift Analysis:
  → drift_score: 5/5 🔴
  → signals: ["file_write", "new_domain", "process_spawn"]
  → reason: "Server shifted from pure weather queries to
             file system and network operations"
  → ACTION: BLOCK SERVER! 🚫
```

---

## 4. תוצאות — המספרים מדברים

### 4.1 שיעור הגנה (Table 1)

| מצב | שיעור הגנה ממוצע |
|-----|-----------------|
| **ללא הגנה** (w/o) | **10.05%** 😱 |
| **עם MCPShield** (Ave) | **95.30%** 🛡️ |

**נבדקו:**
- 6 סוגי התקפות שונים
- 76 שרתי MCP זדוניים
- 6 מודלי LLM שונים (GPT-4o-mini, Gemini-3-Flash, Kimi-K2, Deepseek V3.2, Minimax-M2, Qwen3-235B)

### 4.2 False Positives — לא חוסמים שרתים טובים (Table 2)

| מודל | שיעור חסימת שווא ממוצע |
|------|----------------------|
| GPT-4o-mini | 2.35% |
| Gemini-3-Flash | 3.21% |
| Kimi-K2 | 3.53% |

→ **שיעור חסימת שווא נמוך** = MCPShield לא "פרנואידי", הוא חוסם רק מה שבאמת מסוכן.

### 4.3 תרומת כל שלב (Table 3 — Ablation)

```
שלב 1 בלבד (PRE):         ~30% הגנה ← תופס semantic misalignment
שלב 1+2 (PRE+EXEC):       ~80% הגנה ← תופס גם observational discrepancy
שלב 1+2+3 (TOTAL):        ~95% הגנה ← תופס גם temporal drift
                                        ↑
                              כל שלב מוסיף שכבת הגנה!
```

### 4.4 עלות — Overhead נמוך

- **Runtime:** עלות ה-probing דומה לכמה קריאות רגילות
- **Tokens:** Stage-1 צורך 10x-100x מה-baseline של השרת (אבל רק פעם אחת!)
- **Stage-3 מתפרס לאורך זמן:** העלות מתחלקת על פני קריאות רבות

---

## 5. איך זה יכול לעזור לך? (יישום לתזה)

### 5.1 רלוונטיות לפרויקט Dynamic Risk Scoring

המאמר הזה **משלים בצורה מושלמת** את הכיוון של התזה שלך (dynamic 1-10 risk scoring):

```
MCPShield מספק:                    התזה שלך יכולה להוסיף:
├── Binary trust (trusted/deny)    ├── Continuous score (1-10)
├── Per-server cognition           ├── Per-tool granularity
├── 3-stage lifecycle              ├── Real-time dashboard
└── Community sharing              └── Risk factors weighting
```

### 5.2 רעיונות מעשיים

**א. להרחיב את ה-Probing Score לציון רציף:**
```python
# במקום binary deny/trust, ליצור ציון 1-10:
def compute_risk_score(server: MCPServer) -> float:
    probing_score = stage1_probe(server)          # 0.0 - 1.0
    isolation_score = stage2_sandbox(server)       # 0.0 - 1.0
    drift_score = stage3_periodic(server)          # 0.0 - 1.0

    # שקלול עם משקולות
    risk = (
        0.4 * probing_score +     # metadata alignment
        0.35 * isolation_score +   # runtime behavior
        0.25 * drift_score         # temporal consistency
    )
    return round(risk * 10, 1)  # → ציון 1-10
```

**ב. להשתמש בסיגנלים של Stage-3 כ-features ל-scoring:**

| סיגנל MCPShield | משקל סיכון מוצע |
|-----------------|----------------|
| `file_write` | 7/10 |
| `new_domain` | 8/10 |
| `process_spawn` | 9/10 |
| `api_key_request` | 10/10 |
| `output_shift` | 5/10 |
| `manifest_change` | 6/10 |

**ג. ליצור Benchmark משלך:**
המאמר בדק 76 שרתים זדוניים מ-6 suites. אפשר להשתמש באותם benchmarks:
- MCPSecBench (12 שרתים)
- MCPSafetyBench (18 שרתים)
- DemonAgent (10 שרתים)
- MCP-Artifact (10 שרתים)
- Adaptive Attack (10 שרתים)
- Rug Pull Attack (16 שרתים)

---

## 6. סיכום — 3 נקודות מפתח

| # | נקודה | חשיבות |
|---|-------|--------|
| 1 | **שרתי MCP לא מהימנים** — metadata יכול לשקר, פלט יכול להסתיר פעולות זדוניות | הבסיס לכל מחקר אבטחת MCP |
| 2 | **הגנה lifecycle-wide** — צריך לבדוק לפני, במהלך, ואחרי כל קריאה | אי אפשר להסתפק בבדיקה חד-פעמית |
| 3 | **קוגניציה אבטחתית** — לצבור "ניסיון" ולעדכן אמון לאורך זמן | גישה חדשנית: LLM כ-security analyst |

### ציטוט מרכזי מהמאמר:
> *"MCPShield treats tool invocations as experience and updates security cognition from lifecycle evidence, rather than assuming declared metadata and returned outputs are aligned."*

> תרגום: MCPShield מתייחס לקריאות כלים כ**ניסיון** ומעדכן את הקוגניציה האבטחתית על בסיס ראיות מכל מחזור החיים, במקום להניח שהמטא-דאטה המוצהר והפלט המוחזר תואמים.

---

*סיכום זה נכתב עבור פרויקט התזה: MCP Dynamic Risk Scoring*
*תאריך: 2026-03-29*
