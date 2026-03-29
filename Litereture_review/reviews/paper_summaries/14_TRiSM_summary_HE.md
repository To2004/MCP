# TRiSM ל-AI סוכני: סקירת ניהול אמון, סיכון ואבטחה במערכות רב-סוכניות מבוססות LLM

**מאמר מאת:** Shaina Raza, Ranjan Sapkota, Manoj Karkee, Christos Emmanouilidis
**מוסדות:** Vector Institute (Toronto), Cornell University, University of Groningen
**arXiv:2506.04133v5** | דצמבר 2025
**סוג:** מאמר סקירה (Survey / Review Paper)

---

## 1. הבעיה המרכזית — למה צריך TRiSM ל-AI סוכני?

### תובנת המפתח

מערכות AI סוכניות מרובות-סוכנים (Agentic Multi-Agent Systems, AMAS) מבוססות LLM הפכו מכלי אוטומציה פשוטים **לישויות אוטונומיות** שמתכננות, מנמקות, משתמשות בכלים, ומתאמות זו עם זו. הבעיה: **אין מסגרת אחודה לניהול אמון, סיכון ואבטחה** (Trust, Risk, and Security Management = TRiSM) שמותאמת לעולם הרב-סוכני הזה.

### מטאפורה: "עיר ללא חוקים"

דמיינו עיר (מערכת AMAS) שבה כל תושב (סוכן AI) הוא עצמאי, יכול לנהל עסקים, לגשת למאגרי מידע, ולהתקשר עם תושבים אחרים:

```
🏙️ העיר AMAS (מערכת רב-סוכנית)
    │
    ├── 🤖 סוכן-מתכנן: מחליט מה לעשות, מפרק משימות
    │   └── סיכון: תוכנית שגויה מפעפעת לכל הסוכנים
    │
    ├── 🤖 סוכן-קודר: כותב קוד ומריץ API
    │   └── סיכון: קורא לכלים מסוכנים בלי הרשאה
    │
    ├── 🤖 סוכן-בודק: מאמת תוצאות
    │   └── סיכון: "חשיבה קבוצתית" — מאשר בלי לבדוק באמת
    │
    ├── 🧠 זיכרון משותף: כל הסוכנים קוראים וכותבים
    │   └── סיכון: הרעלת זיכרון, דליפת מידע רגיש
    │
    └── ⚠️ אין עירייה, אין משטרה, אין חוקי בנייה!
        → כל סוכן עושה מה שרוצה, ואף אחד לא אחראי
```

**TRiSM = מערכת הממשל של העיר** — חוקים, פיקוח, שקיפות, ואכיפה.

### למה הסקירות הקיימות לא מספיקות?

| סקירה קיימת | מה חסר? |
|-------------|---------|
| Guo et al. (2024) | אין טיפול באיומים, lifecycle, הסברתיות |
| Chen et al. (2024) | אין TRiSM, אין governance |
| Yan et al. (2025) | אין lifecycle, אין הסברתיות |
| Fang et al. (2025) | אין TRiSM ישיר, אין actionable metrics |
| **הסקירה הזו** | **מכסה הכל:** איומים, lifecycle, הסברתיות, TRiSM, LLM-specific, apps, actionable |

המאמר הוא **הסקירה הראשונה** שבוחנת מערכות רב-סוכניות מבוססות LLM דרך העדשה המלאה של TRiSM — אמון, סיכון, אבטחה וממשל.

---

## 2. מתודולוגיית הסקירה — איך הם בנו את מפת השטח

### 2.1 שאלות מחקר

המאמר נבנה סביב שלוש שאלות מחקר:

- **RQ1:** אילו אתגרי אמון, סיכון ואבטחה ייחודיים ל-AMAS?
- **RQ2:** אילו בקרות governance, הסברתיות, אבטחה, פרטיות ו-lifecycle (TRiSM) הוצעו או הותאמו ל-AMAS?
- **RQ3:** איך מעריכים AMAS (datasets, tasks, metrics) ואיפה הפערים?

### 2.2 אסטרטגיית חיפוש

```
(מונחי AMAS/Agentic)
  "agentic AI" OR "multi-agent systems" OR "multi-agent LLMs"
  OR "AI agents" OR "autonomous agents" OR "intelligent agents"
  OR "collaborative AI" OR "distributed AI" OR "LLM-based agents"
  OR "agent coordination" OR "agent-based modeling" OR "swarm intelligence"

AND (מונחי TRiSM)
  "trust" OR "trustworthiness" OR "risk" OR "security" OR "safety"
  OR "governance" OR "oversight" OR "compliance" OR "explainability"
  OR "interpretability" OR "transparency" OR "privacy" OR "data protection"
  OR "robustness" OR "accountability" OR "ethical AI" OR "fairness"
  OR "adversarial attacks" OR "regulatory compliance" OR "bias mitigation"
  OR "system reliability"
```

**מקורות:** IEEE Xplore, ACM Digital Library, SpringerLink, arXiv, ScienceDirect, Google Scholar
**טווח:** ינואר 2022 — דצמבר 2025 (+ עבודות יסוד קודמות)
**סינון:** 250 מאמרים אחרי title/abstract → **180 מאמרים ראשיים** אחרי full-text screening

### 2.3 סטטיסטיקות ביבליומטריות

- **61.2%** מאמרי journal, **23.2%** conference proceedings
- צמיחה אקספוננציאלית: מ-890 מאמרי multi-agent ב-2019 ל-**18,500** ב-2024
- מאמרי LLM-based agents: מ-0 ב-2019 ל-**9,800** ב-2024 (בעקבות ChatGPT)
- מוקדי פרסום: NeurIPS, ACM Computing Surveys, AAAI
- מוציאים לאור: Elsevier, Springer, IEEE

---

## 3. יסודות מערכות AI סוכניות — ההבדל בין עולם ישן לעולם חדש

### 3.1 סוכנים מסורתיים מול AI סוכני

