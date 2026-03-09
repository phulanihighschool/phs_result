import pandas as pd
import json
import os

# Ensure these match your exact CSV filenames
files = {
    "Class6": "Class 6.csv",
    "Class7": "Class 7.csv",
    "Class8A": "Class 8(A).csv",
    "Class8B": "Class 8(B).csv",
    "Class9A": "Class 9(A).csv",
    "Class9B": "Class 9(B).csv"
}

school_data = {}

for class_name, filename in files.items():
    school_data[class_name] = {}
    if os.path.exists(filename):
        # Read the CSV file
        df = pd.read_csv(filename)

        # Replace empty cells with "AB" (Absent)
        df = df.fillna("AB")

        # Ensure Total is numeric for ranking
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)

        # Calculate Rank ONLY for passing students
        pass_mask = df['Result'].str.upper() == 'PASS'
        df['Rank'] = "-"
        df.loc[pass_mask, 'Rank'] = df.loc[pass_mask, 'Total'].rank(method='min', ascending=False).astype(int).astype(str)

        for _, row in df.iterrows():
            roll_no = str(row['Roll']).strip()

            # Map columns exactly
            school_data[class_name][roll_no] = {
                "name": str(row['Name']),
                "assamese": str(row['Assamese']),
                "english": str(row['English']),
                "science": str(row['General Science']),
                "maths": str(row['General Mathematics']),
                "social": str(row['Social Science']),
                "hindi": str(row['Hindi']),
                "total": str(row['Total']),
                "percentage": str(row['%']),
                "rank": str(row['Rank']),
                "status": str(row['Result'])
            }
    else:
        print(f"Warning: {filename} not found in the folder.")

# Output the data as a JavaScript variable
with open("data.js", "w") as js_file:
    js_file.write("const schoolData = " + json.dumps(school_data, indent=4) + ";")

print("Success! data.js has been generated with Rank calculated automatically.")
