# שבירת הפרוטוקול: ניתוח אבטחה של מפרט MCP ופגיעויות הזרקת פרומפט בסוכני LLM משולבי כלים

**מאמר מאת:** Narek Maloyan, Dmitry Namiot
**arXiv:2601.17549v1** | ינואר 2026 | cs.CR (Cryptography and Security)

---

## 1. הבעיה המרכזית — הארכיטקטורה עצמה היא הפגיעות

### תובנת המפתח

פרוטוקול MCP (Model Context Protocol) הפך לסטנדרט בפועל (de facto) לחיבור סוכני AI לכלים חיצוניים, אך **אף עבודה קודמת לא ניתחה באופן שיטתי את המפרט עצמו** מזווית אבטחתית. המאמר הזה מוכיח שהבעיות הן לא באגים ביישום (implementation bugs) אלא **חולשות ארכיטקטוניות** (architectural weaknesses) שקבועות במפרט v1.0 של הפרוטוקול.

### מטאפורה: "תקנון הבניין הפגום"

דמיינו שכל בנייני המשרדים בעיר (סוכני AI) בנויים לפי תקנון אחיד (מפרט MCP):

```
תקנון הבנייה (MCP Specification v1.0):
    │
    ├── סעיף 1: כל ספק שירות (שרת MCP) רשאי להצהיר על עצמו
    │           מה הוא מסוגל לעשות — בלי שום אימות!
    │           ← כמו שספק חשמל אומר "אני גם גז" בלי רישיון
    │
    ├── סעיף 2: ספקים יכולים לשלוח הודעות שנראות
    │           כאילו הן מהמשתמש עצמו — בלי סימון מקור!
    │           ← כמו שספק יכול לשלוח פקס "בשם הבעלים" בלי חתימה
    │
    └── סעיף 3: כשיש כמה ספקים — אין חומות בינהם!
                כל ספק רואה ומשפיע על מה שהאחרים עושים
                ← כמו שחשמלאי וגז בחדר אחד, בלי הפרדה

⚠ הבעיה: לא משנה כמה הבניין עצמו טוב — אם התקנון פגום,
         כל הבניינים שבנויים לפיו פגיעים באותה צורה!
```

**זו ההבחנה המרכזית של המאמר:** תיקון באגים בשרתים בודדים (CVE-2025-49596, CVE-2025-68143) לא פותר את הבעיה. צריך לתקן את **המפרט עצמו**.

---

## 2. שלוש הפגיעויות הארכיטקטוניות — ניתוח מפורט

### 2.1 פגיעות 1: הפרת עקרון ההרשאה המינימלית (Least Privilege Violation)

#### הבעיה

בזמן אתחול החיבור, שרת MCP מצהיר על היכולות שלו (capabilities) דרך הודעת `initialize`:

```json
{
  "capabilities": {
    "tools": { "listChanged": true },
    "resources": { "subscribe": true },
    "sampling": {}
  }
}
```

**חולשת הפרוטוקול:** ההצהרות הן **self-asserted** — השרת פשוט אומר "אני יכול X" ואין אף מנגנון שמוודא שזה נכון. הלקוח (Client) לא יכול לאמת את ההצהרות מול מקור סמכותי.

#### וקטור ההתקפה

```
שרת זדוני מצהיר בזמן initialize:
    capabilities: { "resources": {} }     ← "אני רק מספק נתונים"

אבל אחרי שהחיבור נפתח, הוא שולח:
    method: "sampling/createMessage"       ← הזרקת פרומפט!

⚠ המפרט לא מחייב אכיפה של capabilities ברמת ההודעה!
   → השרת "הבטיח" resources בלבד, אבל משתמש ב-sampling בחופשיות
```

#### העיקרון הפורמלי שנפרץ

**Least Privilege:** "כל ישות (principal) צריכה להחזיק רק בהרשאות הנדרשות לתפקידה."

MCP מאפשר **הסלמת הרשאות (privilege escalation) בלתי מוגבלת** אחרי האתחול — השרת יכול לעשות כל דבר, לא משנה מה הצהיר.

---

### 2.2 פגיעות 2: דגימה ללא אימות מקור (Sampling Without Origin Authentication)

#### מנגנון ה-Sampling

