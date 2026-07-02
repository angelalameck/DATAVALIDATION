import pandas as pd

def detect_issued_amount_anomalies(df):
    mean_value = df["issued_amt"].mean()
    std_value = df["issued_amt"].std()
    threshold = mean_value + (3 * std_value)
    anomalies = df[
        df["issued_amt"] > threshold
    ].copy()
    anomalies["error_type"] = (
        "Suspicious High Issued Amount"
    )
    return anomalies


def detect_returned_amount_anomalies(df):
    mean_value = df["returned_amt"].mean()
    std_value = df["returned_amt"].std()
    threshold = mean_value + (3 * std_value)
    anomalies = df[
        df["returned_amt"] > threshold
    ].copy()
    anomalies["error_type"] = (
        "Suspicious High Returned Amount"
    )
    return anomalies


def run_anomaly_detection(df):
    anomalies = pd.concat([
        detect_issued_amount_anomalies(df),
        detect_returned_amount_anomalies(df)
    ])
    return anomalies