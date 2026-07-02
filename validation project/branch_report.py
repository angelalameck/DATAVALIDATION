import os
import pandas as pd
from validation import run_all_validations
from anomaly_detection import run_anomaly_detection
from summary_report import generate_summary_report
from error_log import build_error_log

REPORTS_DIR = "reports"

def build_branch_report(input_file, branch_code):
    df = pd.read_csv(input_file, dtype={"branch_code": str})
    total_records = len(df)

    validation_errors = run_all_validations(df)
    anomaly_flags = run_anomaly_detection(df)
    all_flags = pd.concat([validation_errors, anomaly_flags], ignore_index=True)

    report = generate_summary_report(all_flags)
    log = build_error_log(df)

    return df, all_flags, report, log, total_records


def save_branch_outputs(branch_code, report, log):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"{branch_code}_summary_report.csv")
    log_path = os.path.join(REPORTS_DIR, f"{branch_code}_error_log.csv")
    report.to_csv(report_path, index=False)
    log.to_csv(log_path, index=False)
    return report_path, log_path


if __name__ == "__main__":

    branches = [
        ("DSM_raw.csv", "DSM"),
        ("MWZ_raw.csv", "MWZ"),
        ("DDM_raw.csv", "DDM"),
    ]

    for raw_file, branch_code in branches:
        try:
            df, all_flags, report, log, total = build_branch_report(raw_file, branch_code)
            report_path, log_path = save_branch_outputs(branch_code, report, log)

            print(f"\n{'='*50}")
            print(f"{branch_code}: {total} records checked, {len(all_flags)} flagged entries.")
            print(f"\nSummary report -> {report_path}")
            print(report.to_string(index=False))
            print(f"\nDetailed error log -> {log_path}")
            print(f"({len(log)} rows — one per flagged issue)")
            print(log.head(5).to_string(index=False))

        except FileNotFoundError:
            print(f"Skipped {branch_code} — {raw_file} not found.")

    print("\nAll branches validated.")