```
┌──────────────────────────────────────────────────────────────────┐
│           Traditional AI Agents          │    Agentic AI (AMAS)  │
│──────────────────────────────────────────│───────────────────────│
│  חוקים קבועים, מכונות מצבים             │  מונחה מטרות, אדפטיבי │
│  לוגיקה סמלית (SOAR, ACT-R)            │  Foundation Models     │
│  תחום צר, task-specific                 │  cross-domain, רחב     │
│  הסקה דטרמיניסטית                       │  Chain-of-Thought      │
│  סוכנים מבודדים, פירוק ידני             │  תיאום אוטומטי, תפקידים│
│  זיכרון אפיזודי, מוגבל לסשן            │  זיכרון מתמיד, vector DB│
│  כלים סטטיים, interfaces ידניים         │  dynamic function call  │
│  סקריפטים, תבניות                       │  שפה טבעית, NLU/NLG    │
│  MYCIN, ELIZA, SOAR                     │  AutoGen, ChatDev,     │
│                                          │  MetaGPT, CrewAI       │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 ארכיטקטורת AMAS — מבנה מלא

```
┌──────────────────────────────────────────────────────────────────┐
│            LLM-based Agentic Multi-Agent System (AMAS)          │
│                                                                  │
│  ┌──────────────┐    ┌───────────────────┐    ┌───────────────┐ │
│  │  Perception/ │    │   Cognitive/      │    │   ACTION/     │ │
│  │  Input Layer │───→│   Reasoning Layer │───→│   EXECUTION   │ │
│  │              │    │   (LLM Core)      │    │   Layer       │ │
│  │ text, image, │    │ goal → planning → │    │ digital &     │ │
│  │ audio        │    │ decision making   │    │ physical tasks│ │
│  └──────────────┘    └────────┬──────────┘    └───────────────┘ │
│                               │                                  │
│  ┌──────────────┐    ┌────────┴──────────┐    ┌───────────────┐ │
│  │Communication │    │  Data Storage     │    │  Learning     │ │
│  │& Collaboration│←──│  & Retrieval      │───→│  Module       │ │
│  │              │    │ (vector DB,       │    │ (feedback,    │ │
│  │ agent msgs,  │    │  RAG, memory)     │    │  fine-tuning) │ │
│  │ coordination │    └───────────────────┘    └───────────────┘ │
│  └──────────────┘                                                │
│                      ┌───────────────────┐                       │
│                      │  Monitoring &     │                       │
│                      │  Governance       │                       │
│                      │ logs, constraints,│                       │
│                      │ audit, alerts     │                       │
│                      └───────────────────┘                       │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 רכיבי הליבה של AMAS

| רכיב | תפקיד | סיכון TRiSM |
|------|--------|-------------|
| **Communication Middleware** | העברת הודעות בין סוכנים (A2A, ANP) | spoofing, דליפת פרטיות |
| **Cognitive/Reasoning Layer** | LLM כבקר החלטות, CoT/ToT | hallucinations, prompt injection |
| **Planning & Reasoning Module** | פירוק מטרות למשימות-משנה (ReAct) | תוכניות שגויות מפעפעות |
| **Memory Module** | short-term + long-term (vector search) | הרעלת זיכרון, stale context |
| **Learning Module** | הסתגלות מ-feedback/rewards | drift, emergent misalignment |
| **Data Storage & Retrieval** | structured stores + RAG | דליפת מידע, חסר access control |
| **Tool Interface** | קריאות מובנות ל-APIs חיצוניים | שימוש לרעה בכלים, API abuse |
| **Monitoring & Governance** | איסוף logs, אכיפת policies | פערי observability |

### 3.4 טבלת השוואה של frameworks מייצגים

| Framework | LLM Core | תכנון | זיכרון | כלים | תכונה בולטת |
|-----------|---------|--------|--------|------|-------------|
| AutoGPT | GPT-4 | Self-looped CoT | Vector DB | OS shell + web | לולאת מטרות אוטונומית |
| MetaGPT | GPT-4 | SOP workflow | YAML state | Git CLI | תפקידים מובנים לפיתוח תוכנה |
| AutoGen | GPT-4 | Multi-agent PDDL | JSON/DB | API calls | תבניות סוכנים מודולריות |
| CrewAI | Any | Declarative plan | Optional DB | Python modules | framework קל, LangChain-free |
| LangGraph | Model-agnostic | FSM via graph | Persistent nodes | Custom modules | תזמור ויזואלי בגרפים |
| OpenAI Agents SDK | Provider-agnostic | Agent loops, handoffs | Sessions | Tools + guardrails | workflows, safety, extensibility |
| Strands Agents | Model-agnostic | Agent loop + streaming | N/A | Python tools, MCP tools | SDK קל, autonomous workflows |

**תובנת מפתח:** כל ה-frameworks משלבים תכנון, שימוש בכלים, זיכרון ואינטראקציה עם סביבה — מה שיוצר **מערכת סגורה** (closed-loop) שמרחיבה את שטח ההתקפה ומסבכת את הייחוס (accountability).

---

## 4. איומים וסיכונים ב-AI סוכני — טקסונומיה מלאה

### 4.1 שישה איומי ליבה

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMAS Threats Landscape                        │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Autonomy       │  │  Persistent     │  │  Agent         │  │
│  │  Abuse          │  │  Memory         │  │  Orchestration │  │
│  │                 │  │                 │  │                │  │
│  │ סוכנים מפרשים  │  │ תוכן מוזרק     │  │ orchestrator   │  │
│  │ מטרות לא נכון  │  │ מפעפע דרך      │  │ שנפרץ משבש    │  │
│  │ ומבצעים תוכניות│  │ זיכרון משותף    │  │ כל ה-workflow  │  │
│  │ מזיקות         │  │ ללא versioning  │  │                │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Goal           │  │  Tool Misuse &  │  │  Multi-Agent   │  │
│  │  Misalignment   │  │  API Exploits   │  │  Collusion     │  │
│  │                 │  │                 │  │                │  │
│  │ חשיפת מטרות    │  │ הרצת קוד לא    │  │ groupthink:    │  │
│  │ → adversarial   │  │ בטוח, policy   │  │ סוכנים מחזקים  │  │
│  │ steering        │  │ violations     │  │ שגיאות הדדיות  │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 טקסונומיית סיכונים — 4 קטגוריות מרכזיות

המאמר מארגן את סיכוני AMAS לארבע קטגוריות:

#### (א) התקפות אדברסריות (Adversarial Attacks)
- **Prompt injection** — הזרקת הוראות זדוניות ל-prompt
- **Engineered reasoning traps** — מלכודות חשיבה שגורמות לסוכן להסיק מסקנות שגויות
- **Role-swapping attacks** — ב-ChatDev, תוקף מנצל inter-agent dependencies כדי להחליף תפקידים
- **Cascading manipulation** — התקפה על סוכן אחד מפעפעת לכל השאר

