import pandas as pd
import json
import os

# Ensure these match your exact CSV filenames
files = {
    "Class6": "result_portal_Class_6.csv",
    "Class7": "result_portal_Class_7.csv",
    "Class8A": "result_portal_Class_8(A).csv",
    "Class8B": "result_portal_Class_8(B).csv",
    "Class9A": "result_portal_Class_9(A).csv",
    "Class9B": "result_portal_Class_9(B).csv"
}

school_data = {}

FIXED_COLS = {"Roll", "Name", "DOB", "Total", "%", "Result"}

for class_name, filename in files.items():
    school_data[class_name] = {}
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found in the folder.")
        continue

    df = pd.read_csv(filename)
    df = df.fillna("AB")

    all_cols = list(df.columns)

    # Find the index of the "Total" column
    if "Total" not in all_cols:
        print(f"Warning: No 'Total' column in {filename}, skipping.")
        continue
    total_idx = all_cols.index("Total")

    # Data columns are everything between the fixed headers and "Total"
    data_cols = [c for c in all_cols[:total_idx] if c not in FIXED_COLS]

    # Detect format: multi-exam if any data column contains " - "
    is_multi_exam = any(" - " in col for col in data_cols)

    # Compute rank for ALL students (Withheld = pct<15 get '-', handled by JS)
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
    df["_pct_num"] = pd.to_numeric(df["%"], errors="coerce").fillna(0)
    withheld_mask = df["_pct_num"] < 15
    rankable_mask = ~withheld_mask
    df["Rank"] = "-"   # default: withheld or no data
    if rankable_mask.any():
        df.loc[rankable_mask, "Rank"] = (
            df.loc[rankable_mask, "Total"]
            .rank(method="min", ascending=False)
            .astype(int)
            .astype(str)
        )

    def get_dob(row):
        dob = str(row["DOB"]) if "DOB" in df.columns else ""
        if not dob or dob.strip().upper() in ("", "AB", "NAN"):
            return "01/01/2026"
        return dob

    if is_multi_exam:
        # Parse exam and subject names from column headers: "{exam} - {subject}"
        exams_seen = []
        subjects_seen = []
        for col in data_cols:
            if " - " in col:
                exam, sub = col.split(" - ", 1)
                if exam not in exams_seen:
                    exams_seen.append(exam)
                if sub not in subjects_seen:
                    subjects_seen.append(sub)

        for _, row in df.iterrows():
            roll_no = str(row["Roll"]).strip()
            per_exam = {}
            for exam in exams_seen:
                per_exam[exam] = {}
                for sub in subjects_seen:
                    col = f"{exam} - {sub}"
                    if col in df.columns:
                        per_exam[exam][sub] = str(row[col])

            school_data[class_name][roll_no] = {
                "name": str(row["Name"]),
                "dob": get_dob(row),
                "exams": exams_seen,
                "subjects": subjects_seen,
                "per_exam": per_exam,
                "total": str(int(row["Total"])),
                "percentage": str(row["%"]),
                "rank": str(row["Rank"]),
                "status": str(row["Result"]),
            }

    else:
        # Flat / legacy format — data columns are subject names
        subjects_seen = data_cols

        for _, row in df.iterrows():
            roll_no = str(row["Roll"]).strip()
            marks = {sub: str(row[sub]) for sub in subjects_seen if sub in df.columns}

            school_data[class_name][roll_no] = {
                "name": str(row["Name"]),
                "dob": get_dob(row),
                "exams": [],
                "subjects": subjects_seen,
                "per_exam": {"": marks},
                "total": str(int(row["Total"])),
                "percentage": str(row["%"]),
                "rank": str(row["Rank"]),
                "status": str(row["Result"]),
            }

# Output the data as a JavaScript variable
with open("data.js", "w") as js_file:
    js_file.write("const schoolData = " + json.dumps(school_data, indent=4) + ";")

print("Success! data.js has been generated.")