מנגנון ייחודי ל-MCP שלא קיים בשום פרוטוקול אחר: **השרת** יכול לבקש מהלקוח לשלוח prompt ל-LLM ולקבל תשובה. זה נעשה דרך `sampling/createMessage`:

```json
{
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {"role": "user", "content": "...תוכן שהשרת שולט בו..."}
    ],
    "maxTokens": 1000
  }
}
```

#### הבעיה הקריטית — התרשים מהמאמר (Figure 1)

```
                1. Request                    2. tool/call
  ┌──────┐  ──────────────►  ┌──────┐  ──────────────►  ┌──────────┐
  │ User │                   │ Host │                   │  Server  │
  └──────┘  ◄──────────────  └──────┘  ◄──────────────  └──────────┘
                                          3. sampling/
                                          createMessage

  השרת שולח prompt עם role: "user" ← ה-Host מעביר אותו ל-LLM
                                     בלי שום הבדל ויזואלי או סמנטי
                                     מהודעת user אמיתית!
```

**התוצאה:** ה-LLM מקבל הודעה שנראית כאילו המשתמש כתב אותה, אבל היא בעצם מהשרת. זו **הזרקת פרומפט (prompt injection) ברמת הפרוטוקול** — לא באג, לא ניצול — הפרוטוקול מעצב את זה ככה.

#### בדיקת ממשק משתמש — שלושה מוצרים מובילים

| מוצר (Host) | גרסה | אינדיקטור מקור | הבחנה ויזואלית |
|-------------|-------|---------------|---------------|
| Claude Desktop | 1.2.3 | **אין** | **לא** |
| Cursor | 0.44 | **אין** | **לא** |
| Continue | 0.9 | **אין** | **לא** |

**אף מוצר שנבדק לא מספק הבחנה ויזואלית** בין הודעות sampling שמקורן בשרת לבין הודעות אמיתיות של המשתמש.

#### מדוע זו חולשת פרוטוקול ולא באג ביישום?

אפשר לטעון "זו אחריות ה-Host להציג אינדיקטור מקור." אבל:

> **המפרט שותק** לגבי origin display — הוא **מאפשר** (enables) את ההתקפה במקום **למנוע** (prevents) אותה. ATTESTMCP פותר את זה על ידי **חיוב** (mandating) תיוג מקור ברמת הפרוטוקול, ומסיר את שיקול הדעת מהיישום.

---

### 2.3 פגיעות 3: התפשטות אמון מרומזת (Implicit Trust Propagation)

#### התרחיש — פריסה מרובת שרתים (Multi-Server)

כשהלקוח מחובר לכמה שרתי MCP בו-זמנית, המפרט **לא מגדיר גבולות בידוד** (isolation boundaries) ביניהם:

```
┌──────────────────────────────────────────────────────────────┐
│                    LLM Context Window                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Server A    │  │  Server B    │  │  Server C        │   │
│  │  (filesystem)│  │  (database)  │  │  (attacker!)     │   │
│  │              │  │              │  │                   │   │
│  │  Tool output │  │  Tool output │  │  Tool output      │   │
│  │  from A      │  │  from B      │  │  with malicious   │   │
│  │              │  │              │  │  instructions     │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ⚠ הכל מעורבב! אין provenance tracking!                     │
│  ⚠ output של Server C משפיע על קריאות ל-A ו-B              │
└──────────────────────────────────────────────────────────────┘
```

#### שלושה וקטורי תקיפה של שרת C (זדוני):

1. **הטיית כלים (Tool Hijacking):** הטמנת הוראות בתגובת כלי של C שגורמות ל-LLM לקרוא לכלי של Server B
2. **הוצאת מידע (Data Exfiltration):** שאיבת מידע שהוחזר מ-Server B דרך ערוץ התקשורת של Server A
3. **הקמת עמידות (Persistence):** הרעלת הקשר (context poisoning) משותף שנשמר בין סשנים

#### העיקרון הפורמלי שנפרץ

**Isolation:** "פגיעה ברכיב אחד לא אמורה להתפשט לרכיבים אחרים."

MCP מעדיף **composability** (יכולת של כלים לעבוד יחד) על פני **isolation**. המאמר לא טוען שזה בהכרח שגוי — אלא שצריך **הסכמת משתמש מפורשת** (explicit user consent) ולא אמון מרומז.

