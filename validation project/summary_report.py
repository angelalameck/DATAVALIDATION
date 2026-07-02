import pandas as pd
def generate_summary_report(all_flags):
    summary = (
        all_flags
        .groupby(
            [
                "branch_code",
                "error_type"
            ]
        )
        .size()
        .reset_index(
            name="flagged_count"
        )
    )
    return summary