import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
from PIL import Image
import time


@st.dialog("Voice Attendance")
def voice_attendance_dialog():
    st.button()