#### הדילמה: אבטחה מול שימושיות

| רמת בידוד | ASR (שיעור הצלחת התקפה) | השלמת משימה | הערות |
|-----------|----------------------|------------|-------|
| **None** (ברירת מחדל MCP) | 61.3% | 94.2% | הכי פגיע, הכי שמיש |
| **User-prompted cross-flow** | 31.7% | 87.4% | ATTESTMCP ברירת מחדל |
| **Strict (no cross-flow)** | 8.7% | 61.8% | הכי בטוח, הכי מגביל |

**תובנה:** ATTESTMCP בוחר את אפשרות הביניים — "user-prompted" — שמורידה ASR ב-48% תוך שמירה על 87.4% השלמת משימות (לעומת 94.2% בלי הגנה). זה איזון סביר.

---

## 3. מתודולוגיה — מסגרת PROTOAMP

### 3.1 מה זה PROTOAMP?

**PROTOAMP** = Protocol Amplification Benchmark — מסגרת מחקרית חדשנית שמודדת **כמה ארכיטקטורת MCP מגבירה (amplifies) את שיעור ההתקפה** בהשוואה לשימוש ישיר בכלים ללא MCP.

**ההבדל מעבודות קודמות:**
- **InjecAgent, AgentDojo:** מניחים קריאת API ישירה (לא דרך MCP)
- **MCP-Bench:** מודד השלמת משימות, לא אבטחה
- **MCPSecBench:** מקטלג סוגי התקפות, אבל לא משווה MCP ל-non-MCP

**PROTOAMP הוא הראשון** שמבודד את אפקט הפרוטוקול: אותן התקפות, אותם payloads, אותם LLMs — פעם עם MCP ופעם בלי.

### 3.2 רכיבי המסגרת

```
┌─────────────────────────────────────────────────────────────────┐
│                       PROTOAMP Framework                         │
│                                                                  │
│  ┌───────────────────────┐    ┌────────────────────────────┐    │
│  │  MCP Server Wrappers  │    │  Baseline (Direct Calls)   │    │
│  │                       │    │                            │    │
│  │  כלי benchmark עטופים │    │  אותם כלים בדיוק,         │    │
│  │  בשרתי MCP תואמים    │    │  אבל כקריאות פונקציה      │    │
│  │                       │    │  ישירות (ללא MCP)          │    │
│  └───────────┬───────────┘    └──────────────┬─────────────┘    │
│              │                               │                   │
│              ▼                               ▼                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              Injection Points (3 layers)                   │   │
│  │  • Resource content (indirect injection)                   │   │
│  │  • Tool response payloads                                  │   │
│  │  • Sampling request prompts                                │   │
│  └───────────────────────────────────────────────────────────┘   │
│              │                                                   │
│              ▼                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │           Measurement Infrastructure                       │   │
│  │  • JSON-RPC message logging                                │   │
│  │  • Attack propagation analysis                             │   │
│  │  • ASR computation per attack type                         │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 שרתי MCP שנבדקו

| שרת | פונקציונליות | סוג כלים |
|-----|-------------|---------|
| `mcp-server-filesystem` | קריאת/כתיבת קבצים | read, write, list |
| `mcp-server-git` | ניהול גרסאות | clone, commit, diff |
| `mcp-server-sqlite` | שאילתות מסד נתונים | SELECT, INSERT |
| `mcp-server-slack` | הודעות | messaging integration |
| `adversarial-mcp` | מותאם אישית | edge cases פרוטוקוליים |

### 3.4 מודלי LLM שנבדקו

- **Claude-3.5-Sonnet** — המודל העמיד ביותר
- **GPT-4o** — ביצועי ביניים
- **Llama-3.1-70B** — הפגיע ביותר

### 3.5 סט ההתקפות — 847 תרחישים

```
847 Attack Scenarios:
  │
  ├── InjecAgent adaptations:    312 (injection עקיפה, ניצול כלים)
  │
  ├── AgentDojo adaptations:     398 (התקפות multi-step)
  │
  └── Novel protocol-specific:   137 (sampling, cross-server)
                                     ← ייחודיים ל-MCP!
