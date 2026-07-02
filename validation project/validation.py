import pandas as pd
VALID_DENOMINATIONS = [
    "TZS 500",
    "TZS 1000",
    "TZS 2000",
    "TZS 5000",
    "TZS 10000"
]

def check_missing_dates(df):
    missing = df[
        df["report_date"].isnull()
    ].copy()
    missing["error_type"] = "Missing Date"
    return missing


def check_negative_amounts(df):
    negative = df[
        (df["issued_amt"] < 0) |
        (df["returned_amt"] < 0)
    ].copy()
    negative["error_type"] = "Negative Amount"
    return negative


def check_invalid_denominations(df):
    invalid = df[
        ~df["denomination"].isin(
            VALID_DENOMINATIONS
        )
    ].copy()
    invalid["error_type"] = "Invalid Denomination"
    return invalid


def check_duplicate_reports(df):
    duplicates = df[
        df["report_id"].duplicated(
            keep=False
        )
    ].copy()
    duplicates["error_type"] = "Duplicate Report ID"
    return duplicates


def run_all_validations(df):
    errors = pd.concat([
        check_missing_dates(df),
        check_negative_amounts(df),
        check_invalid_denominations(df),
        check_duplicate_reports(df)
    ])
    return errors


def build_flagged_dataset(df):
    errors = run_all_validations(df)
    if errors.empty:
        flagged = df.copy()
        flagged["data_quality_flag"] = "OK"
        return flagged
    flags_per_id = (
        errors.groupby("report_id")["error_type"]
        .apply(lambda types: "; ".join(sorted(set(types))))
    )
    flagged = df.copy()
    flagged["data_quality_flag"] = flagged["report_id"].map(flags_per_id).fillna("OK")
    return flagged