#### (ב) דליפת נתונים (Data Leakage)
- **זיכרון משותף** — סוכנים חולקים מידע רגיש דרך shared memory
- **תקשורת בין-סוכנית** — הודעות בין סוכנים עלולות לחשוף מידע
- **גבולות חלשים** — sanitization לקויה, access controls חסרים

#### (ג) קנוניה בין סוכנים (Agent Collusion)
- **Groupthink** — סוכנים מחזקים הנחות שגויות זה של זה
- **Mode collapse** — התכנסות על פלטים sub-optimal
- **Collusive failure** — ב-ChatDev, שגיאות תכנון מתפשטות כי אין feedback חיצוני

#### (ד) התנהגויות מתגלות (Emergent Behaviors)
- **Shortcutting verification** — סוכנים מדלגים על בדיקות
- **Unpredictable strategies** — אינטראקציות מורכבות יוצרות התנהגויות לא צפויות
- **System prompt drift** — context שמצטבר לאורך זמן משנה מטרות

### 4.3 דוגמאות מהעולם האמיתי

```
דוגמה 1 — Prompt Leakage (AutoGPT-style):
  ┌─────────────────────────────────────────┐
  │ AutoGPT prompt augmentation ← recursion │
  │ + weak memory controls                  │
  │ → stored tokens surface in              │
  │   summaries or logs later               │
  │ → sensitive content exposed! ❌         │
  └─────────────────────────────────────────┘

דוגמה 2 — Collusive Failure (ChatDev):
  ┌─────────────────────────────────────────┐
  │ Planner agent → שגיאה בתוכנית           │
  │ Coder agent → מקודד לפי תוכנית שגויה    │
  │ Reviewer agent → "נראה טוב" (groupthink) │
  │ → אין feedback חיצוני → שגיאה מתפשטת ❌ │
  └─────────────────────────────────────────┘

דוגמה 3 — Memory Poisoning:
  ┌─────────────────────────────────────────┐
  │ Feedback buffers ← adversarial signals  │
  │ → polluted policy updates               │
  │ → degraded behavior over time ❌        │
  └─────────────────────────────────────────┘

דוגמה 4 — System Prompt Drift:
  ┌─────────────────────────────────────────┐
  │ Self-appended context (no versioning)   │
  │ → prompts shift over time               │
  │ → hallucinated goals ❌                 │
  │ → misaligned behaviors                  │
  └─────────────────────────────────────────┘
```

**תובנת מפתח:** כל הסיכונים נובעים מהעובדה ש-AMAS היא מערכת **סגורה** (closed-loop) עם אוטונומיה, זיכרון משותף, תזמור ושימוש בכלים — מה שמאפשר **לכשלים להפעפע** דרך סוכנים ולהתמיד דרך זיכרון.

---

## 5. מסגרת TRiSM ל-AMAS — חמישה עמודים

### 5.1 סקירת המסגרת

מסגרת TRiSM מורכבת מחמישה עמודים (pillars) שמותאמים לאתגרים הייחודיים של AMAS:

```
┌──────────────────────────────────────────────────────────────────────┐
│         Lifecycle Governance Plane (TRiSM Pillar)                    │
│   policies · accountability · compliance · oversight · traceability  │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │  Trust & Explainability (TRiSM Pillar)                          │ │
│ │  reasoning/provenance traces · explainer agent · audit logs     │ │
│ ├──────────────────────────────────────────────────────────────────┤ │
│ │  ModelOps / Lifecycle Management (TRiSM Pillar)                 │ │
│ │  prompt+agent config versioning · CI/CD safety gates ·          │ │
│ │  monitoring/rollback · incident workflow                        │ │
│ ├──────────────────────────────────────────────────────────────────┤ │
│ │  Application Security (TRiSM Pillar)                            │ │
│ │  prompt hygiene · allowlists · tool sandboxing ·                │ │
│ │  least privilege (RBAC) · anomaly detection                     │ │
│ ├──────────────────────────────────────────────────────────────────┤ │
│ │  Model Privacy & Data Protection (TRiSM Pillar)                 │ │
│ │  encrypted/scoped memory · data minimization ·                  │ │
│ │  DP where applicable · access logs · retention/consent          │ │
│ ├──────────────────────────────────────────────────────────────────┤ │
│ │  Planning & Reasoning (Agent Core Layer; non-TRiSM)             │ │
│ │  multi-agent planning · task decomposition ·                    │ │
│ │  CoT/ToT/ReAct · inter-agent coordination                      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │
│  │ User / HITL  │  │ Secure API       │  │ External Tools         │ │
│  │ UI           │  │ Gateway          │  │                        │ │
│  │ confirm ·    │  │ authN/authZ ·    │  │ web · DB · code ·     │ │
│  │ override ·   │  │ egress control · │  │ enterprise APIs       │ │
│  │ stop ·       │  │ tool isolation · │  │                        │ │
│  │ feedback     │  │ policy checks    │  │                        │ │
│  └──────────────┘  └──────────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 עמוד 1: הסברתיות ואמון (Explainability / Trust)

**האתגר ב-AMAS:** הסברתיות לא עוסקת בפירוש מודל בודד, אלא בהבנת **איך החלטות מתגלות מאינטראקציה בין סוכנים מתמחים**. התוצאה הסופית היא תוצר של שיתוף פעולה, לא חיזוי בודד.

**אתגרים ספציפיים:**
- **התנהגות מתגלה (Emergent behavior)** — אינטראקציות בין סוכנים יוצרות דפוסים שלא תוכננו
- **אימות שלבי ביניים** — vanilla CoT יכול להיראות אמין אך להיות שגוי; שגיאות קטנות מצטברות

**טכניקות הסברתיות ל-AMAS:**

| טכניקה | תיאור | יתרון ל-AMAS |
|--------|-------|-------------|
| **Feature attribution (LIME/SHAP)** | ייחוס פלט לקלטים ספציפיים | מבהיר אילו signals השפיעו על סוכן |
| **Counterfactual analysis** | "What-if" — מה היה קורה אם סוכן X לא היה פועל? | מבודד תלויות סיבתיות |
| **Reasoning-trace logging** | הקלטת CoT, tool calls, דיאלוגים | audit trail שחושף תרומת כל סוכן |
| **Natural-language explanations** | סוכן מסביר שמסנתז traces ל-narrative | שקיפות למשתמש |
| **Role-oriented architectures** | תפקידים מפורשים (reasoning, verification, credit) | כל שלב inspectable |
| **Explainable reward critics** | ב-multi-agent RL, critics מספקים הצדקה שקופה | debugging של incentives |

**כיוונים חדשים:**
- **Layered Chain-of-Thought** — פירוק reasoning לשכבות, כל שכבה עונה על sub-question
  - Reasoning Agent → תוצאות חלקיות
  - Verification Agent → cross-check מול knowledge graphs
  - User-Interaction Agent → אימות מול feedback אנושי

### 5.3 עמוד 2: ModelOps — ניהול מחזור חיים

ModelOps מרחיב את MLOps מעבר לאימון ופריסה **לממשל, ניהול סיכונים ופיקוח מתמשך**.

**מה צריך ב-AMAS:**
- **Version control & CI/CD** — מעקב אחר גרסאות של model, prompts, tools, configuration. סימולציות multi-agent ב-CI לוודא שעדכונים לא שוברים safety
- **Hierarchical monitoring** — מערכות כמו MegaAgent: agents log → group admins → system supervisors
- **Risk measurement policies** — לפי NIST Generative AI profile: תיעוד סיכונים, gradient-based attributions, counterfactual prompting

### 5.4 עמוד 3: אבטחת יישומים (Application Security)

**איומים מרכזיים:** prompt injection, data exfiltration, tool misuse

**בקרות הגנה:**

```
┌────────────────────────────────────────────────────┐
│        Defense-in-Depth for AMAS Security          │
│                                                    │
│  Layer 1: Prompt Hygiene                           │
│    • sanitize & filter inputs                      │
│    • secure system prefixes                        │
│    • validate instructions                         │
│    • constrain output formats                      │
│                                                    │
│  Layer 2: Design Patterns                          │
│    • Action-Selector: בחירה מתוך allowlist         │
│    • Plan-Then-Execute: הפרדת תכנון מביצוע         │
│    • isolate untrusted data from execution paths   │
│                                                    │
│  Layer 3: Least-Privilege Access                   │
│    • RBAC/ABAC per agent/role                      │
│    • strong authentication                         │
│    • continuous monitoring for anomalies            │
│    • flag or suspend deviating agents              │
│                                                    │
│  Layer 4: Post-Processing & Anomaly Detection      │
│    • output filters (sensitive/inaccurate content) │
│    • robust logging & retention policies           │
│    • incident response                             │
│                                                    │
│  Layer 5: Cross-Agent Verification                 │
│    • hierarchical monitoring (LangChain, AutoGen)  │
│    • agent-level checks (reviewers/critics)        │
│    • trust/reputation signals                      │
│    • adversarial training & red-teaming             │
└────────────────────────────────────────────────────┘
```

### 5.5 עמוד 4: פרטיות מודל והגנת נתונים (Model Privacy & Data Protection)

**אסטרטגיה מרובדת:**

| טכניקה | מנגנון | יישום ב-AMAS |
|--------|--------|-------------|
| **Differential Privacy (DP)** | הוספת רעש מכויל לנתוני אימון/הסקה | DP-SGD + epsilon budget בין סוכנים |
| **Anonymization** | הסרת מידע מזהה | pseudonymization לפני שיתוף בין סוכנים |
| **Data Minimization** | הגבלת היקף, גרנולריות, משך | ניקוי memory buffers אחרי task completion |
| **Secure MPC** | חישוב משותף על נתונים מוצפנים | PUMA framework: inference על מודל 7B בדקות |
| **Homomorphic Encryption (HE)** | חישוב על ciphertext | LoRA fine-tuning + Gaussian kernels ל-FHE |
| **TEEs** | בידוד חומרתי (Intel SGX, AMD SEV, Arm TrustZone) | LLM inference רק בתוך enclaves מאומתים |

**עקרון Privacy-by-Design:** ארכיטקטורות AMAS חדשות מטמיעות consent layers, configurable privacy settings, ומודולי redaction בזיכרון.

### 5.6 עמוד 5: ממשל (Governance)

**מסגרות רגולטוריות מרכזיות:**

```
┌────────────────────────────────────────────────────────────────┐
│  EU AI Act (Article 14): Human Oversight                       │
│  → מערכות high-risk חייבות לאפשר פיקוח אנושי                  │
│  → stop mechanism, anomaly detection, interpretable outputs    │
│                                                                │
│  OECD AI Principles (2024):                                    │
│  → שקיפות, הסברתיות, חוסן, בטיחות, accountability             │
│  → mechanisms to override or decommission systems              │
│                                                                │
│  NIST AI RMF:                                                  │
│  → Govern, Map, Measure, Manage                                │
│  → gradient-based attributions, occlusion tests                │
│  → counterfactual prompting for transparency                   │
│                                                                │
│  Auditability:                                                 │
│  → auditable logs of agent actions, decisions, data flows      │
│  → clear roles (reasoning, verification, summarization)        │
│  → RBAC prevents unauthorized agents from sensitive functions  │
│                                                                │
│  Global Harmonization:                                         │
│  → GDPR, CCPA: data-subject rights, consent, privacy-by-design│
│  → OECD + NIST: international cooperation                     │
└────────────────────────────────────────────────────────────────┘
```

### 5.7 טבלת מיפוי TRiSM Pillars — בקרות, טכניקות וסיכונים

| עמוד TRiSM | בקרות ליבה | טכניקות/דפוסים | סיכונים שנמנעים |
|-------------|-----------|----------------|-----------------|
| **Explainability** | CoT logging, inter-agent traceability, provenance | Layered-CoT, LIME/SHAP, decision-provenance graphs | שרשראות אטומות, reasoning לא ניתן לאימות |
| **ModelOps** | Versioning, CI/CD safety gates, hierarchical monitoring | Prompt & agent-config versioning, sandbox simulation | drift שקט, bias re-introduction, cost blowouts |
| **App Security** | Prompt hygiene, sandboxed tools, least privilege, RBAC | Prompt-injection patterns, plan-then-execute, HITL holds | prompt injection, data exfiltration, lateral movement |
| **Privacy** | DP, anonymization, MPC, HE/FHE, TEEs | DP budgets, k-anonymity, MPC/PUMA pipelines, PII detectors | memorization, shared memory leakage, unauthorized access |
| **Governance** | Human oversight, accountability, DPIA, auditability | Oversight playbooks, two-person verification, audit trails | weak responsibility, non-compliance, opaque decisions |

---

## 6. מטריקות הערכה חדשות — CSS ו-TUE

### 6.1 מסגרת ההערכה — חמישה ממדים

המאמר מציע **5 ממדי הערכה** לצד שתי מטריקות חדשות:

| ממד | מוקד | מטריקות |
|-----|------|---------|
| **Trustworthiness** | אמינות, בטיחות, alignment | robustness, violation rate, calibration |
| **Explainability** | שקיפות, עקיבות | coverage, faithfulness, fidelity, stability |
| **User-Centered** | חוויית משתמש | CSAT, goal-fulfillment rate, coherence |
| **Coordination** | שיתוף פעולה בין סוכנים | team success rate, communication efficiency |
| **Composite** | ציון מצטבר | weighted scores, tool-use efficacy |

### 6.2 מדד אמינות מנורמל (Trustworthiness Index)

**נוסחה (1):**

```
        w_acc · A + w_rob · R + w_align · L