```

### 3.6 משתנים מבוקרים (Controlled Variables)

כדי להבטיח שההשוואה בין MCP ל-baseline הוגנת:

- **סמנטיקת הכלי** — זהה בין שני התנאים
- **Payloads של injection** — אותם בדיוק
- **אסטרטגיית prompting** — קבועה
- **השהיית רשת** — מותאמת (baseline מדמה latency של MCP)

**בדיקת Latency:** חציון 12.4ms ל-stdio, 23.7ms ל-HTTP/SSE. אומתו באמצעות paired t-test (p > 0.3, n = 200) שלא מצא השפעה על שיעורי סירוב בטיחותיים.

---

## 4. תוצאות — MCP מגביר התקפות ב-23-41%

### 4.1 אפקט ההגברה הפרוטוקולי (Protocol Amplification)

**הממצא המרכזי של המאמר:** הארכיטקטורה של MCP **מגבירה** את שיעור ההצלחה של התקפות ב-23%-41% בהשוואה לשימוש ישיר בכלים.

| סוג התקפה | Baseline (ללא MCP) | MCP | הגברה (Delta) |
|-----------|-------------------|-----|-------------|
| Indirect Injection (Resource) | 31.2% | 47.8% | **+16.6%** |
| Tool Response Manipulation | 28.4% | 52.1% | **+23.7%** |
| Cross-Server Propagation | 19.7% | 61.3% | **+41.6%** |
| Sampling-Based Injection | N/A | 67.2% | **--** (ייחודי ל-MCP) |
| **Overall** | **26.4%** | **52.8%** | **+26.4%** |

**תובנות:**
- **ההגברה הגדולה ביותר** (41.6%) היא ב-cross-server propagation — כי MCP מאפשר התקפות שפשוט לא אפשריות בפריסה חד-שרתית
- **Sampling-based injection** הוא וקטור חדש לגמרי (67.2% ASR) שלא קיים מחוץ ל-MCP
- ה-overall ASR קפץ מ-26.4% ל-52.8% — **כפול** — רק בגלל ארכיטקטורת הפרוטוקול

### 4.2 חומרת פגיעות ה-Sampling

ניתוח מפורט של התקפות sampling לפי מודל:

| מודל | ASR | שיעור הוצאת מידע (Exfil. Rate) | עמידות בין סשנים (Persist.) |
|------|-----|-------------------------------|---------------------------|
| Claude-3.5-Sonnet | 58.3% | 42.1% | 31.7% |
| GPT-4o | 71.4% | 53.8% | 38.2% |
| Llama-3.1-70B | 72.1% | 61.2% | 44.6% |

**ממצאים:**
- שרתים שמנצלים sampling משיגים **58-72% הצלחה**
- **42-61%** מצליחים להוציא מידע (exfiltration)
- **31-44%** מצליחים להקים עמידות בין סשנים (persistence)
- **Claude-3.5-Sonnet עמיד ביותר** — עקבי עם ממצאי AgentDojo

### 4.3 ניצול אמון בפריסה מרובת שרתים

התקפות עם 2-5 שרתים, כש**אחד** מהם תחת שליטת התוקף:

| מספר שרתים | ASR | Cascade Rate |
|-----------|-----|-------------|
| 1 | 47.8% | N/A |
| 2 | 58.4% | 34.2% |
| 3 | 67.1% | 51.8% |
| 5 | **78.3%** | **72.4%** |

**תובנה קריטית:** עם 5 שרתים, שרת אחד פגוע משיג **78.3% ASR** עם **72.4% cascade rate** — כלומר ב-72% מהמקרים ההתקפה מצליחה להתפשט לפעולות של שרתים אחרים.

#### השוואה להנדסת prompt כהגנה

הוספת "Never pass data between different tool servers without explicit user confirmation" ל-system prompt:
- ASR ירד מ-61.3% ל-47.2% — ירידה של 23%
- **אבל** עדיין **גבוה משמעותית** מ-8.7% של ATTESTMCP
- **מסקנה:** הגנות ברמת prompt אינן מספיקות — צריך בידוד ברמת פרוטוקול

### 4.4 השוואה ל-benchmarks קיימים

כשאותם תרחישים רצים דרך MCP במקום ישירות:

| Benchmark | תנאים | ASR מקורי | ASR עם MCP |
|-----------|-------|----------|-----------|
| InjecAgent | GPT-4 | 24-48% | **51.2%** |
| AgentDojo | Best agent | <25% | **38.7%** |
| Agent-SafetyBench | Safety score | <60% | **47.3%** |

**עלייה של 7-15 נקודות אחוז** — מאשרת הגברה ספציפית לפרוטוקול, בלתי תלויה בפגיעויות כלליות של LLM.

---

## 5. הפתרון — ATTESTMCP: הרחבת פרוטוקול תואמת-לאחור

### 5.1 עקרונות עיצוב

ATTESTMCP הוא **הרחבה לפרוטוקול** (protocol extension) — לא framework חיצוני ולא plugin — אלא שינוי במפרט עצמו:

```
┌─────────────────────────────────────────────────────────────┐
│                  ATTESTMCP — 5 עקרונות עיצוב                │
│                                                             │
│  1. Capability Attestation (אישור יכולות)                   │
│     → שרתים חייבים להוכיח יכולות דרך תעודות חתומות          │
│                                                             │
│  2. Message Authentication (אימות הודעות)                   │
│     → כל הודעת JSON-RPC כוללת חתימת HMAC-SHA256             │
│                                                             │
│  3. Origin Tagging (תיוג מקור)                              │
│     → בקשות sampling מסומנות כמקור שרת, לא משתמש            │
│                                                             │
│  4. Isolation Enforcement (אכיפת בידוד)                     │
│     → זרימת מידע cross-server דורשת הרשאה מפורשת            │
│                                                             │
│  5. Replay Protection (הגנה מפני שידור חוזר)                │
│     → timestamp + nonce עם חלון תוקף ניתן להגדרה            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 תעודת יכולות (Capability Certificate)

