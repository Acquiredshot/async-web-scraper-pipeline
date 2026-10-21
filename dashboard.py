import json
import sqlite3
from contextlib import closing

import pandas as pd
import streamlit as st

from config import settings


st.set_page_config(
    page_title="Playwright Pipeline Dashboard", page_icon="🕷️", layout="wide"
)
st.title("🕷️ Automated Web Scraper & Pipeline Dashboard")
st.caption("Telemetry and inspection interface for captured asynchronous pipeline items.")


@st.cache_data(ttl=5)
def load_data(database_uri: str) -> pd.DataFrame:
    with closing(sqlite3.connect(database_uri, uri=True)) as connection:
        return pd.read_sql_query(
            "SELECT id, title, author, tag, captured_at "
            "FROM scraped_items ORDER BY id DESC",
            connection,
        )


if not settings.database_path.is_file():
    st.warning("Database not found yet. Run the scraper pipeline using `py -3.13 main.py`.")
    st.stop()

st.sidebar.header("Pipeline Metrics")
if st.sidebar.button("Refresh data"):
    load_data.clear()

try:
    frame = load_data(settings.database_path.resolve().as_uri() + "?mode=ro")
except (sqlite3.Error, pd.errors.DatabaseError) as error:
    st.error(f"Could not read the scraper database: {error}")
    st.stop()

st.sidebar.metric("Total Records Extracted", len(frame))
st.sidebar.metric("Unique authors", frame["author"].nunique())

if frame.empty:
    st.info("No results yet. Run `python main.py` to collect data.")
    st.stop()

search_term = st.text_input("Search Scraped Content", "")
if search_term:
    frame = frame[
        frame["title"].str.contains(search_term, case=False, na=False, regex=False)
        | frame["author"].str.contains(search_term, case=False, na=False, regex=False)
    ]

total_col, authors_col = st.columns(2)
total_col.metric("Matching records", len(frame))
authors_col.metric("Matching authors", frame["author"].nunique())

if frame.empty:
    st.info("No records match your search.")
else:
    st.subheader("Records by author")
    author_counts = frame.groupby("author").size().reset_index(name="records")
    st.bar_chart(author_counts, x="author", y="records")

st.subheader("Extracted Data Registry")
st.dataframe(frame, use_container_width=True, hide_index=True)

csv_bytes = frame.to_csv(index=False).encode("utf-8-sig")
json_bytes = json.dumps(
    frame.to_dict(orient="records"),
    ensure_ascii=False,
    indent=2,
    default=str,
).encode("utf-8")
csv_download, json_download = st.columns(2)
csv_download.download_button(
    "Download CSV",
    csv_bytes,
    file_name="scraped_items.csv",
    mime="text/csv",
)
json_download.download_button(
    "Download JSON",
    json_bytes,
    file_name="scraped_items.json",
    mime="application/json",
)
