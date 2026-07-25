import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embedding, train_clf
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject
import time
from src.components.subject_card import subject_card
from src.components.dialog_enroll import enroll_dialog
from src.pipelines.voice_pipeline import get_voice_embedding


def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
        
    with c2:
        st.subheader(f"Welcome Back, {student_data['name']}")
        if st.button("Logout", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.student_data
            st.rerun()
    st.space()
    st.space()

    col1, col2 = st.columns(2)

    with col1:
        st.header("Your Enrolled Subjects")

    with col2:
        if st.button("Enroll in Subject", type="primary", width="stretch"):
            enroll_dialog()

    st.divider()

    with st.spinner("Loding Your Enrolled Subjects..."):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended":0}

        stats_map[sid]['total'] += 1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1

    cols = st.columns(2)

    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']

        stats = stats_map.get(sid, {"total":0, "attended":0})
        def unenroll_btn():
            if st.button('Unenroll from this course', type="tertiary", width="stretch", icon= ":material/delete_forever:"):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f'Unenroll from {sub["name"]} succesfully!')
                st.rerun()
        with cols[i % 2]:
            subject_card(
                name = sub['name'],
                code = sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📅', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended'])
                ],
                footer_callback = unenroll_btn()
            )

    footer_dashboard()
def student_screen():

    style_background_dashboard()
    style_base_layout()

    if 'student_data' in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
        
    with c2:
        if st.button("Go back to Home", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()
    
    st.header("Login using FaceID", text_alignment="center")
    
    st.space()
    st.space()

    show_registration = False


    enable = st.checkbox("Enable camera")
    photo_source = st.camera_input("Position your face in the Center", disabled=not enable)

    st.markdown("""
            <style>
            video {
                transform: scaleX(-1);
            }
            </style>
            """, unsafe_allow_html=True)
    if photo_source:
        img = np.array(Image.open(photo_source))

        with st.spinner("AI is Scanning..."):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning("No Faces Found")
            elif num_faces > 1:
                st.warning("Multiple Faces Found")
            else:
                if detected:
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()
                    student = next((s for s in all_students if s['student_id']==student_id), None)

                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = "student"
                        st.session_state.student_data = student
                        st.toast("Welcome Back!!!")
                        time.sleep(1)
                        st.rerun()

                else:
                    st.info("Face Not Recognized!, You Might be a new student")
                    show_registration= True
    if show_registration:
        with st.container(border=True):
            st.header("Register your profile")
            new_name = st.text_input("Enter your name:", placeholder="Samarth Dalu")

            st.subheader("Optional: Voice Enrollment")
            st.info("Enroll for Voice Only Attendance:")

            audio_data = None

            try:
                audio_data = st.audio_input("Record a short phase like; I'm Present, My name is xyz")
            except Exception:
                st.error("Audio Data Failed!")

            if st.button("Create Account", type="primary"):
                if new_name:
                    with st.spinner("Creating Profile..."):
                        img = np.array(Image.open(photo_source))
                        encodings = get_face_embedding(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            voice_emb = None

                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(new_name, face_embedding= face_emb, voice_embedding = voice_emb)

                            if response_data:
                                train_clf()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = "student"
                                st.session_state.student_data = response_data[0]
                                st.toast("Profile Created!!!")
                                time.sleep(1)
                                st.rerun()

                        else:
                            st.error("Could'nt capture your face features for registration")


                else:
                    st.warning("Please enter name!")
    footer_dashboard()