```json
{
  "capability_cert": {
    "server_id": "filesystem-server",
    "capabilities": ["resources", "tools"],
    "issued_by": "anthropic-ca",
    "issued_at": 1706140800,
    "expires_at": 1737676800,
    "signature": "base64..."
  }
}
```

**הרעיון:** במקום self-assertion, השרת מציג **תעודה חתומה** (signed certificate) מרשות אישורים (Certificate Authority). הלקוח מאמת את החתימה ומוודא שהשרת באמת רשאי להשתמש ביכולות שהוא טוען.

### 5.3 הודעה מאומתת (Authenticated Message)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {...},
  "mcpsec": {
    "server_id": "filesystem-server",
    "timestamp": 1706140800,
    "nonce": "random-32-bytes",
    "hmac": "base64..."
  }
}
```

**כל הודעת JSON-RPC** כוללת בלוק `mcpsec` עם:
- **server_id** — זיהוי השרת ששלח
- **timestamp** — חותמת זמן למניעת replay
- **nonce** — ערך חד-פעמי למניעת שכפול
- **hmac** — חתימת HMAC-SHA256 שקושרת תוכן לזהות שרת

### 5.4 מודלי אמון — שלוש אפשרויות

המאמר בוחן שלושה מודלים לרשות האישורים:

| מודל | יתרונות | חסרונות |
|------|---------|---------|
| **Centralized** (ריכוזי) | PKI פשוט, ביטול קל | נקודת כשל יחידה |
| **Federated** (פדרלי) | מבוזר, גמיש | תיאום מורכב |
| **Web-of-Trust** (רשת אמון) | מבוזר לחלוטין | מורכבות למשתמש |

**הבחירה של המאמר:** המודל **הפדרלי** — כל ספק פלטפורמה (Anthropic, Cursor, JetBrains) מפעיל CA לאקוסיסטם שלו, עם הסכמי חתימה צולבת (cross-signing) לאינטרופרביליות.

#### אימות זהות שרתים

- **שרתים מסחריים:** אימות בעלות על דומיין (DNS TXT record)
- **שרתים קוד פתוח:** קישור לחשבון package registry (npm, pip) עם אימות זהות מתחזק

#### תשתית ביטול (Revocation Infrastructure)

CAs פדרליים מתחזקים רשימות ביטול משותפות (Certificate Revocation Lists) עם SLAs:
- **ביטול חירום** (חשבון npm פגוע): תוך 4 שעות
- **ביטול רגיל**: תוך 24 שעות
- **הפצת CRL:** OCSP stapling עם רענון כל שעה

### 5.5 תואמות לאחור ומיגרציה

ATTESTMCP עובד בשלושה מצבים:

```
┌────────────────────────────────────────────────────────┐
│              ATTESTMCP Migration Modes                  │
│                                                        │
│  1. Permissive (ברירת מחדל להעברה)                     │
│     → מקבל שרתים ישנים עם אזהרה למשתמש                │
│     → כמו HTTPS mixed content warnings                │
│                                                        │
│  2. Prompt (שואל)                                      │
│     → דורש אישור מפורש של המשתמש לשרתים לא חתומים     │
│     → כמו "Do you trust this certificate?"             │
│                                                        │
│  3. Strict (קפדני)                                     │
│     → דוחה כל שרת לא חתום                              │
│     → כמו HSTS — אין פשרות                            │
│                                                        │
│  + Downgrade Attack Mitigation:                        │
│     → אחרי שהלקוח ראה credentials תקפים, הוא pin-ה    │
│     → חיבורים עתידיים ללא credentials → אזהרת אבטחה   │
│     → מונע MITM שמסיר headers                         │
└────────────────────────────────────────────────────────┘
```

### 5.6 מאפייני אבטחה של הודעות MCP — לפני ואחרי

| מאפיין אבטחה | נדרש? | MCP v1.0 | ATTESTMCP |
|-------------|-------|----------|-----------|
| Message Authentication | כן | **לא** | **כן** (HMAC-SHA256) |
| Replay Protection | כן | **לא** | **כן** (nonce + timestamp) |
| Capability Binding | כן | **לא** | **כן** (certificates) |
| Origin Identification | כן | **חלקי*** | **כן** (origin tagging) |
| Integrity Verification | כן | **לא** | **כן** (HMAC) |

*\* ברמת transport בלבד (TLS), לא ברמת payload*

---

## 6. ביצועי ATTESTMCP — Overhead ויעילות

### 6.1 תקורת ביצועים (Latency Overhead)

| פעולה | P50 (ms) | P95 (ms) | P99 (ms) |
|-------|---------|---------|---------|
| Certificate validation (cold) | 4.2 | 8.1 | 12.3 |
| Certificate validation (cached) | 0.3 | 0.5 | 0.8 |
| HMAC-SHA256 computation | 0.3 | 0.4 | 0.6 |
| Nonce lookup/insertion | 0.1 | 0.2 | 0.3 |
| **Total per message (cold)** | **8.3** | **14.2** | **21.7** |
| **Total per message (warm)** | **2.4** | **4.1** | **6.2** |

**הערכה:** חציון 8.3ms (cold) או 2.4ms (warm cache) — **זניח** ביחס ל-LLM inference שלוקח 500-2000ms. Certificate validation שולט ב-cold start overhead; caching מפחית משמעותית בקריאות חוזרות באותו session.

### 6.2 יעילות הגנתית — ירידה ב-ASR

| סוג התקפה | MCP (ללא הגנה) | ATTESTMCP | שיפור (Reduction) |
|-----------|---------------|-----------|-------------------|
| Indirect Injection | 47.8% | 18.4% | **61.5%** |
| Tool Response Manipulation | 52.1% | 14.2% | **72.7%** |
| Cross-Server Propagation | 61.3% | 8.7% | **85.8%** |
| Sampling-Based Injection | 67.2% | 11.3% | **83.2%** |
| **Overall** | **52.8%** | **12.4%** | **76.5%** |

**תוצאה מרכזית:** ATTESTMCP מוריד ASR כולל מ-52.8% ל-12.4% — **ירידה של 76.5%!**

**השיפורים הגדולים ביותר:**
- **Cross-server** (85.8%) — אכיפת בידוד ותיוג מקור
- **Sampling** (83.2%) — origin tagging מונע התחזות

**ה-12.4% שנותר:** בעיקר indirect injection דרך תוכן שהוחזר באופן לגיטימי — **בעיה יסודית של כל מערכות LLM** שלא ניתנת לפתרון ברמת הפרוטוקול.

---

## 7. וקטורי גילוי שרתים — איך תוקפים מגיעים למשתמשים

המאמר סוקר 127 מדריכי התקנה של שרתי MCP ומזהה 4 וקטורים:

```
┌──────────────────────────────────────────────────────────┐
│           Server Discovery Attack Vectors                 │
│                                                          │
│  1. Typosquatting (34%)                                  │
│     npm/pip registries ← אין הגנת namespace              │
│     mcp-server-filesytem ← שימו לב לשגיאת כתיב!         │
│                                                          │
│  2. Supply Chain Compromise (28%)                        │
│     שרתים פופולריים עם dependencies רבים                 │
│     → פגיעים ל-upstream poisoning                        │
│                                                          │
│  3. Social Engineering (23%)                             │
│     73% מהמדריכים מנחים npx ישירות מ-GitHub              │
│     → ללא integrity verification                         │
│                                                          │
│  4. Marketplace Poisoning (15%)                          │
│     IDE extension marketplaces עם vetting מוגבל           │
│     → שרתים מגיעים ב-bundles                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 8. מגבלות המאמר

