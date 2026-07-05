import os
import pandas as pd

# === CONFIG ===
folder_path = "historical_data"
output_folder = "cleaned_data"  # optional: separate folder
os.makedirs(output_folder, exist_ok=True)

# === FILE LOOP ===
for filename in os.listdir(folder_path):
    if not filename.endswith(".csv"):
        continue

    filepath = os.path.join(folder_path, filename)

    try:
        df = pd.read_csv(filepath)

        # If all columns are unnamed (e.g. 0, 1, 2...), treat as already cleaned
        if all(col.startswith("Unnamed") for col in df.columns):
            print(f"[SKIP] {filename} is already clean.")
            continue

        # Check if necessary columns exist
        expected_cols = {'Date', 'Open', 'High', 'Low', 'Close', 'Volume'}
        if not expected_cols.issubset(df.columns):
            print(f"[WARNING] {filename} is missing expected columns — skipping.")
            continue

        # Drop rows where price data is missing
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

        # Keep only the needed columns
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Sort and deduplicate
        df = df.sort_values('Date').drop_duplicates(subset='Date')
        df.set_index('Date', inplace=True)

        # Save cleaned version
        output_path = os.path.join(output_folder, filename)
        df.to_csv(output_path)

        print(f"[CLEANED] {filename} → saved to {output_folder}")

    except Exception as e:
        print(f"[ERROR] Failed to process {filename}: {e}")
