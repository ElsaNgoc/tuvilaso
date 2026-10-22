# 🔮 Tử Vi Lá Số: AI Birth Chart Reader

A web app that turns a **Tử Vi (Vietnamese Purple Star astrology) birth chart** into a personalised, easy to read report, written by an AI that is only allowed to reason from a classic reference book.

> **Language note:** the app's interface and its reports are intentionally in **Vietnamese**, because they are written for Vietnamese users. The code comments and this README are in English.

## ✨ Overview

Traditional Tử Vi readings are long, full of jargon, and often give the same advice to a child and a retiree. This project explores how **AI assisted product design** can make them personal and practical:

* Users **paste a birth chart** (lá số) and the app converts it into structured data
* A short **context survey**, tailored to the user's age group, captures their real situation (study, work, family, health)
* An LLM writes a **four chapter report**, grounded only in passages from the reference book *Tử Vi Đẩu Số Tân Biên* and in the user's context
* A **daily page** shows today's Trực (one of the 12 day officers in the Vietnamese almanac) with advice adjusted to the user's age

The app was designed and built through **AI assisted development (vibe coding)** with Cursor, with a strong focus on content design and making a complex domain approachable.

## 🧭 UX & Content Design Highlights

* **Age aware advice**: advice is rewritten for four life stages (children, young people, adults, over 60), so a child is never advised about money or investments
* **Context before content**: the survey runs before the analysis, and the answers are woven into all four chapters
* **Grounded, not invented**: the AI only receives the book passages relevant to each chapter, which keeps the readings consistent and avoids overloading the model
* **Readable structure**: a table of contents with sub sections (overview, each palace, each month) lets users jump straight to what they care about
* **Guest friendly privacy**: guests can paste a chart, read the report, download it and ask questions; everything is deleted when they close the page. Only signed in users have their charts and conversations saved
* **Family profiles**: one account can store several named charts, for example everyone in a family

## 📖 Report Structure

Each report is written chapter by chapter, with each chapter receiving only its own context:

| Chapter | Content | Context given to the AI |
| --- | --- | --- |
| 1. Overview of destiny | Four short sections on the person's overall chart, with advice matched to their age group | Four Pillars knowledge and the book's Yin Yang / Five Elements rules |
| 2. The 12 palaces | Each palace in three paragraphs: everyday life, visible influences (tam hợp) and hidden influences (nhị hợp) | Knowledge of the 14 main stars from the book |
| 3. This year's fortune | Key events of the year, then a month by month outlook with age appropriate topics | Annual stars and the 12 months calculated per the book |
| 4. Action guide | A table of the 12 Trực: favourable or not, what to do and what to avoid, adjusted for age | Day selection (trạch cát) knowledge |

Reports can be downloaded as **Word documents**, and users can ask follow up questions about their chart in a chat box.

## 🧩 Features

* Paste a birth chart and convert it to structured JSON
* Age based context survey
* Four chapter AI report, grounded in the reference book
* Follow up Q&A about the chart, remembered per chart for signed in users
* Daily "what to do today" page and a lunar calendar of the 12 Trực
* Word export of the full report
* Google sign in, multiple named charts per account
* Works with **OpenAI** or **Google Gemini**

## 🛠️ Tech Stack

`Python` `http.server` `Pydantic` `OpenAI API` `Google Gemini` `pdfplumber` `Word export` `SQLite` `Turso` `Google Sign In` `HTML` `JavaScript` `Lunar JavaScript`

## 🚀 Getting Started

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then add your OpenAI or Gemini key
python db.py                # create the database tables
python web.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

### Environment variables

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Use OpenAI for the analysis |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Or use Google Gemini instead |
| `GOOGLE_CLIENT_ID` | Google OAuth client for sign in |
| `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | Optional; store data in Turso. Leave empty to use the local `du_lieu/tuvilaso.db` file |

### The reference book

The book *Tử Vi Đẩu Số Tân Biên* by Vân Đằng Thái Thứ Lang is **not included** in this repository for copyright reasons. To generate full reports:

1. Place your own PDF copy of the book in `tai_lieu/`.
2. Run `python pdf_parser.py` to extract it into `tai_lieu/TuVi_TanBien_Data.md`.

The small knowledge files in `tai_lieu/*.json` (Four Pillars, main stars, auxiliary stars, day selection) are included.

### Sample chart

`sample_laso.json` is an **illustrative sample** with fictional birth details, used by `python models.py` to check the chart format.

## 📁 Project Structure

```text
web.py            # Web server and all pages / API routes
nhap_laso.py      # Converts a pasted chart into JSON
models.py         # Chart data model (Pydantic)
engine.py         # Labels the chart before calling the AI
hoan_canh.py      # Context survey for each age group
han.py            # Yearly and monthly fortune calculations
ngay.py           # Daily Trực and advice for each age group
analyze.py        # Builds prompts and calls the LLM chapter by chapter
xuat_word.py      # Exports the report to Word
pdf_parser.py     # Extracts the reference book from PDF
db.py             # Database tables (SQLite or Turso)
tai_khoan.py      # Accounts, Google sign in and sessions
kho_laso.py       # Stores charts, reports and Q&A
trang_chinh.html  # Main page
trang_ngay.html   # Daily page
thu_vien/         # Lunar JavaScript calendar library (third party)
tai_lieu/         # Knowledge files (the book itself is not included)
du_lieu/          # Database design notes and survey questions (Vietnamese)
```

## ⚠️ Disclaimer

This project is built for learning and cultural interest. Astrology readings are for entertainment and reflection only and should not replace professional advice.

## 👩‍💻 Author

**Elsa Ngoc Dang**: product design, UX/content design and AI assisted development

[LinkedIn](https://www.linkedin.com/in/ha-bao-ngoc-dang/) · [GitHub](https://github.com/ElsaNgoc)