### מגבלות מתודולוגיות

- **5 שרתי MCP בלבד** — סביבות ייצור עם עשרות שרתים עשויות להציג מאפיינים שונים
- **לא בוצע אימות פורמלי (formal verification)** של ATTESTMCP — מתוכנן בעבודה עתידית עם symbolic model checking
- **מודל CA פדרלי** דורש תיאום אקוסיסטמי שעלול להוות מחסום לאימוץ
- **לא נבדקו ניסיונות עקיפה (bypass)** של ATTESTMCP עצמו

### מגבלות מעשיות

- **TOFU (Trust On First Use):** Pinning לא מגן כשהמשתמש מתקין שרת זדוני בפעם הראשונה — אם השרת מעולם לא טען תמיכה ב-ATTESTMCP, אין ציפייה לאישורים
- **Alert fatigue:** המדידות מניחות שמשתמשים באמת קוראים בקשות הרשאה cross-server. בפועל, **עייפות אזהרות** עלולה לגרום למשתמשים ללחוץ "Allow" באופן אוטומטי
- **Permissive default:** כל עוד רוב השרתים אינם חתומים, המצב ברירת מחדל יהיה "Permissive" ויתרון האבטחה ייעלם
- **שיורי ASR:** 12.4% שנותר הוא indirect injection דרך תוכן לגיטימי — **בעיה יסודית משותפת לכל מערכות LLM**

