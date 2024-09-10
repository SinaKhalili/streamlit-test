import csv
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import streamlit as st


def process_csv(file):
    rows = []
    file.seek(0)
    spamreader = csv.reader(StringIO(file.getvalue().decode("utf-8")), delimiter=",")
    for row in spamreader:
        rows.append(row)

    names = set(row[14] for row in rows if len(row) > 14 and row[14] != "")
    symbol_table = {name: {} for name in names if name != "" and name is not None}
    weekday_identifiers = ["M", "Tu", "W", "Th", "F", "Sa", "Su"]
    all_weeks = {}
    attendance_days = defaultdict(set)

    for row in rows:
        if len(row) > 14 and row[14] in symbol_table:
            name = row[14]
            date = row[9]  # Assuming the date is in column 9 (index 9)
            time = row[10]  # Assuming the time is in column 10 (index 10)
            try:
                date_obj = datetime.strptime(date, "%m/%d/%Y")
                time_obj = datetime.strptime(time.strip(), "%I:%M:%S%p")
                formatted_time = time_obj.strftime("%I:%M %p")

                start_of_week = date_obj - timedelta(days=date_obj.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                week_range = f"{start_of_week.strftime('%m/%d')} - {end_of_week.strftime('%m/%d')}"

                all_weeks[week_range] = (start_of_week, end_of_week)

                if week_range not in symbol_table[name]:
                    symbol_table[name][week_range] = ["🟥"] * 7
                symbol_table[name][week_range][
                    date_obj.weekday()
                ] = f"🟩({formatted_time})"
                attendance_days[week_range].add(date_obj.weekday())
            except Exception as e:
                pass

    sorted_weeks = sorted(all_weeks.keys(), key=lambda x: all_weeks[x][0])
    for week_range in sorted_weeks:
        for day in range(5):  # Only for weekdays (Mon-Fri)
            if day not in attendance_days[week_range]:
                for name in symbol_table:
                    if week_range in symbol_table[name]:
                        symbol_table[name][week_range][day] = "🟪"

    output = StringIO()
    csv_writer = csv.writer(output)

    headers = ["Name"] + sorted_weeks
    csv_writer.writerow(headers)

    for name in names:
        row = [name]
        for week_range in sorted_weeks:
            week_data = symbol_table[name].get(week_range, ["🟥"] * 7)
            formatted_week_data = [
                f"{weekday_identifiers[i]}: {status}"
                for i, status in enumerate(week_data[:5])
            ]
            row.append("\n".join(formatted_week_data))
        csv_writer.writerow(row)

    output.seek(0)
    return output


st.title("b8y Official Unofficial")
st.title("🎉 NARC Sheet Generator 🎉")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    processed_file = process_csv(uploaded_file)
    st.write("## 🔽 Download 🔽 ")
    st.download_button(
        label="Download Processed CSV",
        data=processed_file.getvalue(),
        file_name=f"PROCESSED - f{uploaded_file.name}.csv",
        mime="text/csv",
    )
    st.write(
        """
    To put it into a new sheet in Google Sheets, follow these steps:

    `File` -> `Import` -> `Upload` 

    ## Meaning
    - 🟩 for days when someone attended (with the time they attended)
    - 🟥 for days when a particular person didn't attend, but others did
    - 🟪 for days when nobody attended at all - this usually means this day doesn't exist i.e. the boundary of the month
    """
    )
    st.image("Narc.jpg")
    st.write("## Preview")
    st.table(pd.read_csv(processed_file))
    st.success("CSV file processed successfully.")
