import pandas as pd
from validation import run_all_validations
from anomaly_detection import run_anomaly_detection

def build_error_log(df):
    validation_errors = run_all_validations(df)
    anomaly_flags = run_anomaly_detection(df)
    all_flags = pd.concat([validation_errors, anomaly_flags], ignore_index=True)

    if all_flags.empty:
        return pd.DataFrame(columns=[
            "row_number", "report_id", "branch_code", "report_date",
            "denomination", "issued_amt", "returned_amt",
            "error_type", "problem_field", "bad_value"
        ])
    df_numbered = df.copy().reset_index(drop=True)
    df_numbered["row_number"] = df_numbered.index + 1
    field_map = {
        "Missing Date":                   "report_date",
        "Negative Amount":                "issued_amt / returned_amt",
        "Invalid Denomination":           "denomination",
        "Duplicate Report ID":            "report_id",
        "Suspicious High Issued Amount":  "issued_amt",
        "Suspicious High Returned Amount":"returned_amt",
    }
    log_rows = []
    for _, flag_row in all_flags.iterrows():
        rid = flag_row["report_id"]
        etype = flag_row["error_type"]
        matches = df_numbered[df_numbered["report_id"] == rid]

        for _, orig_row in matches.iterrows():
            problem_field = field_map.get(etype, "unknown")

            if etype == "Missing Date":
                bad_value = str(orig_row["report_date"]) if pd.notna(orig_row["report_date"]) else "(blank)"
            elif etype == "Negative Amount":
                issued = orig_row["issued_amt"]
                returned = orig_row["returned_amt"]
                parts = []
                try:
                    if float(str(issued).replace(",", "")) < 0:
                        parts.append(f"issued_amt={issued}")
                except:
                    pass
                try:
                    if float(str(returned).replace(",", "")) < 0:
                        parts.append(f"returned_amt={returned}")
                except:
                    pass
                bad_value = ", ".join(parts) if parts else f"issued={issued} / returned={returned}"
            elif etype == "Invalid Denomination":
                bad_value = str(orig_row["denomination"])
            elif etype == "Duplicate Report ID":
                bad_value = str(orig_row["report_id"])
            elif etype == "Suspicious High Issued Amount":
                bad_value = str(orig_row["issued_amt"])
            elif etype == "Suspicious High Returned Amount":
                bad_value = str(orig_row["returned_amt"])
            else:
                bad_value = "—"

            log_rows.append({
                "row_number":   orig_row["row_number"],
                "report_id":    orig_row["report_id"],
                "branch_code":  orig_row["branch_code"],
                "report_date":  orig_row["report_date"],
                "denomination": orig_row["denomination"],
                "issued_amt":   orig_row["issued_amt"],
                "returned_amt": orig_row["returned_amt"],
                "error_type":   etype,
                "problem_field":problem_field,
                "bad_value":    bad_value,
            })

    log_df = pd.DataFrame(log_rows)
    log_df = log_df.sort_values("row_number").reset_index(drop=True)
    return log_df