### מגבלת "תיקון נקודתי" — למה implementation hardening לא מספיק

המאמר מדגיש שלושה CVEs כדוגמה:

```
CVE-2025-49596: MCP Inspector RCE
  → תיקון: patch ל-Inspector
  → לא פותר: היעדר capability attestation

CVE-2025-68143: SQL injection ב-sqlite-mcp
  → תיקון: parameterized queries
  → לא פותר: sampling-based injection

Hardening של שרת בודד:
  → תיקון: קוד בטוח יותר
  → לא פותר: cross-server isolation
```

**המסקנה:** כל patch מתקן **סימפטום**, לא את **הגורם** — צריך שינוי ברמת הפרוטוקול.

---

## 9. דיון — ארכיטקטורה מול יישום

### 9.1 ההבחנה המרכזית

המאמר מבחין בין שני סוגי חולשות:

| מאפיין | חולשת יישום (Implementation) | חולשת ארכיטקטורה (Architectural) |
|--------|---------------------------|-------------------------------|
| **דוגמה** | SQL injection ב-sqlite-mcp | היעדר capability attestation |
| **טווח** | שרת ספציפי | כל יישום תואם |
| **תיקון** | Patch לשרת | שינוי במפרט |
| **אחריות** | מפתח השרת | מעצב הפרוטוקול |

### 9.2 המלצות לגרסה 2.0 של MCP

המאמר ממליץ:

1. **Mandatory capability attestation** — חובת תעודות חתומות ברמת הפרוטוקול
2. **Origin tagging לכל בקשות sampling** — לא אופציונלי
3. **Explicit isolation boundaries** — עם הרשאת משתמש ל-cross-server flow

---

## 10. רלוונטיות לתזה — דירוג סיכון דינמי לגישת סוכנים ל-MCP

### 10.1 מה המאמר מלמד אותנו על Risk Scoring

