from __future__ import annotations
import streamlit as st
from typing import Optional, BinaryIO

def upload_box(label: str) -> Optional[BinaryIO]:
    return st.file_uploader(label, type=["xlsx"], accept_multiple_files=False)
