from flask import Flask, render_template, request, redirect, url_for, session, flash
from pathlib import Path
import json
import pandas as pd
from matching_engine import evaluate
from ai_engine import similarity_scores

app = Flask(__name__)
app.secret_key = "masar-local-demo-change-this"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CSV = DATA / "masar_scholarships_demo.csv"
PROFILE = DATA / "profile.json"

def scholarships():
    df = pd.read_csv(CSV, encoding="utf-8-sig")
    for col in ("eligible_degrees", "eligible_majors", "required_documents"):
        if col in df:
            df[col] = df[col].fillna("[]").apply(lambda x: json.loads(x) if str(x).startswith("[") else [])
    return df.fillna("").to_dict("records")

def get_profile():
    if "profile" in session:
        return session["profile"]
    if PROFILE.exists():
        try: return json.loads(PROFILE.read_text(encoding="utf-8"))
        except Exception: return {}
    return {}

@app.context_processor
def inject():
    return {"profile": get_profile()}

@app.route("/")
def home():
    rows = scholarships()
    return render_template("home.html", count=len(rows), countries=len(set(r["country"] for r in rows)))

@app.route("/scholarships")
def explore():
    rows = scholarships()
    q = request.args.get("q","").strip().lower()
    country = request.args.get("country","")
    funding = request.args.get("funding","")
    rows = [r for r in rows if (not q or q in str(r["scholarship_name"]).lower() or q in str(r["university"]).lower() or q in str(r["country"]).lower()) and (not country or r["country"]==country) and (not funding or r["funding_type"]==funding)]
    all_rows = scholarships()
    return render_template("scholarships.html", rows=rows, countries=sorted(set(r["country"] for r in all_rows)), q=q, country=country, funding=funding)

@app.route("/profile", methods=["GET","POST"])
def profile_page():
    if request.method == "POST":
        p = {
            "full_name": request.form.get("full_name","").strip(),
            "major": request.form.get("major","").strip(),
            "degree_level": request.form.get("degree_level","Bachelor"),
            "preferred_study_level": request.form.get("preferred_study_level","Master"),
            "gpa": float(request.form.get("gpa") or 0),
            "gpa_scale": request.form.get("gpa_scale","4.0"),
            "target_country": request.form.get("target_country","Any"),
            "english_level": request.form.get("english_level","Intermediate"),
            "english_test": request.form.get("english_test",""),
            "english_score": float(request.form.get("english_score") or 0) or None
        }
        if not p["full_name"] or not p["major"]:
            flash("يرجى إدخال الاسم والتخصص على الأقل.")
        else:
            session["profile"] = p
            DATA.mkdir(exist_ok=True)
            PROFILE.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
            flash("تم حفظ ملفك الأكاديمي على هذا الجهاز.")
            return redirect(url_for("matches"))
    return render_template("profile.html", p=get_profile())

@app.route("/matches")
def matches():
    p = get_profile()
    if not p:
        flash("أنشئ ملفك الأكاديمي أولًا حتى نحلل توافقك.")
        return redirect(url_for("profile_page"))
    rows = scholarships()
    output=[]
    for s in rows:
        rule=evaluate(p,s)
        output.append({**s, "result":rule})
    output.sort(key=lambda x: (x["result"]["status"]!="Eligible", -x["result"]["rule_score"]))
    return render_template("matches.html", rows=output)

@app.route("/scholarship/<scholarship_id>")
def detail(scholarship_id):
    item=next((x for x in scholarships() if x["scholarship_id"]==scholarship_id),None)
    if not item: return "المنحة غير موجودة",404
    p=get_profile()
    result=evaluate(p,item) if p else None
    return render_template("detail.html", s=item, result=result)

@app.route("/plan")
def plan():
    return render_template("plan.html")

if __name__ == "__main__":
    app.run(debug=True)