T  =  ─────────────────────────────────────
                  1 + λ · V
```

**כאשר:**
- `A` = הצלחת משימה מכוילת (accuracy adjusted for calibration)
- `R` = חוסן (robustness) תחת שינויי distribution
- `L` = alignment/safety compliance (1 - violation rate), מנורמל ל-[0,1]
- `V >= 0` = penalty term עבור הפרות (violation/self-serving), ככל שגבוה יותר → גרוע יותר
- `w_acc + w_rob + w_align = 1` — משקולות
- `λ >= 0` — קובע כמה חזק הפרות "מענישות" את ציון האמון

**מטאפורה:** דמיינו ציון אשראי — גם אם יש לכם הכנסה גבוהה (`A`) וחסכונות (`R`), אם יש לכם הפרות חוק (`V`), הציון יורד בצורה דרמטית.

### 6.3 מטריקה מרוכבת (Composite Metric)

**נוסחה (2):**

```
M_comp = ω_T · M_T + ω_E · M_E + ω_U · M_U + ω_Co · M_Co
```

**כאשר:**
- `M_T, M_E, M_U, M_Co ∈ [0,1]` = ציונים מנורמלים ל-trustworthiness, explainability, user-centered, coordination
- `ω_* >= 0` עם `Σω_* = 1` — משקולות לפי domain priorities

**אזהרה חשובה:** scalarization (חיבור לציון יחיד) יכול **להסתיר כשלים** בממד בודד. לכן המאמר ממליץ **תמיד** לדווח את הווקטור המלא:

```
M = (M_T, M_E, M_U, M_Co)
```

ולבחור מודלים לפי:
1. **Thresholds** — `M_T >= τ_T` ו-`M_Co >= τ_Co` (סף מינימלי לכל ממד)
2. **Pareto-optimality** — מודלים non-dominated (אי אפשר לשפר ממד אחד בלי לפגוע באחר)

### 6.4 Component Synergy Score (CSS) — מטריקה חדשה

**מטרה:** לכמת את **איכות שיתוף הפעולה** בין סוכנים — עד כמה פעולות של סוכן אחד **מאפשרות ומשפרות** את הביצועים של סוכן אחר.

**נוסחה (4):**

```
         1
CSS = ──────── Σ_i Σ_{j≠i} [ Impact(a_i → a_j) · Quality(a_j | a_i) ]
       N_pairs
```

**כאשר:**
- `N_pairs` = מספר זוגות סוכנים מסודרים `(i, j)` בהערכה
- `Impact(a_i → a_j)` = כמה `a_i` שינה את הביצועים של `a_j` (שיפור יחסי)
- `Quality(a_j | a_i)` = איכות הפלט של `a_j` בהתניה על תרומת `a_i`

**דוגמה מוחשית — מערכת פיתוח תוכנה:**

```
AMAS: Planner → Coder → Tester

Link 1: Planner → Coder
  Impact = 0.35  (הפירוק של Planner מאיץ את Coder ב-35%)
  Quality = 0.92 (Coder מייצר קוד ב-92% איכות)
  → Contribution = 0.35 × 0.92 = 0.322

Link 2: Coder → Tester
  Impact = 0.40  (הקוד של Coder מאפשר ל-Tester לכסות 40% יותר)
  Quality = 0.88 (Tester מזהה 88% מהבאגים)
  → Contribution = 0.40 × 0.88 = 0.352

CSS = (0.322 + 0.352) / 2 = 0.337

