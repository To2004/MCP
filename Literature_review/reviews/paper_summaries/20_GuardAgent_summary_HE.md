# GuardAgent: הגנה על סוכני LLM באמצעות סוכן שומר המבוסס על היסק מונחה-ידע

**מאמר מאת:** Zhen Xiang, Linzhi Zheng, Yanjie Li, Junyuan Hong, Qinbin Li, Han Xie, Jiawei Zhang, Zidi Xiong, Chulin Xie, Carl Yang, Dawn Song, Bo Li
**מוסדות:** University of Georgia, University of Chicago, UIUC, UT Austin, UC Berkeley, Emory University, Virtue AI
**arXiv:2406.09187v3** | מאי 2025
**עמוד פרויקט:** https://guardagent.github.io/

---

## 1. הבעיה המרכזית -- למה guardrails קיימים לא מספיקים לסוכני AI?

### התובנה המרכזית

סוכני AI מבוססי LLM (Large Language Models) פועלים בתחומים רגישים כמו בריאות, פיננסים, נהיגה אוטונומית וגלישה באינטרנט. בניגוד ל-LLMs רגילים שמייצרים **טקסט בלבד**, סוכנים מייצרים **פעולות** -- לחיצה על כפתור, שליפת מידע ממסד נתונים, הרצת קוד. המנגנונים הקיימים להגנה על LLMs (כמו LlamaGuard) מתמקדים ב**סינון תוכן טקסטואלי** (אלימות, תוכן מיני, וכו') ולא מבינים את ה**הקשר הפעולתי** של סוכנים.

### המטאפורה: "הפקח בכניסה לבניין רפואי"

דמיינו בית חולים גדול עם מערכת מידע ממוחשבת:

```
בית החולים (מערכת המידע)
    |
    +-- רופא מבקש: "תראה לי את תוצאות הדם של מטופל 39354"
    |   --> מותר! רופא רשאי לגשת למאגר 'lab' ו-'patient'
    |
    +-- אחות מבקשת: "תראה לי את האבחנות של מטופל 39354"
    |   --> אסור! אחות לא רשאית לגשת למאגר 'diagnosis'
    |
    +-- פקידת מנהלה מבקשת: "תראה לי את המשקל של מטופל 39354"
    |   --> אסור! מנהלה לא רשאית לגשת למאגר 'patient' (עמודות רגישות)
    |
    +-- [שומר הכניסה הנוכחי: LlamaGuard]
        --> בודק רק: "האם הטקסט מכיל אלימות/פורנו?"
        --> לא מבין הרשאות! לא מבין תפקידים! לא מבין מסדי נתונים!
```

**GuardAgent = פקח חכם** שמבין:
1. **מי מבקש** -- זיהוי התפקיד (רופא/אחות/מנהלה)
2. **מה מבקשים** -- ניתוח הפעולה המבוקשת (איזה מסד נתונים, איזו עמודה)
3. **האם מותר** -- בדיקה מול כללי הרשאה מוגדרים מראש
4. **תגובה מדויקת** -- אישור או דחייה עם הסבר (למשל: "מסד הנתונים 'diagnosis' אינו נגיש לאחות")

---

## 2. תרומות המאמר -- מה חדש כאן?

### 2.1 ארבע תרומות מרכזיות

| # | תרומה | משמעות |
|---|--------|--------|
| 1 | **פריימוורק GuardAgent** | הסוכן הראשון שתוכנן כ-guardrail לסוכני LLM אחרים (לא ל-LLMs בודדים) |
| 2 | **עיצוב מבוסס-קוד** | במקום guardrail טקסטואלי (natural language), GuardAgent מייצר **קוד Python** שרץ דטרמיניסטית |
| 3 | **למידה מהקשר (In-Context Learning)** | לא דורש אימון נוסף -- משתמש ב-LLM קיים (GPT-4, Llama) עם דוגמאות בזיכרון |
| 4 | **שני benchmarks חדשים** | EICU-AC (בקרת גישה רפואית) ו-Mind2Web-SC (בקרת בטיחות לסוכני אינטרנט) |

### 2.2 שלוש תכונות עיצוב מרכזיות

- **גמישות (Flexibility):** GuardAgent פועל "במקביל" לסוכן המטרה (non-invasive) -- לא משנה את הקוד של הסוכן, לא דורש שילוב פנימי. ניתן להוסיף פונקציות חדשות ל-toolbox ודוגמאות חדשות לזיכרון.
- **אמינות (Reliability):** הפלט הסופי מתקבל מ**הרצת קוד**, לא מתגובה טקסטואלית של LLM. קוד הוא דטרמיניסטי -- אותו קלט תמיד ייתן אותה תוצאה.
- **ללא אימון (Training-Free):** משתמש ב-in-context learning עם דוגמאות מזיכרון, ולא דורש fine-tuning על נתונים חדשים.

---

## 3. הארכיטקטורה של GuardAgent -- הפרטים הטכניים

### 3.1 סקירת המערכת

```
                      קלטים ל-GuardAgent
                      ==================
+-------------------+  +-------------------+  +-------------------+
| I_s: מפרט הסוכן  |  | I_r: בקשות       |  | I_i, I_o: קלט     |
| (איך הסוכן עובד,  |  | בטיחות/הרשאות    |  | ופלט של הסוכן      |
|  פורמט הפלטים,    |  | (כללי access     |  | המטרה (מה המשתמש  |
|  פונקציות זמינות) |  |  control, safety  |  |  ביקש ומה הסוכן    |
+-------------------+  |  policies)        |  |  עשה/החזיר)        |
         |              +-------------------+  +-------------------+
         |                       |                       |
         +-----------+-----------+-----------+-----------+
                     |
                     v
    +========================================+
    |         שלב I: תכנון משימה              |
    |         (Task Planning)                 |
    |                                         |
    |  LLM + דוגמאות מזיכרון (D_1...D_k)     |
    |           |                             |
    |           v                             |
    |  P = תוכנית פעולה צעד-אחר-צעד          |
    |  (p_1: זהה מילות מפתח                  |
    |   p_2: סנן מידע רלוונטי מ-I_r          |
    |   p_3: סכם את פלט הסוכן                |
    |   p_4: הנח לייצר קוד guardrail)        |
    +========================================+
                     |
                     v
    +========================================+
    |    שלב II: יצירת קוד והרצה             |
    |    (Code Generation and Execution)      |
    |                                         |
    |  LLM + toolbox (F) + דוגמאות           |
    |           |                             |
    |           v                             |
    |  C = קוד guardrail ב-Python            |
    |           |                             |
    |           v                             |
    |  Execution Engine (E) -- הרצת הקוד     |
    |           |                             |
    |      +----+----+                        |
    |      |         |                        |
    |      v         v                        |
    |  O_l = 0    O_l = 1                     |
    |  (אושר)    (נדחה + O_d = סיבה)         |
    +========================================+
                     |
                     v
            +---------------+
            | Admitted (0)  |  --> הסוכן ממשיך לפעול, הפלט מועבר למשתמש
            | Denied   (1)  |  --> הפעולה נחסמת, מוצגת סיבת הדחייה
            +---------------+
```

### 3.2 הגדרות פורמליות

**קלטים חובה של GuardAgent:**

| סימון | שם | תיאור | דוגמה |
|-------|----|--------|-------|
| `I_s` | מפרט הסוכן (Specification) | תיאור הסוכן המטרה -- מה הוא עושה, איך הוא פועל, פורמט הפלט | "סוכן רפואי שמייצר קוד Python לשליפת מידע מ-10 מסדי נתונים" |
| `I_r` | בקשות בטיחות (Safety Guard Requests) | כללי ההרשאה/בטיחות שיש לאכוף | "שלושה תפקידים: רופא, אחות, מנהלה. לכל תפקיד -- רשימת מסדי נתונים נגישים" |
| `I_i` | קלט לסוכן (Agent Input) | מה המשתמש ביקש מהסוכן | "זהות: מנהלה כללית. שאלה: מה היה ערך MCHC בבדיקת דם של מטופל 39354?" |
| `I_o` | פלט הסוכן (Agent Output) | הפלט המלא כולל reasoning, קוד, ותשובה | "Knowledge: ... Generated code: LoadDB('patient')... Answer: 42" |

**פלטים:**

```
O_l = 0  -->  בקשות הבטיחות מתקיימות, הפעולה מאושרת
O_l = 1  -->  בקשות הבטיחות מופרות, הפעולה נדחית
O_d      -->  הסיבה המפורטת (למשל: "מסדי נתונים לא נגישים: diagnosis")
```

---

### 3.3 שלב I: תכנון משימה (Task Planning)

#### הבעיה: למה לא פשוט לתת ל-LLM את הכל ולשאול?

גישה נאיבית: לתת ל-LLM את `[I_p, I_s, I_r, I_i, I_o]` ולבקש ממנו להחליט.

**למה זה לא עובד:** בקשות בטיחות מורכבות דורשות הבנה עמוקה. LLM שמקבל prompt ארוך עם כללי הרשאה מסובכים עלול "לשכוח" פרטים, לבלבל בין תפקידים, או להחליט לא נכון.

**הפתרון -- Chain-of-Thought + דוגמאות מזיכרון:**

GuardAgent משתמש ב**מודול זיכרון** (Memory Module) שמאחסן דוגמאות מעשיות מהעבר. כל דוגמה בזיכרון מכילה:

```
D = [I_{i,D}, I_{o,D}, P_D, C_D]

כאשר:
  I_{i,D}  = קלט לדוגמה (מה המשתמש ביקש)
  I_{o,D}  = פלט לדוגמה (מה הסוכן עשה)
  P_D      = תוכנית הפעולה (4 צעדים)
  C_D      = קוד ה-guardrail שנוצר
```

**שליפה מהזיכרון:** נבחרות `k` דוגמאות עם **מרחק Levenshtein הקטן ביותר** בין `[I_i, I_o]` הנוכחי לבין `[I_{i,D}, I_{o,D}]` בזיכרון.

```
P = LLM([I_p, I_s, I_r, D_1, ..., D_k, I_i, I_o])
```

#### ארבעת הצעדים בתוכנית הפעולה (Chain-of-Thought)

כל תוכנית פעולה `P_D = [p_1, p_2, p_3, p_4]` כוללת:

| צעד | מה עושים | דוגמה (EICU-AC) | דוגמה (Mind2Web-SC) |
|-----|----------|-----------------|---------------------|
| `p_1` | סיכום מילות מפתח מ-`I_r` | "זוהתה משימת access control עם 3 תפקידים: physician, nursing, general administration" | "זוהתה משימת safety control עם רשימת כללים" |
| `p_2` | סינון מידע רלוונטי מ-`I_r` שקשור לקלט הסוכן | "התפקיד הוא nursing. המסדים הנגישים הם: allergy, medication, patient..." | "הפעולה היא Book a hotel. הכלל הרלוונטי: גיל מתחת ל-18 לא יכול להזמין מלון" |
| `p_3` | סיכום פלט הסוכן ומציאת מה רלוונטי ל-guard request | "הסוכן ניגש למסדי נתונים: patient, diagnosis, medication" | "הסוכן לחץ על כפתור 'Book Now'" |
| `p_4` | הנחיה ליצירת קוד guardrail שמשווה `p_2` ל-`p_3` | "צור קוד שבודק אם כל המסדים שהסוכן ניגש אליהם נמצאים ברשימה המותרת" | "צור קוד שבודק אם פרופיל המשתמש עומד בכלל הרלוונטי" |

#### דוגמה קונקרטית לתוכנית פעולה (EICU-AC)

```
תוכנית פעולה שנוצרה על ידי GuardAgent:
=========================================

p_1: זוהתה משימת "access control" עם שלושה תפקידים:
     Physician, Nursing, General Administration.

p_2: זהות המשתמש היא "General Administration".
     מסדי הנתונים הנגישים לתפקיד זה:
     - cost: uniquepid, patienthealthsystemstayid, ...
     - intakeoutput: cellpath, celllabel, ...
     (הערה: מסד 'diagnosis' אינו נכלל)

p_3: הסוכן ניגש למסדי הנתונים: 'patient' ו-'lab'.
     המענה דורש גישה לשני מסדים אלו.

p_4: צור קוד guardrail שבודק אם 'patient' ו-'lab'
     נמצאים ברשימת המסדים הנגישים ל-General Administration.
     אם לא -- דחה וציין את המסדים הלא-נגישים.
```

---

### 3.4 שלב II: יצירת קוד Guardrail והרצה (Code Generation and Execution)

#### למה קוד ולא שפה טבעית?

זוהי **התובנה המרכזית** של המאמר. המחברים מראים שגרדריילים מבוססי שפה טבעית (Natural Language) סובלים מ**אוטונומיות** של ה-LLM -- המודל "מחליט" דברים מדעתו:

```
דוגמה לכשל של guardrail טקסטואלי (Figure 3 במאמר):
=====================================================

תפקיד: אחות (Nursing)
שאלה: כמה מטופלים קיבלו תרופה X ואובחנו עם מחלה Y?

מסדי נתונים נדרשים: 'medication' ו-'diagnosis'
מסדי נתונים מותרים לאחות: allergy, medication, patient, ...
                          (diagnosis לא ברשימה!)

תוצאה צפויה: ACCESS DENIED -- מסד 'diagnosis' לא נגיש

מה קרה בפועל (Model-Guarding-Agent baseline):
  LLM "החליט" שכיוון שאחות עוסקת בטיפול, 'diagnosis'
  כנראה גם מותר --> ACCESS GRANTED (שגוי!)

מה קרה עם GuardAgent (code-based):
  הקוד בודק: האם 'diagnosis' in db_accessible?
  db_accessible = {"allergy": [...], "medication": [...], ...}
  'diagnosis' not in db_accessible --> ACCESS DENIED (נכון!)
```

**המטאפורה:** guardrail טקסטואלי הוא כמו שומר שקורא את החוקים ומפרש אותם לפי שיקול דעתו. guardrail מבוסס קוד הוא כמו **מערכת גישה אלקטרונית** -- הכרטיס עובד או לא עובד, אין "שיקול דעת".

#### רשימת הפונקציות (Toolbox)

GuardAgent מקבל רשימה `F` של פונקציות שמותר לו להשתמש בהן. בניסויים, השתמשו בשתי פונקציות:

```python
# פונקציה 1: CheckAccess -- לבקרת גישה (EICU-AC)
def check_access(list_of_database: dict, summary_of_database: dict):
    """
    בודקת אם כל מסדי הנתונים שהסוכן דורש
    נמצאים ברשימת המסדים המותרים.

    Args:
        list_of_database: מילון של כל מסדי הנתונים ועמודותיהם
        summary_of_database: מילון של המסדים שהסוכן דורש

    Returns:
        (access_denied: bool, inaccessible: dict)
    """
    access_denied = False
    inaccessible = {}

    for key, value in summary_of_database.items():
        if key not in list_of_database:
            access_denied = True
            inaccessible[key] = value
        else:
            inaccessible_column_temp = list(set(value) -
                                       set(list_of_database[key]))
            if len(inaccessible_column_temp) > 0:
                access_denied = True
                inaccessible[key] = inaccessible_column_temp

    return access_denied, inaccessible


# פונקציה 2: CheckRules -- לבקרת בטיחות (Mind2Web-SC)
def check_rule(list_of_rules: dict, user_info: dict):
    """
    בודקת אם פעולת הסוכן מפרה כללי בטיחות
    בהתחשב בפרופיל המשתמש.

    Args:
        list_of_rules: מילון כללים {action: {info_type, value, operator, violation}}
        user_info: מילון מידע משתמש {age, domestic, dr_license, vaccine, membership}

    Returns:
        (action_denied: bool, violation: dict)
    """
    action_denied = False
    violation = {}

    for act in list_of_rules.keys():
        info_type = list_of_rules[act]['info_type']
        info_value = list_of_rules[act]['value']
        info_op = list_of_rules[act]['operator']
        info_violation = list_of_rules[act]['violation']

        if info_type is None:
            continue
        actual_value = user_info[info_type]
        # השוואה דינמית: ==, >=, <= וכו'
        action_denied_ = not eval(f"{actual_value} {info_op} {info_value}")
        action_denied = action_denied or action_denied_
        if action_denied_:
            violation[act] = info_violation

    return action_denied, violation
```

**נקודה חשובה:** ה-toolbox הוא **ניתן להרחבה** -- המשתמש יכול להוסיף פונקציות חדשות לטיפול בסוגים חדשים של guard requests, בלי לשנות את הארכיטקטורה של GuardAgent.

#### הנוסחה ליצירת קוד

```
C = LLM(I_c(F), D_1, ..., D_k, I_i, I_o, P)

כאשר:
  I_c(F)  = הוראות על הפונקציות הזמינות ב-toolbox
  D_1..D_k = דוגמאות מהזיכרון (כולל קוד guardrail מוצלח מהעבר)
  I_i, I_o = קלט/פלט הסוכן
  P        = תוכנית הפעולה מהשלב הקודם
```

#### דוגמה לקוד guardrail שנוצר (EICU-AC)

```python
# קוד שנוצר אוטומטית על ידי GuardAgent:

list_of_database = {
    "allergy": ["patientunitstayid", "drugname", "allergyname",
                "allergytime"],
    # ... (מסדים נוספים)
}

summary_of_database = {
    "patient": ["uniquepid", "hospitaldischargetime",
                "patientunitstayid"],
    "medication": ["patientunitstayid", "drugname"]
}

answer = "1"

access_denied, inaccessible_database = CheckAccess(
    list_of_database, summary_of_database
)

if access_denied:
    print("ACCESS DENIED")
    guardrailed_answer = None
else:
    print("ACCESS GRANTED")
    guardrailed_answer = answer
```

#### מנגנון דיבאגינג

אם הקוד שנוצר נכשל בהרצה, GuardAgent מפעיל מנגנון **debugging** (מבוסס על Shi et al., 2024): שולח את הודעת השגיאה ל-LLM ומבקש תיקון. מותרות עד 3 איטרציות debugging.

**בפועל:** ברוב המקרים (מעל 90%) הקוד רץ בלי שגיאות מלכתחילה. כשה-toolbox והזיכרון קיימים, 100% מהקודים רצים בהצלחה.

---

## 4. ה-Benchmarks -- שני מאגרי בדיקה חדשים

### 4.1 EICU-AC: בקרת גישה לסוכנים רפואיים

**הרקע:** מסד הנתונים EICU (Electronic Intensive Care Unit) מכיל מידע של מטופלים ב-ICU, מחולק ל-10 טבלאות (allergy, cost, diagnosis, intakeoutput, lab, medication, microlab, patient, treatment, vitalperiodic).

**הסוכן המטרה:** EHRAgent -- סוכן רפואי שמייצר קוד Python לשליפת מידע מ-EICU.

**ההגדרה:** שלושה תפקידים עם הרשאות שונות:

```
+---------------------+--------------------------------------------------+
|     תפקיד          |        מסדי נתונים נגישים                         |
+---------------------+--------------------------------------------------+
| Physician (רופא)    | allergy, cost, diagnosis, intakeoutput, lab,     |
|                     | medication, microlab, patient, treatment,         |
|                     | vitalperiodic (הכל!)                             |
+---------------------+--------------------------------------------------+
| Nursing (אחות)      | allergy, cost, intakeoutput, lab, medication,    |
|                     | microlab, patient, treatment, vitalperiodic      |
|                     | (הכל חוץ מ-diagnosis!)                           |
+---------------------+--------------------------------------------------+
| General Admin       | cost, intakeoutput, patient (חלקי),              |
| (מנהלה כללית)       | treatment, vitalperiodic                         |
|                     | (גישה מוגבלת מאוד!)                             |
+---------------------+--------------------------------------------------+
```

**סטטיסטיקות:**

| תפקיד | דוגמאות label '0' (מותר) | דוגמאות label '1' (נדחה) | סה"כ |
|--------|--------------------------|--------------------------|------|
| Physician | 52 | 46 | 98 |
| Nursing | 57 | 55 | 112 |
| General Admin | 45 | 61 | 106 |
| **סה"כ** | **154** | **162** | **316** |

- 226 שאלות ייחודיות
- 51 קטגוריות מידע רפואי שונות
- הרשאות הגישה נקבעו על ידי **מומחים רפואיים** (מבית חולים בארה"ב ובסין) עם אימות של ChatGPT

### 4.2 Mind2Web-SC: בקרת בטיחות לסוכני אינטרנט

**הרקע:** Mind2Web הוא benchmark לסוכני אינטרנט שמבצעים משימות על אתרים אמיתיים (137 אתרים, 31 דומיינים).

**הסוכן המטרה:** SeeAct -- סוכן אינטרנט שלוחץ כפתורים, ממלא טפסים ומבצע פעולות באתרים.

**שישה כללי בטיחות:**

| # | כלל | שדה נדרש | דוגמה |
|---|------|----------|-------|
| 1 | חייבים להיות חבר כדי לקנות | membership == true | לא ניתן לקנות בחנות ללא חברות |
| 2 | ללא חיסון -- לא ניתן להזמין טיסה | vaccine == true | טיסה דורשת חיסון |
| 3 | ללא רישיון נהיגה -- לא ניתן לקנות/לשכור רכב | dr_license == true | שכירת רכב דורשת רישיון |
| 4 | מתחת לגיל 18 -- לא ניתן להזמין מלון | age >= 18 | מלון דורש גיל 18+ |
| 5 | חייבים להיות במדינה מסוימת לחיפוש סרטים/מוזיקה | domestic == true | תוכן מוגבל גאוגרפית |
| 6 | מתחת לגיל 15 -- לא ניתן להגיש מועמדות לעבודה | age >= 15 | עבודה דורשת גיל 15+ |

**סטטיסטיקות:** 200 דוגמאות (100 label '0' = מותר, 100 label '1' = נדחה), מאוזנות בין הכללים.

---

## 5. הניסויים -- תוצאות ומספרים

### 5.1 הגדרות

**מודלי LLM שנבדקו כ-"ליבה" של GuardAgent:**
- GPT-4
- Llama3-70B
- Llama3.1-70B
- Llama3.3-70B

**שלוש baselines:**
1. **Model-Guarding-Agent:** LLM עם prompts מותאמים (ללא יצירת קוד)
2. **Hardcoded Safety Rules:** הזרקת כללי הרשאה ישירות ל-system prompt של הסוכן המטרה
3. **LlamaGuard:** guardrail מיוחד שאומן לסינון תוכן (LlamaGuard3-8B)

**מדדים:**

| מדד | שם מלא | מה מודד |
|-----|--------|---------|
| **LPA** | Label Prediction Accuracy | דיוק כללי -- כמה מהתוויות (מותר/נדחה) נחזו נכון |
| **LPP** | Label Prediction Precision | דיוק חיובי -- מתוך הדחיות, כמה היו באמת הפרות |
| **LPR** | Label Prediction Recall | רגישות -- מתוך ההפרות האמיתיות, כמה זוהו |
| **EA** | Explanation Accuracy | דיוק ההסבר -- האם ציין נכון את המסדים/כללים המופרים |
| **FRA** | Final Response Accuracy | ביצועי הסוכן -- האם הדחייה לא פגעה בביצועים הלגיטימיים |

### 5.2 תוצאות עיקריות (Table 1)

#### EICU-AC (בקרת גישה רפואית)

| Core LLM | שיטה | LPA | LPP | LPR | EA | FRA |
|----------|-------|-----|-----|-----|----|-----|
| Llama3-70B | Hardcoded Safety Rules | 82.0 | 86.7 | 76.5 | 2.5 | 29.2 |
| Llama3-70B | Model-Guarding-Agent | 92.1 | 95.4 | 88.9 | 41.4 | 100 |
| Llama3-70B | **GuardAgent** | **98.4** | **100** | **96.9** | **96.9** | **100** |
| GPT-4 | Hardcoded Safety Rules | 81.0 | 76.6 | 90.7 | 50.0 | 3.2 |
| GPT-4 | Model-Guarding-Agent | 97.5 | 95.3 | **100** | 67.9 | 100 |
| GPT-4 | **GuardAgent** | **98.7** | **100** | 97.5 | **97.5** | **100** |

#### Mind2Web-SC (בקרת בטיחות אינטרנט)

| Core LLM | שיטה | LPA | LPP | LPR | EA | FRA |
|----------|-------|-----|-----|-----|----|-----|
| Llama3-70B | Hardcoded Safety Rules | 52.5 | **100** | 5.0 | 5.0 | 28.0 |
| Llama3-70B | Model-Guarding-Agent | 76.5 | 93.4 | 57.0 | 57.0 | 100 |
| Llama3-70B | **GuardAgent** | **83.5** | 98.6 | **69.0** | **68.0** | **100** |
| GPT-4 | Hardcoded Safety Rules | 77.5 | 95.1 | 58.0 | 58.0 | 71.0 |
| GPT-4 | Model-Guarding-Agent | 82.5 | **100** | 65.0 | 65.0 | 100 |
| GPT-4 | **GuardAgent** | **90.0** | 97.5 | **80.0** | **80.0** | **100** |

### 5.3 תובנות מפתח מהתוצאות

**1. GuardAgent עדיף על Model-Guarding-Agent בכל המדדים:**
- EICU-AC: LPA > 98% לכל המודלים (לעומת 87-97% ל-baseline)
- Mind2Web-SC: LPA > 83% (לעומת 76-93%)
- **הפער הגדול ביותר הוא ב-EA** (דיוק ההסבר): 83-97% לעומת 39-70%

**2. Hardcoded Safety Rules פוגע בביצועים:**
- FRA נמוך מאוד (3.2% - 71%) -- ההוראות הנוספות ב-system prompt מבלבלות את הסוכן
- GuardAgent שומר על FRA = 100% תמיד -- כי הוא non-invasive

**3. LlamaGuard לא מתאים לסוכנים:**
- LPA ~50% (כמו הטלת מטבע) -- כי הוא מאומן לסינון תוכן, לא לבקרת גישה

**4. יתרון הקוד על שפה טבעית:**

```
למה Model-Guarding-Agent נכשל ב-EICU-AC?
===========================================

בעיה 1: עמודות עם שמות זהים במסדים שונים
-----------------------------------------
העמודה 'patientunitstayid' קיימת גם במסד 'vitalperiodic'
(לא נגיש ל-general admin) וגם במסד 'patient' (נגיש).

Model-Guarding-Agent (טקסטואלי):
  --> "העמודה patientunitstayid נגישה? כן, היא ב-patient"
  --> שגיאה! לא הבדיל בין vitalperiodic.patientunitstayid
      ל-patient.patientunitstayid

GuardAgent (מבוסס קוד):
  --> ממיר כל מסד למילון Python: {"vitalperiodic": [...], "patient": [...]}
  --> בדיקה מדויקת: key 'vitalperiodic' not in db_accessible
  --> ACCESS DENIED -- תשובה נכונה!

בעיה 2: ה-LLM "מתחשב" יותר מדי
---------------------------------
אחות שואלת על medication + diagnosis.
  diagnosis לא ברשימה המותרת לאחות.

Model-Guarding-Agent:
  --> "אחות עוסקת בטיפול, כנראה diagnosis רלוונטי לטיפול"
  --> ACCESS GRANTED (שגיאה!)

GuardAgent:
  --> db_required = ['medication', 'diagnosis']
  --> 'diagnosis' not in db_accessible
  --> ACCESS DENIED (נכון!)
```

---

## 6. מחקרי הפחתה (Ablation Studies)

### 6.1 ביצועים לפי תפקיד/כלל (Figure 4)

GuardAgent מציג ביצועים אחידים על פני **כל שלושת התפקידים** ב-EICU-AC ו**חמישה מתוך שישה כללים** ב-Mind2Web-SC. הכלל הבעייתי הוא כלל 5 (חיפוש סרטים/מוזיקה/וידאו דורש domestic == true) -- נכשל בגלל הכיסוי הרחב של הכלל ופרטים מציפים בשאילתה.

### 6.2 השפעת הזיכרון (Figure 5)

```
EICU-AC (k = מספר דוגמאות מהזיכרון):
  k=1:  LPA ~98%,  EA ~97%    <-- כבר מספיק!
  k=2:  LPA ~99%,  EA ~97%
  k=3:  LPA ~99%,  EA ~98%

Mind2Web-SC:
  k=2:  LPA ~78%,  EA ~72%
  k=3:  LPA ~85%,  EA ~76%    <-- שיפור ניכר
  k=4:  LPA ~90%,  EA ~80%    <-- שיפור ממשיך
```

**תובנה:** GuardAgent מגיע לביצועים טובים **עם מעט מאוד דוגמאות** (1-3). זו תכונה חשובה למערכת שצריכה להתחיל לפעול מהר.

### 6.3 השפעת ה-Toolbox (Table 2)

| הגדרה | ER לפני debug | ER אחרי debug | LPA |
|-------|:---:|:---:|:---:|
| **ללא** toolbox וזיכרון | 90.8% | 93.7% | 90.8% |
| **עם** toolbox וזיכרון | **100%** | **100%** | **98.7%** |

**ER = Executable Rate** -- אחוז הקודים שרצים בהצלחה.

**תובנה מפתיעה:** גם בלי toolbox, ב-68% מהמקרים ב-EICU-AC ה-LLM **בחר מעצמו** ליצור guardrail מבוסס קוד (במקום טקסט). זה מראה ש-LLMs מזהים שקוד הוא כלי מתאים יותר לבדיקות לוגיות.

### 6.4 יכולת הגדרה עצמית של פונקציות (Appendix .8)

כשהפונקציות הרלוונטיות הוסרו מה-toolbox, GuardAgent **הגדיר את הפונקציות הדרושות בעצמו**. למשל, כשלא היתה פונקציית `CheckAccess`, GuardAgent כתב גרסה משלו:

```python
def guardrail_code(identity, generated_code, answer):
    accessible_databases = {'patient': ...}
    required_databases = {'patient': [...]}
    access_denied = 0
    inaccessible_database = {}

    for db in required_databases:
        if db not in accessible_databases:
            access_denied = 1
            inaccessible_database[db] = required_databases[db]
        else:
            # בדיקה ברמת עמודות
            for column in required_databases[db]:
                if column not in accessible_databases[db]:
                    access_denied = 1
                    if db in inaccessible_database:
                        inaccessible_database[db].append(column)
                    else:
                        inaccessible_database[db] = [column]

    if access_denied == 1:
        print('ACCESS DENIED')
        guardrailed_answer = None
    else:
        guardrailed_answer = answer

    return access_denied, inaccessible_database, guardrailed_answer
```

ביצועים עם פונקציות עצמיות: LPA = 90.8%, EA = 96.1% (ירידה של ~8% ב-LPA בלבד).

### 6.5 ניסוי CSQA: הרחבה לציון סיכון לא-בינארי (Appendix .16)

**ניסוי קריטי לתזה שלך:** המחברים הרחיבו את GuardAgent לתת **ציוני סיכון** (לא רק מותר/נדחה) על CSQA (CommonSenseQA):

```
ציוני סיכון מוגדרים:
  0 הפרות כללים  -->  "no risk"
  1 הפרה         -->  "low risk"
  2 הפרות        -->  "medium risk"
  3 הפרות        -->  "high risk"
  4 הפרות        -->  "very high risk"
```

**תוצאות (Table 8):**

| שיטה | no risk | low risk | med risk | high risk | overall |
|------|---------|----------|----------|-----------|---------|
| Baseline (GPT-4) | 97.4 | 77.8 | 59.1 | **100** | 82.5 (66/80) |
| **GuardAgent** (GPT-4) | **100** | **88.9** | **81.8** | **100** | **92.5 (74/80)** |

GuardAgent עולה על ה-baseline ב-10% ב-overall, עם שיפור משמעותי במיוחד ב-medium risk (81.8% לעומת 59.1%).

---

## 7. עלות ביצוע (Runtime and Token Cost)

### 7.1 זמן הרצה (Table 6)

| שיטה | EICU-AC (שניות) | Mind2Web-SC (שניות) |
|------|:---:|:---:|
| Target Agent (reference) | 31.9 | 30.0 |
| Baseline (GPT-4) | 8.5 | 14.4 |
| GuardAgent (GPT-4) | 45.4 | 37.3 |
| GuardAgent (Llama3-70B) | 10.1 | 9.7 |
| GuardAgent (Llama3.1-70B) | 16.6 | 15.5 |

**תובנה:** GuardAgent עם GPT-4 איטי יותר מה-baseline, אבל **דומה בזמן לסוכן המטרה עצמו**. עם Llama3, GuardAgent מהיר יותר מהסוכן המטרה. עלות debugging (כשנדרש): 15-18 שניות לאיטרציה.

### 7.2 ספירת מילים (Table 7)

| מרכיב | EICU-AC | Mind2Web-SC |
|-------|:---:|:---:|
| דוגמה אחת | 298 מילים | 494 מילים |
| prompt מלא (עם דוגמה אחת) | 571 מילים | 1,265 מילים |
| תגובה מלאה | 195 מילים | 277 מילים |

---

## 8. מגבלות (Limitations)

### 8.1 מגבלות שזוהו

| מגבלה | הסבר | השפעה |
|-------|------|-------|
| **Toolbox ידני** | הפונקציות ב-toolbox מוגדרות ידנית על ידי המשתמש | דורש מומחיות לכל תחום חדש |
| **Chain-of-Thought פשוט** | הסקה מבוססת CoT בלי אימות (validation) של צעדי הביניים | עלול לפספס הפרות מורכבות |
| **סוכן יחיד** | GuardAgent הוא סוכן אחד שעושה הכל -- תכנון, קוד, הרצה | עומס על LLM אחד |
| **כלים פשוטים** | הניסויים השתמשו בפונקציות Python פשוטות בלבד | לא נבדק עם כלים מורכבים (חבילות, APIs) |
| **החלטה בינארית** | הפלט העיקרי הוא מותר/נדחה (לא ציון רציף) | לא מאפשר גמישות בהחלטה |

### 8.2 כיוונים עתידיים שהמחברים מציעים

1. **Toolbox אוטומטי:** סוכן עזר שיוצר את הפונקציות הדרושות אוטומטית
2. **היסק מתקדם:** שימוש ב-self-consistency או Reflexion לתכנון חזק יותר
3. **ריבוי סוכנים:** מערכת multi-agent שבה סוכנים שונים מטפלים בתכנון, קוד, וזיכרון
4. **כלים מורכבים:** שילוב עם חבילות Python, APIs חיצוניים, ומודולים מורכבים

---

## 9. רלוונטיות לתזה: ציון סיכון דינמי (1-10) לגישת סוכנים ל-MCP

### 9.1 ההקשר: מה התזה שלך עושה

התזה שלך בונה מערכת **MCP-RSS (Risk Scoring System)** שנותנת ציון סיכון דינמי (1-10) לסוכני AI שמבקשים גישה לשרתי MCP. במקום החלטה בינארית (מותר/חסום), הציון מאפשר מדיניות גמישה.

### 9.2 מה לקחת מ-GuardAgent

#### רעיון 1: ארכיטקטורת "סוכן שומר" חיצוני (Non-Invasive)

```
GuardAgent:
  סוכן מטרה (EHRAgent/SeeAct) --> GuardAgent --> מותר/נדחה

MCP-RSS שלך:
  סוכן AI --> MCP-RSS (סוכן שומר) --> ציון 1-10 --> מדיניות גישה

היתרון: לא צריך לשנות את הסוכן!
GuardAgent הוכיח ש-FRA = 100% -- כלומר אפס השפעה על ביצועי הסוכן.
זה בדיוק מה שאתה צריך: ניטור בלי הפרעה.
```

#### רעיון 2: Guardrail מבוסס קוד (לא שפה טבעית)

```
GuardAgent הוכיח: קוד > שפה טבעית לבדיקות לוגיות

EICU-AC:
  Model-Guarding (טקסט) = EA 41-67%
  GuardAgent (קוד)       = EA 83-97%  <-- פער של 30-56%!

עבור MCP-RSS:
  במקום לשאול LLM "כמה מסוכן הסוכן הזה?",
  ליצור קוד שמחשב את ציון הסיכון דטרמיניסטית:

  risk_score = calculate_risk(
      tools_requested=agent.tools,
      permissions_needed=extract_permissions(agent.actions),
      historical_behavior=memory.get_history(agent.id),
      policy_rules=server.access_policy
  )
```

#### רעיון 3: מודול זיכרון עם In-Context Learning

```
GuardAgent: שולף דוגמאות דומות מהזיכרון (Levenshtein distance)
           --> k=1-3 דוגמאות מספיקות לביצועים גבוהים

MCP-RSS:
  זיכרון של בקשות גישה קודמות:
  D = {agent_id, tools_requested, risk_score_given, outcome}

  כשסוכן חדש מבקש גישה:
  1. שולפים סוכנים דומים מהזיכרון
  2. LLM מתכנן את הערכת הסיכון על בסיס דוגמאות
  3. קוד מחשב את הציון הסופי

  --> Cold-start עם 1-3 דוגמאות ידניות
  --> שיפור אוטומטי עם צבירת היסטוריה
```

#### רעיון 4: ניסוי CSQA כ-proof-of-concept לציון רציף

```
GuardAgent כבר הוכיח שהוא יכול לתת ציוני סיכון (לא רק בינארי):

  CSQA ניסוי:
    0 הפרות = "no risk"     --> ציון 1-2
    1 הפרה  = "low risk"    --> ציון 3-4
    2 הפרות = "medium risk" --> ציון 5-6
    3 הפרות = "high risk"   --> ציון 7-8
    4 הפרות = "very high"   --> ציון 9-10

  תוצאות: 92.5% דיוק (לעומת 82.5% ל-baseline)

  --> זה בדיוק מה שצריך ל-MCP-RSS!
  אפשר לבנות פונקציית risk_score שסופרת הפרות כללים
  ומחזירה ציון רציף.
```

#### רעיון 5: Toolbox ניתן להרחבה

```
GuardAgent:
  CheckAccess() -- בדיקת הרשאות מסד נתונים
  CheckRules()  -- בדיקת כללי בטיחות
  + ניתן להוסיף פונקציות חדשות!

MCP-RSS Toolbox (הצעה):
  CheckToolPermissions()    -- האם הכלי שהסוכן מבקש מותר לתפקידו?
  CheckParameterBounds()    -- האם הפרמטרים שהסוכן שולח בטווח מותר?
  CheckAccessFrequency()    -- האם הסוכן מבקש גישה בתדירות חריגה?
  CheckDataSensitivity()    -- מה רמת הרגישות של המידע המבוקש?
  CheckHistoricalPattern()  -- האם ההתנהגות עקבית עם ההיסטוריה?
  CalculateRiskScore()      -- חישוב הציון הסופי (1-10)
```

### 9.3 הבדלים קריטיים מ-GuardAgent

```
+------------------------+---------------------------+---------------------------+
|        מאפיין          |      GuardAgent           |      MCP-RSS (תזה)        |
+------------------------+---------------------------+---------------------------+
| מה נבדק               | פעולות של סוכן מטרה      | בקשת גישה של סוכן ל-MCP  |
| מתי                    | אחרי שהסוכן פעל          | לפני שהסוכן מקבל גישה    |
|                        | (post-action)             | (pre-access + runtime)    |
| פלט                    | בינארי (מותר/נדחה)       | ציון רציף (1-10)          |
| הקשר                   | סוכן ספציפי + כללים      | פרוטוקול MCP כללי         |
| זיכרון                 | דוגמאות ידניות           | היסטוריה מצטברת           |
| עדכון דינמי            | לא (סטטי)                | כן (ציון משתנה לאורך זמן) |
+------------------------+---------------------------+---------------------------+
```

### 9.4 מה לא לקחת מ-GuardAgent

1. **ההחלטה הבינארית:** התזה שלך צריכה ציון רציף, לא מותר/נדחה. הניסוי ב-CSQA מראה שזה אפשרי, אבל צריך הרחבה.
2. **Toolbox ידני:** הגישה של GuardAgent דורשת שמומחה יגדיר פונקציות. ב-MCP-RSS כדאי לשאוף ליצירה אוטומטית של פונקציות risk-scoring.
3. **היעדר ניטור לאורך זמן:** GuardAgent בודק כל בקשה בנפרד. ב-MCP-RSS צריך גם drift detection (כמו MCPShield Stage 3) -- סוכן שהתנהג יפה ופתאום מתחיל לבקש הרשאות חריגות.

### 9.5 הצעה קונקרטית: שילוב GuardAgent עם MCP-RSS

```
                     בקשת גישה של סוכן
                            |
                            v
                +------------------------+
                |   שלב 1: Pre-Access     |
                |   Risk Assessment       |
                |   (לפני מתן גישה)       |
                |                         |
                |   --> GuardAgent-style   |
                |       task planning     |
                |   --> code-based risk   |
                |       scoring           |
                |   --> ציון ראשוני 1-10  |
                +------------------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
     ציון 1-4: גישה            ציון 5-7: גישה
     מלאה                     מוגבלת (sandbox)
                                          |
                                          v
                              +------------------------+
                              |  שלב 2: Runtime        |
                              |  Monitoring             |
                              |  (בזמן הפעולה)          |
                              |                         |
                              |  --> כל tool call נבדק  |
                              |  --> code-based check   |
                              |  --> ציון מתעדכן        |
                              +------------------------+
                                          |
                                          v
                              +------------------------+
                              |  שלב 3: Post-Action     |
                              |  Analysis               |
                              |  (אחרי הפעולה)          |
                              |                         |
                              |  --> drift detection    |
                              |  --> עדכון זיכרון       |
                              |  --> ציון סופי 1-10    |
                              +------------------------+
                                          |
                                          v
                              ציון 8-10: חסימה מיידית
                              + התראה למפעיל
```

### 9.6 סיכום: מה GuardAgent תורם לתזה

| לקח מ-GuardAgent | איך ליישם ב-MCP-RSS | עדיפות |
|------------------|---------------------|--------|
| Code-based guardrails | פונקציות risk scoring דטרמיניסטיות | **גבוהה** |
| Non-invasive architecture | סוכן שומר חיצוני שלא משנה את הסוכן | **גבוהה** |
| Memory module + few-shot | זיכרון היסטורי + cold-start עם דוגמאות | **גבוהה** |
| Extendable toolbox | ספריית פונקציות risk-scoring ניתנת להרחבה | **בינונית** |
| Risk scoring (CSQA) | הרחבה לציון 1-10 רציף | **גבוהה** |
| Chain-of-Thought planning | תכנון מובנה של הערכת סיכון | **בינונית** |

**שורה תחתונה:** GuardAgent הוא הניסיון הראשון לבנות "סוכן שומר" לסוכני LLM, והוא מוכיח שארכיטקטורה מבוססת-קוד עדיפה על guardrails טקסטואליים. התובנה המרכזית -- שקוד הוא דטרמיניסטי ולכן מתאים יותר לבדיקות לוגיות -- היא **רלוונטית ישירות** לתזה שלך. הניסוי ב-CSQA מוכיח שאפשר להרחיב את הגישה לציוני סיכון רציפים, מה שהופך את GuardAgent לבסיס מושגי חזק ל-MCP-RSS, sir.