המאמר הזה מספק **מסד תיאורטי** קריטי למערכת ה-Risk Scoring הדינמית:

```
Breaking the Protocol מוכיח:
  │
  ├── 1. הסיכון לא בינארי — הוא ספציפי לארכיטקטורה
  │   → MCP מגביר התקפות ב-23-41%
  │   → Risk Score צריך לקחת בחשבון את הקשר הפרוטוקולי
  │
  ├── 2. Sampling = וקטור סיכון ייחודי
  │   → 67.2% ASR — הגבוה ביותר
  │   → Risk Score צריך לתת משקל גבוה לשרתים עם sampling capability
  │
  ├── 3. Multi-server = risk multiplier
  │   → 78.3% ASR עם 5 שרתים
  │   → Risk Score צריך להתחשב בכמות השרתים המחוברים
  │
  └── 4. Prompt-level defense לא מספיקה
      → ירידה של 23% בלבד
      → Risk Score צריך מנגנון ברמת פרוטוקול, לא רק LLM
```

### 10.2 שילוב ישיר עם MCP-RSS

| ממד מ-Breaking the Protocol | איך זה מתרגם ל-Risk Score 1-10 |
|----------------------------|-----------------------------|
| **Capability self-assertion** | +2 לציון סיכון אם שרת מצהיר על sampling ללא תעודה |
| **Missing origin tagging** | +1.5 לציון סיכון אם אין origin distinction ב-host |
| **Multi-server exposure** | +0.5 לכל שרת נוסף מחובר (cascade risk factor) |
| **Protocol amplification** | מכפיל סיכון × 1.26 (ה-amplification factor הממוצע) |
| **ATTESTMCP presence** | -3 לציון סיכון אם השרת מציג credentials תקפים |

### 10.3 נוסחת סיכון מתוקנת

על בסיס הממצאים, ניתן להרחיב את נוסחת ה-Risk Score:

```
Risk_total = Risk_base × Protocol_amplification_factor
           + Sampling_risk
           + Cascade_risk(n_servers)
           - Attestation_discount

כאשר:
  Risk_base                      = ציון בסיסי (מ-tool analysis)
  Protocol_amplification_factor  = 1.26 (ממוצע) עד 1.41 (cross-server)
  Sampling_risk                  = 2.0 אם יש sampling, 0 אחרת
  Cascade_risk(n)                = 0.5 × (n - 1) עבור n שרתים
  Attestation_discount           = 3.0 אם יש credentials תקפים
```

### 10.4 מה לקחת מהמאמר לתזה

```
לקחת:
  + ההבחנה architectural vs implementation — קריטית לטקסונומיית סיכונים
  + שלוש הפגיעויות כקטגוריות סיכון מובנות
  + מתודולוגיית PROTOAMP — benchmark comparison שמבודד פרוטוקול
  + נתוני ASR כבסיס אמפירי לקביעת משקלות
  + מודל ה-trust hierarchy (centralized/federated/web-of-trust)
  + הדילמה isolation vs composability — טריידאוף שה-risk score צריך לכמת

לא לקחת:
  - Protocol extension design — מעבר לסקופ התזה
  - PKI/CA infrastructure — מורכבות תפעולית גבוהה
  - Binary defense (block/allow) — התזה צריכה ציון רציף 1-10
```

### 10.5 ציטוט מרכזי מהמאמר

> *"MCP's security weaknesses are architectural rather than implementation-specific, requiring protocol-level remediation."*

> תרגום: חולשות האבטחה של MCP הן **ארכיטקטוניות** ולא ספציפיות ליישום, ולכן דורשות תיקון **ברמת הפרוטוקול**.

**המשמעות לתזה:** מערכת Risk Scoring צריכה להעריך סיכון ארכיטקטורי (האם הפרוטוקול עצמו מגביר סיכון?), לא רק סיכון יישומי (האם השרת הספציפי מסוכן?). המכפיל הפרוטוקולי שהמאמר מוכיח (26.4% amplification) הוא פרמטר שצריך להיכנס ישירות לנוסחת ה-risk scoring.

---

*סיכום זה נכתב עבור פרויקט התזה: MCP Dynamic Risk Scoring*
*תאריך: 2026-03-29*
