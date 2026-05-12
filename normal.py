import streamlit as st
import pandas as pd
import numpy as np

st.title("KEAM Normalization")

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    df = df.sort_values(["Batch", "Percentile"])

    batches = sorted(df["Batch"].unique())

    # PREPROCESS ONCE
    batch_lookup = {}

    for batch in batches:

        temp = df[df["Batch"] == batch]

        batch_lookup[batch] = {
            "percentiles": temp["Percentile"].to_numpy(),
            "scores": temp["Score"].to_numpy()
        }

    def interpolate_score(percentile, p_arr, s_arr):

        idx = np.searchsorted(p_arr, percentile)

        # Below minimum
        if idx == 0:
            return float(s_arr[0])

        # Above maximum
        if idx >= len(p_arr):
            return float(s_arr[-1])

        p1 = p_arr[idx - 1]
        p2 = p_arr[idx]

        s1 = s_arr[idx - 1]
        s2 = s_arr[idx]

        # Exact match
        if p1 == percentile:
            return float(s1)

        if p2 == percentile:
            return float(s2)

        # Interpolation
        return float(
            s1 + ((percentile - p1) / (p2 - p1)) * (s2 - s1)
        )

    output = []

    total_batches = len(batches)

    progress = st.progress(0)

    rows = list(df.itertuples(index=False))

    total_rows = len(rows)

    for i, row in enumerate(rows):

        percentile = row.Percentile
        current_batch = row.Batch

        scores = []

        row_data = {
            "RollNo": row.RollNo,
            "Batch": current_batch,
            "Percentile": percentile,
            "Score": row.Score
        }

        scores.append(row.Score)

        score_index = 2

        for batch in batches:

            if batch == current_batch:
                continue

            interp_score = interpolate_score(
                percentile,
                batch_lookup[batch]["percentiles"],
                batch_lookup[batch]["scores"]
            )

            row_data[f"Score{score_index}"] = interp_score

            scores.append(interp_score)

            score_index += 1

        row_data["Norm_Score"] = round(np.mean(scores), 4)

        output.append(row_data)

        if i % 1000 == 0:
            progress.progress(i / total_rows)

    out_df = pd.DataFrame(output)

    st.success("Completed")

    st.dataframe(out_df)

    out_df.to_excel("normalized_output.xlsx", index=False)

    with open("normalized_output.xlsx", "rb") as f:
        st.download_button(
            "Download Output",
            f,
            file_name="normalized_output.xlsx"
        )