→ CSS = 0.337 — שיתוף פעולה בינוני-טוב
→ שיפור אפשרי: חיזוק הקשר Planner→Coder
```

### 6.5 Tool Utilization Efficacy (TUE) — מטריקה חדשה

**מטרה:** להעריך **עד כמה נכון ויעיל** סוכנים משתמשים בכלים חיצוניים (APIs, databases, code interpreters).

**5 רכיבים:**

| רכיב | טווח | מה מודד |
|------|------|---------|
| **Sel** (Selection) | [0,1] | precision/recall בבחירת כלי |
| **Arg** (Argument validity) | [0,1] | האם הפרמטרים תקינים (well-formed) |
| **Exec** (Execution success) | [0,1] | האם הקריאה הצליחה (ללא errors/timeouts) |
| **Out** (Outcome correctness) | [0,1] | האם תוצאת ה-task נכונה (downstream) |
| **Eff** (Efficiency) | [0,1] | הפוך מנורמל של latency/tokens/cost |

**נוסחה (5) — Linear aggregator:**

```
TUE_lin = α_s · Sel + α_a · Arg + α_e · Exec + α_o · Out + α_f · Eff
```

**כאשר** `α_* >= 0` ו-`Σα_* = 1`.

**מטאפורה:** TUE הוא כמו ציון נהיגה:
- `Sel` = האם בחרת את הנתיב הנכון?
- `Arg` = האם הגדרת את ה-GPS נכון?
- `Exec` = האם הגעת בלי תאונות?
- `Out` = האם הגעת ליעד הנכון?
- `Eff` = האם הגעת בזמן סביר ובלי לבזבז דלק?

---

## 7. אבטחה ופרטיות — הגנה בעומק

### 7.1 מנגנוני אבטחה

| מנגנון | תיאור | יישום ב-AMAS |
|--------|-------|-------------|
| **Encryption** | SSL/TLS, HE, secure enclaves | הגנה על handoffs בין סוכנים |
| **Access Control** | RBAC + ABAC | per-agent permissions, dynamic trust levels |
| **Adversarial Learning** | adversarial training, reward shaping, contrastive learning | חיסון נגד prompt injection |
| **Runtime Monitoring** | LSTM/autoencoder anomaly detection, trust scoring | זיהוי real-time של סוכנים חריגים |

**דוגמה — Microsoft Copilot:** governance layers מנטרים agent behavior anomalous לאורך sessions.

### 7.2 טכניקות שימור פרטיות

```
┌──────────────────────────────────────────────────────────────┐
│            Privacy-Preserving for AMAS                        │
│                                                              │
│  1. Differential Privacy (DP)                                │
│     ├── DP-SGD with ε budget per agent pair                  │
│     └── limits what agents can reveal to each other          │
│                                                              │
│  2. Data Minimization                                        │
│     ├── clear temporary memory buffers after subgoal         │
│     ├── anonymize before passing between agents              │
│     └── strict retention policies                            │
│                                                              │
│  3. Secure Computation                                       │
│     ├── SMPC: joint computation without data exposure        │
│     ├── HE: arithmetic on encrypted RAG vectors              │
│     └── TEEs: isolated hardware enclaves for inference       │
│                                                              │
│  4. Privacy-by-Design                                        │
│     ├── user consent layers                                  │
│     ├── configurable privacy settings                        │
│     └── memory redaction modules                             │
└──────────────────────────────────────────────────────────────┘
```

### 7.3 Benchmarks להערכת אבטחה

| Benchmark | כיסוי התקפות | מטריקות | עמודי TRiSM | מגבלות |
|-----------|-------------|---------|-------------|--------|
| **HarmBench** | Prompt injection, jailbreaks | ASR, robustness | Security, Explainability | מוגבל ל-multi-agent |
| **ToolBench** | Tool misuse, unauthorized API | Effectiveness, FP/FN | Security, Privacy | tool-focused בלבד |
| **AgentBench** | Multi-step attacks, coordination | Task success, compliance | All pillars | adversarial מוגבל |
| **GAIA** | Ambiguous instructions, reasoning | Completion, safety | Explainability, Governance | שלב מוקדם |
| **WebArena** | Web attacks, malicious content | Success, safety | Security, Privacy | domain-specific |
| **HELM** | Robustness, fairness, bias | Comprehensive | ModelOps, Governance | לא agent-specific |
| **MLCommons** | Harmful content, privacy leakage | Safety scores | Security, Privacy, Governance | מתפתח |

---

## 8. ממשל ואכיפה — מהתקנות לפרקטיקה

### 8.1 מיפוי governance controls

המאמר מציג **טבלה מפורטת** (Table 7) שממפה כל בקרת governance ל:
- **עמוד TRiSM** → **Control** → **Operationalization** → **Evidence/Artifacts** → **Standards**

**דוגמאות מרכזיות:**

| עמוד | בקרה | איך מפעילים | ראיות | תקנים |
|------|------|-------------|-------|-------|
| Governance | Org. accountability | RACI owners, approvals for high-impact | RACI records, change approvals | NIST AI RMF, ISO/IEC 42001 |
| Governance | Policy-as-code | allow/deny rules in orchestration | Policy repository, gate logs | EU AI Act Arts. 11-14 |
| Risk Mgmt | Risk register & AIA | Hazard/threat enumeration, likelihood scoring | Risk register, AIA reports | ISO/IEC 23894, 42005 |
| Security | Tool access control | RBAC/ABAC per agent/role, API tokens, allowlists | Access matrices, token scopes | NIST SP 800-218/218A |
| Security | Isolation/sandboxing | Containers/VMs, syscall/network/file egress policies | Sandbox configs, egress policy | NIST SP 800-218A, TEEs |
| Privacy | DP budgeting & consent | Differential privacy budgets, data-subject rights flows | DP budget ledger, DSR tickets | GDPR Art. 25, OECD |
| Traceability | Provenance & logging | Log prompts, plans, tool calls, I/O, timestamps, agent role | Immutable logs (WORM), signed artifacts | EU AI Act Arts. 12-13 |

### 8.2 Auditability — ביקורת ב-AMAS

AMAS מייצרים **התנהגויות מתגלות ואטומות** — מבקרים חייבים לשחזר את שרשרת ההחלטות:

- **Comprehensive logging** — prompts, plans, actions, tool calls, I/O, timestamps, agent role/identity, model hashes
- **Action traceability** — decision provenance: planner→coder→tester, link every external effect to proposing/approving principal
- **Role-granular trails** — tag entries by agent role, require countersignatures for high-impact actions
- **Immutability** — append-only, tamper-evident storage (WORM buckets, cryptographic sealing)

### 8.3 Policy Enforcement — אכיפת מדיניות בזמן אמת

- **Orchestrator-level controls** — meta-controller שאוכף allow/deny policies על plans ו-tool calls
- **Memory & retention** — TTLs, redaction, scoped memory (task- and tenant-scoped)
- **Tool & data access** — RBAC/ABAC, per-tool API tokens, environment scoping (dev/stage/prod)
- **Isolation** — containers/VMs עם syscall/network/file egress policies, TEEs for sensitive workloads
- **I/O mediation** — content filters, egress controls, detect PII/PHI/secrets before release
- **Real-time monitoring** — anomaly signals, runtime kill-switches, rollbacks, incident triggers

---

## 9. דיון — תובנות, מגבלות וכיוונים עתידיים

### 9.1 השלכות טכניות של TRiSM על עיצוב AMAS

**רעיון "Guardian Agents":** במקום להתייחס לסוכני LLM כקופסאות שחורות, TRiSM מעודד תכנון של **סוכני שמירה מתמחים** שמסננים נתונים רגישים, מבססים baselines של התנהגות תקינה, ואוכפים policies בזמן ריצה.

**"Excessive Agency":** סוכנים אוטונומיים מדי עם גישה רחבה לכלים עלולים לגרום נזק לא מכוון (hallucination-driven execution, misinterpreted goals). TRiSM מציע:
- הפרדת תפקידים (role separation)
- הרשאות מצומצמות (scoped permissions)
- אילוצי בטיחות (safety constraints)

### 9.2 היבטים אתיים וחברתיים

- **Accountability** — TRiSM governance דורש שארגונים ישמרו אחריות על פעולות AI
- **Human-in-the-Loop** — TRiSM לא מסיר אנשים מהלולאה; הוא **מבנה** את שיתוף הפעולה אדם-סוכן
- **User Complacency** — סיכון שמשתמשים יסמכו עיוורות על סוכנים אוטונומיים → TRiSM מתנגד לזה דרך oversight רשמי

### 9.3 אתגרי יישום בעולם האמיתי

```
┌────────────────────────────────────────────────────────────────┐
│              Implementation Challenges                         │
│                                                                │
│  1. Computational Overhead                                     │
│     continuous monitoring + validation + anomaly detection      │
│     → latency & cost impact on user experience                 │
│                                                                │
│  2. Scale                                                      │
│     enterprise: 100s-1000s of agents                           │
│     → compute, storage, networking, staffing costs             │
│                                                                │
│  3. Legacy Integration                                         │
│     existing infrastructure not designed for agentic security  │
│     → cross-component changes, ongoing maintenance             │
│                                                                │
│  4. Alert Fatigue                                              │
│     monitoring produces high volume of alerts (incl. false +)  │
│     → may overwhelm security teams                             │
│                                                                │
│  5. Phased Adoption Strategy:                                  │
│     Start: input validation, restricted tool access, logging   │
│     Then: add stronger controls as maturity increases           │
└────────────────────────────────────────────────────────────────┘
```

### 9.4 התאמה לרגולציה

TRiSM מתיישר עם:
- **EU AI Act** — risk management, transparency, data governance, human oversight
- **NIST AI RMF** — Govern, Map, Measure, Manage
- **ISO/IEC 42001** — AI management systems

**פערים שנותרו:**
- אין benchmarks סטנדרטיים להערכת AMAS תחת עקרונות TRiSM
- רוב הבקרות נבדקו רק בסביבות מעבדה, לא בפריסות אמיתיות
- adversarial learning נשאר מרוץ חימוש מתמיד

### 9.5 מפת דרכים עתידית

```
             ┌───────────────────┐
        ┌────│  Ethics &         │────┐
        │    │  Governance       │    │
        │    └───────────────────┘    │
   ┌────┴──────┐            ┌────────┴────────┐
   │ Autonomous│            │ Controllability  │
   │ Lifecycle │            │                  │
   │ Management│            │                  │
   └────┬──────┘            └────────┬────────┘
        │    ┌───────────────────┐    │
        │    │   Agentic AI      │    │
        └────│   Roadmap         │────┘
             └──┬──────────┬────┘
        ┌───────┴──┐  ┌───┴────────────┐
        │Explainable│  │ Benchmarking   │
        │Multi-Agent│  │ & Evaluation   │
        │Decisions  │  │                │
        └───────┬──┘  └───┬────────────┘
                │  ┌──────┴──────────┐
                └──│ Cognitive       │
                   │ Capability      │
                   │ Expansion       │
                   └─────────────────┘
