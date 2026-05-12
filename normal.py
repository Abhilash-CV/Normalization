import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="KEAM Normalization", layout="wide")

st.title("KEAM 2026 Normalization Calculator")

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

def interpolate_score(target_percentile, batch_df):
    """
    Find interpolated score for target percentile
    from another session/batch.
    """

    df = batch_df.sort_values("Percentile").reset_index(drop=True)

    # Exact match
    exact = df[np.isclose(df["Percentile"], target_percentile)]

    if not exact.empty:
        return float(exact.iloc[0]["Score"])

    # Lower percentile row
    lower = df[df["Percentile"] < target_percentile]

    # Higher percentile row
    higher = df[df["Percentile"] > target_percentile]

    # If no lower found -> minimum score
    if lower.empty:
        return float(df.iloc[0]["Score"])

    # If no higher found -> maximum score
    if higher.empty:
        return float(df.iloc[-1]["Score"])

    lower_row = lower.iloc[-1]
    higher_row = higher.iloc[0]

    p1 = lower_row["Percentile"]
    p2 = higher_row["Percentile"]

    s1 = lower_row["Score"]
    s2 = higher_row["Score"]

    # Linear interpolation
    interpolated = s1 + (
        (target_percentile - p1) / (p2 - p1)
    ) * (s2 - s1)

    return float(interpolated)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = ["RollNo", "Batch", "Percentile", "Score"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            st.stop()

    # Get all batches
    batches = sorted(df["Batch"].unique())

    output_rows = []

    for idx, row in df.iterrows():

        roll = row["RollNo"]
        current_batch = row["Batch"]
        percentile = row["Percentile"]
        original_score = row["Score"]

        result = {
            "RollNo": roll,
            "Batch": current_batch,
            "Percentile": percentile,
            "Score": original_score
        }

        all_scores = [original_score]

        score_col_no = 2

        for batch in batches:

            if batch == current_batch:
                continue

            batch_df = df[df["Batch"] == batch]

            interp_score = interpolate_score(
                percentile,
                batch_df
            )

            result[f"Score{score_col_no}"] = interp_score

            all_scores.append(interp_score)

            score_col_no += 1

        # Average = Normalized score
        norm_score = np.mean(all_scores)

        result["Norm_Score"] = round(norm_score, 4)

        output_rows.append(result)

    out_df = pd.DataFrame(output_rows)

    # Reorder columns
    cols = list(out_df.columns)

    fixed_cols = ["RollNo", "Batch", "Percentile", "Score"]

    score_cols = sorted(
        [c for c in cols if c.startswith("Score") and c != "Score"],
        key=lambda x: int(x.replace("Score", ""))
    )

    final_cols = fixed_cols + score_cols + ["Norm_Score"]

    out_df = out_df[final_cols]

    st.success("Normalization Completed")

    st.dataframe(out_df, use_container_width=True)

    # Download
    output_file = "keam_normalized_output.xlsx"

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False)

    with open(output_file, "rb") as f:
        st.download_button(
            label="Download Output Excel",
            data=f,
            file_name=output_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
