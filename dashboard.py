from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from database import DB_PATH, init_db, seed_db
from crud import get_all_polls_admin, get_poll_results, get_poll_summary


def rows_to_dataframe(rows: list) -> pd.DataFrame:
    """Convert SQLite rows to pandas DataFrame."""
    return pd.DataFrame([dict(row) for row in rows])


def main() -> None:
    """Run Streamlit dashboard for poll results."""
    init_db(DB_PATH)
    seed_db(DB_PATH)

    st.set_page_config(page_title="Дашборд опросов", layout="wide")
    st.title("Дашборд результатов голосований и опросов")

    polls = get_all_polls_admin(DB_PATH)
    polls_df = rows_to_dataframe(polls)

    st.subheader("Список опросов")
    st.dataframe(polls_df)

    if polls_df.empty:
        st.info("Опросов пока нет.")
        return

    poll_id = st.selectbox(
        "Выберите ID опроса",
        polls_df["id"].tolist(),
    )

    summary = get_poll_summary(int(poll_id), DB_PATH)
    if summary is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Вопросов", int(summary["question_count"]))
        col2.metric("Участников", int(summary["participant_count"]))
        col3.metric("Голосов", int(summary["vote_count"]))

    results = get_poll_results(int(poll_id), DB_PATH)
    results_df = rows_to_dataframe(results)

    st.subheader("Результаты")
    st.dataframe(results_df)

    if not results_df.empty:
        for question in results_df["question"].unique():
            st.write(f"### {question}")
            part = results_df[results_df["question"] == question]
            st.bar_chart(part, x="option_text", y="vote_count")


if __name__ == "__main__":
    main()
