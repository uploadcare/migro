import csv
from pathlib import Path
from datetime import datetime


def save_result_to_csv(files, attempt_id, source):
    path = Path(__file__).resolve().parent.parent / "logs"
    path.mkdir(exist_ok=True)
    current_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename = path / f"Attempt {attempt_id} - {current_time} - {source}.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Path', 'File Size', 'Uploadcare UUID', 'Status', 'Error'])
        writer.writerows(files)

    return filename
