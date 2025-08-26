from __future__ import annotations
import streamlit as st
from supabase import create_client, Client

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        url = st.secrets.get("SUPABASE_URL", None)
        key = st.secrets.get("SUPABASE_ANON_KEY", None)
        if not url or not key:
            class Dummy:
                class Auth:
                    def sign_in_with_password(self, *a, **k): raise Exception("Brak SUPABASE_URL/KEY w secrets.")
                    def sign_out(self): pass
                    def get_user(self): return type("U",(),{"user": None})
                auth = Auth()
                def table(self, *a, **k): return self
                def upsert(self, *a, **k): return self
                def insert(self, *a, **k): return self
                def delete(self, *a, **k): return self
                def eq(self, *a, **k): return self
                def execute(self): return None
            return Dummy()
        _client = create_client(url, key)
    return _client

def get_user():
    try:
        return get_client().auth.get_user().user
    except Exception:
        return None