```

**כיוונים קונקרטיים:**
1. **Open benchmarks** — סביבות תרחישים עם איומים ודילמות אתיות מובנים
2. **Cross-disciplinary collaboration** — security experts + LLM researchers → anomaly detectors, robust tool APIs
3. **Red-team/Blue-team exercises** — "cyber wargames" ל-AMAS
4. **Better HCI** — dashboards שמציגים agent society state, flagging, rollback
5. **Regulatory sandboxes** — סביבות בדיקה לניסויי multi-agent בקנה מידה
6. **Multimodal & Embodied Agents** — הרחבת TRiSM לסוכנים multimodal (LLaVA, GPT-4V) ו-embodied (רובוטים)

---

## 10. מגבלות המאמר

| מגבלה | פירוט |
|-------|-------|
| **מאמר סקירה, לא מחקר אמפירי** | אין ניסויים, אין validation מעשית של CSS/TUE |
| **CSS ו-TUE לא נבדקו** | המטריקות מוצעות תיאורטית בלבד — אין results |
| **משקולות subjective** | ב-M_comp ו-TUE, בחירת ω/α תלויה ב-domain ואין הנחיה ברורה |
| **Goodhart's Law** | מטריקות composite ניתנות ל-gaming — מערכות עלולות לאופטם לציון ולא ליכולת |
| **חסר evaluation בעולם האמיתי** | רוב הבקרות נבדקו רק ב-lab settings |
| **Adversarial arms race** | TRiSM מניח שאפשר להגן — אבל תוקפים מסתגלים |
| **Emergent behaviors חמקמקים** | behavioral drift קשה לתפוס עם protocols נוכחיים |
| **Human-centered evaluation** | costly, doesn't scale, high variance |
| **LLM-centric** | לא מכסה סוכנים multimodal או embodied לעומק |

---

## 11. תרומות מרכזיות — סיכום

1. **מסגרת TRiSM אחודה ל-Agentic AI** — ראשונה שמשלבת 5 עמודים (Explainability, ModelOps, Application Security, Model Privacy, Governance) ומקשרת לאתגרים ייחודיים של AMAS

2. **טקסונומיית סיכונים ל-AMAS** — 4 קטגוריות (adversarial attacks, data leakage, agent collusion, emergent behaviors) עם דוגמאות מעשיות ומיפוי לבקרות

3. **שתי מטריקות חדשות:**
   - **CSS** — Component Synergy Score למדידת איכות שיתוף פעולה בין סוכנים
   - **TUE** — Tool Utilization Efficacy למדידת נכונות ויעילות שימוש בכלים

4. **תבנית הערכה הוליסטית** — 5 ממדים (trustworthiness, explainability, user-centered, coordination, composite) עם נוסחאות מנורמלות

5. **מיפוי טכניקות ופערים** — survey שיטתי של explainability, prompt hygiene, sandboxing, ModelOps ומיפויים ל-AMAS

6. **מיפוי governance** — טבלה מפורטת (Table 7) שממפה TRiSM pillars ← controls ← operationalization ← evidence ← standards

---

## 12. רלוונטיות לתזה — MCP Risk Scoring System

### 12.1 קשר ישיר למערכת ציון סיכון דינמי

המאמר הזה הוא **מסגרת תיאורטית קריטית** לתזה שלך. הוא מספק את ה-**"למה"** ואת ה-**"מה"** של ניהול אמון וסיכון, בעוד התזה שלך (MCP-RSS) מספקת את ה-**"איך"**.

```
TRiSM (המאמר הזה):
  "צריך מסגרת אחודה לניהול אמון, סיכון ואבטחה ב-AMAS"
  → מספק taxonomy, pillars, metrics (CSS, TUE, T, M_comp)
  → אבל: אין מימוש, אין validation, אין ציון דינמי

