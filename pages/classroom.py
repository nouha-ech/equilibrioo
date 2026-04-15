#!/usr/bin/env python3
"""
Google Classroom API Course List Streamlit App
Displays your Google Classroom courses in a Streamlit interface.
"""

import os
import pickle
import sys
from pathlib import Path

import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


CLIENT_SECRET_FILE = str(Path(__file__).parent / "client_secret.json")
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/classroom.courses.readonly"]
OAUTH_PORT = 8082
API_NAME = "classroom"
API_VERSION = "v1"



def authenticate_google_classroom():
    """Handle OAuth authentication and return authorized credentials."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            st.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            st.info("Starting new OAuth flow...")
            if not os.path.exists(CLIENT_SECRET_FILE):
                st.error(f"❌ {CLIENT_SECRET_FILE} not found! Please download it from Google Cloud Console.")
                st.stop()

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(
                open_browser=True,
                port=OAUTH_PORT,
                bind_addr="127.0.0.1"
            )

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
            st.success(f"✅ Token saved to {TOKEN_FILE}")

    return creds


def fetch_classroom_courses(service):
    """Fetch and return list of courses from Google Classroom API."""
    try:
        results = service.courses().list().execute()
        return results.get("courses", [])
    except Exception as e:
        st.error(f"❌ Error fetching courses: {e}")
        return []


def main():
    st.title("📚 Google Classroom Courses")
    st.write("This app fetches and displays your Google Classroom courses.")

    st.info("🔐 Authenticating with Google Classroom API...")
    creds = authenticate_google_classroom()

    st.info("🔌 Building Classroom API service...")
    service = build(API_NAME, API_VERSION, credentials=creds)

    st.info("📚 Fetching your courses...")
    courses = fetch_classroom_courses(service)

    if not courses:
        st.warning("✅ No courses found (or you don't have access to any).")
    else:
        st.success(f"✅ Found {len(courses)} course(s):")
        course_data = [{"Course Name": c.get("name", "Unnamed Course")} for c in courses]
        st.table(course_data)


if __name__ == "__main__":
    main()