MCP-RSS (התזה שלך):
  "נבנה מערכת ציון סיכון דינמי (1-10) לסוכני MCP"
  → מספק מימוש קונקרטי, real-time scoring
  → משתמש ב-TRiSM כמסגרת תיאורטית
```

### 12.2 מטריקות TRiSM → ציון סיכון דינמי

ניתן **למפות ישירות** את מטריקות ה-TRiSM לציון ה-1-10 שלך:

```python
# TRiSM Trustworthiness Index → MCP-RSS risk component
def trism_to_risk_score(T, CSS, TUE):
    """
    Map TRiSM metrics to dynamic 1-10 risk score.

    T    = Trustworthiness index (0-1, higher = more trustworthy)
    CSS  = Component Synergy Score (0-1, higher = better collaboration)
    TUE  = Tool Utilization Efficacy (0-1, higher = better tool use)
    """
    # Invert: TRiSM measures trust (higher=good),
    # MCP-RSS measures risk (higher=bad)
    trust_risk = (1 - T) * 10         # Low trust → high risk
    synergy_risk = (1 - CSS) * 10     # Poor synergy → may indicate collusion
    tool_risk = (1 - TUE) * 10        # Poor tool use → may indicate misuse

    # Weighted combination (weights from domain)
    risk_score = (
        0.40 * trust_risk +           # Trust is primary
        0.25 * tool_risk +            # Tool misuse is key for MCP
        0.20 * synergy_risk +         # Coordination quality
        0.15 * explainability_risk    # How transparent is the agent
    )

    return min(10, max(1, round(risk_score)))
```

### 12.3 טקסונומיית סיכונים → threat vectors ב-MCP

| סיכון TRiSM | ביטוי ב-MCP | ציון סיכון |
|-------------|-------------|-----------|
| Prompt injection | סוכן שולח tool descriptions עם הוראות זדוניות | 8-10 |
| Data leakage | סוכן מבקש גישה לנתונים מחוץ ל-scope | 7-9 |
| Agent collusion | סוכנים מתאמים כדי לעקוף safety guards | 9-10 |
| Tool misuse | קריאות API לא מורשות, parameter abuse | 6-9 |
| Memory poisoning | סוכן כותב מידע מזיק לזיכרון משותף | 7-10 |
| Autonomy abuse | סוכן מרחיב הרשאות מעבר למה שנדרש | 8-10 |
| Emergent drift | התנהגות שמשתנה לאורך זמן | 5-8 |

### 12.4 חמשת עמודי TRiSM → שכבות ב-MCP-RSS

```
┌──────────────────────────────────────────────────────────────────┐
│           MCP-RSS Architecture (inspired by TRiSM)              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 5: Governance Score                               │   │
│  │  → compliance check, audit trail, human override rules   │   │
│  │  → Input to: final risk decision (allow/restrict/deny)   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Layer 4: Trust & Explainability Score                   │   │
│  │  → can the agent explain its requests?                   │   │
│  │  → reasoning trace quality, provenance                   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Layer 3: Privacy & Data Protection Score                │   │
│  │  → data access scope, PII exposure risk                  │   │
│  │  → memory access patterns, retention compliance          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Layer 2: Application Security Score (= TUE-based)       │   │
│  │  → tool selection correctness, argument validity          │   │
│  │  → execution safety, outcome verification                │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Layer 1: Lifecycle Score (= ModelOps)                    │   │
│  │  → version tracking, drift detection, rollback capability │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Output: Risk Score 1-10 (dynamic, updated per interaction)     │
│  → 1-3: Allow | 4-6: Restrict | 7-10: Deny/Escalate           │
└──────────────────────────────────────────────────────────────────┘
```

### 12.5 נקודות ציטוט חשובות לתזה

1. **הצדקת הגישה הדינמית:** "Accuracy alone is insufficient for Agentic AI, where failures often arise from coordination breakdowns, unsafe tool use, or misaligned autonomy rather than incorrect predictions" — מחזק את הטענה שציון בינארי (allow/deny) לא מספיק

2. **הצדקת multi-dimensional scoring:** נוסחאות T, M_comp, CSS, TUE מספקות בסיס מתמטי לציון רב-ממדי — בדיוק מה שאתה צריך

3. **Phased adoption:** ההמלצה להתחיל עם input validation ו-logging ולהוסיף בקרות בהדרגה — מתאים לגישת Lenovo (cost, speed, practicality)

4. **Goodhart's Law warning:** אזהרה שציונים composite ניתנים ל-gaming — חשוב לציין ולהציע mitigation בתזה

5. **Gap שאתה ממלא:** המאמר מציע CSS/TUE אבל **לא מממש אותם**. התזה שלך יכולה להיות ה-**first implementation** של מטריקות אלו בהקשר MCP

### 12.6 מה לקחת מהמאמר הזה לתזה

| תרומת המאמר | שימוש בתזה שלך |
|-------------|----------------|
| 5 TRiSM pillars | 5 שכבות ב-MCP-RSS architecture |
| Trustworthiness formula (T) | בסיס לחישוב trust component ב-risk score |
| CSS metric | מדד לשיתוף פעולה — רלוונטי כשסוכנים מרובים ניגשים ל-MCP |
| TUE metric | מדד לשימוש בכלים — **ישירות רלוונטי** ל-MCP tool calls |
| Risk taxonomy | threat vectors לזיהוי ב-MCP-RSS |
| Governance mapping (Table 7) | compliance framework ל-MCP-RSS |
| Phased adoption | אסטרטגיית פריסה מדורגת — מתאים ל-Lenovo constraints |
| Evaluation dimensions | מבנה ל-evaluation methodology של MCP-RSS |

**שורה תחתונה:** המאמר הזה הוא ה-**survey הכי מקיף** שקיים על TRiSM ל-AMAS. הוא מספק מסגרת תיאורטית, טקסונומיית סיכונים, ומטריקות — כולם ישירות שמישים כבסיס אקדמי לתזת MCP-RSS. היתרון שלך: אתה ממש **מממש** את מה שהם רק מציעים.
