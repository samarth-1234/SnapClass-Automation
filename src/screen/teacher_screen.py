import streamlit as st
import numpy as np
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects
from src.components.dialog_add_photos import add_photos_dialog
from src.pipelines.face_pipeline import predict_attendance
from src.database.config import supabase
from datetime import datetime
import pandas as pd
from src.components.dialog_attendance_result import attendance_results_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog

def teacher_screen():
    style_background_dashboard()
    style_base_layout()
    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()

def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
        
    with c2:
        st.subheader(f"Welcome Back, {teacher_data['name']}")
        if st.button("Logout", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data
            st.rerun()
    st.space()
    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"
    tab1, tab2, tab3 = st.columns(3)

    with tab1:
            type1 = "primary" if st.session_state.current_teacher_tab == "take_attendance" else "tertiary"
            if st.button("Take Attendance", width="stretch", icon=":material/ar_on_you:", type= type1):
                st.session_state.current_teacher_tab = "take_attendance"
                st.rerun()
    with tab2:
            type2 = "primary" if st.session_state.current_teacher_tab == "manage_subjects" else "tertiary"
            if st.button("Manage Subjects", width="stretch", icon=":material/book_ribbon:", type=type2):
                st.session_state.current_teacher_tab = "manage_subjects"
                st.rerun()
    with tab3:
            type3 = "primary" if st.session_state.current_teacher_tab == "attendance_record" else "tertiary"
            if st.button("Attendance Record", width="stretch", icon=":material/cards_stack:", type=type3):
                st.session_state.current_teacher_tab = "attendance_record"
                st.rerun()

    st.divider()


    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()


    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()


    if st.session_state.current_teacher_tab == "attendance_record":
        teacher_tab_attendance_record()



    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header("Take Attendance Tab")

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning("You Havent Created any Subjects Yet!, Please Create One to Begin!")
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3,1])

    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))

    with col2:
        if st.button('Add Photos ', type="primary", icon=':material/photo_library:', width="stretch"):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()


    if st.session_state.attendance_images:
        st.header('Added Photos')
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, width='stretch', caption=f'Photo {idx + 1}')

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("Clear all Photos", width= 'stretch', type='tertiary', icon=':material/delete:'):
                st.session_state.attendance_images = []
                st.rerun()

        with c2:
            has_photos = bool(st.session_state.attendance_images)
            if st.button("Run face analytics", width= 'stretch', type='secondary', icon=':material/analytics:'):
                with st.spinner('Deep Scanning Classroom Photos...'):
                    all_detected_ids = {}

                    for idx, img in enumerate(st.session_state.attendance_images):
                        img_np = np.array(img.convert('RGB'))

                        detected, _, _ = predict_attendance(img_np)


                        if detected:
                            for sid in detected.keys():
                                student_id = int(sid)

                                all_detected_ids.setdefault(student_id, []).append(f"Photo: {idx+1}")

                    enrolled_res = supabase.table('subject_students').select('*, students(*)').eq('subject_id', selected_subject_id).execute()

                    enrolled_students = enrolled_res.data

                    if not enrolled_students:
                        st.warning('No Students Enrolled in this Course!')
                    else:
                        results, attendance_to_log = [], []

                        current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                        for node in enrolled_students:
                            student = node['students']
                            sources = all_detected_ids.get(int(student['student_id']), [])
                            is_present = len(sources) > 0

                            results.append({
                                "Name": student['name'],
                                "ID": student['student_id'],
                                "Source": ', '.join(sources) if is_present else '-',
                                "Status": "Present" if is_present else "Absent"
                            })

                            attendance_to_log.append({
                                'student_id': student['student_id'],
                                'subject_id': selected_subject_id,
                                "timestamp": current_timestamp,
                                'is_present': bool(is_present)
                            })
                    attendance_results_dialog(pd.DataFrame(results), attendance_to_log)

        with c3:
            if st.button("Use Voice Attendance", type='primary', width='stretch', icon=':material/mic:'):
                voice_attendance_dialog()
def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data["teacher_id"]
    col1, col2 = st.columns(2)
    with col1:
        st.header("Manage Subjects", width="stretch")
    with col2:
        if st.button("Create New Subject", width="stretch"):
            create_subject_dialog(teacher_id)

    # List all subjects
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("👤", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes'])
            ]
            def share_btn():
                if st.button(f"Share Code: {sub['name']}", key=f"share_{sub['subject_code']}", icon=":material/share:"):
                    share_subject_dialog(sub['name'], sub['subject_code'])
                st.space()

            subject_card(
                name = sub['name'],
                code = sub['subject_code'],
                section = sub['section'],
                stats = stats,
                footer_callback = share_btn
            )
    else:
        st.info("NO SUBJECTS FOUND, CREATE ONE!!!")


def teacher_tab_attendance_record():
    st.header("Attendance Record")
def login_teacher(username, password):
    if not username or not password:
        return False
    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True
    return False

def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
    
    with c2:
        if st.button("Go back to Home", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header("Login using Password", text_alignment="center")

    st.space()
    st.space()

    teacher_username = st.text_input("Enter Username", placeholder="username@1")
    teacher_pass = st.text_input("Enter Password", type="password", placeholder="pass@123")
    

    st.divider()

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button("Login", shortcut="control+enter",  icon=':material/passkey:', width="stretch"):
            if login_teacher(teacher_username, teacher_pass):
                st.toast("Welcome Back!")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid Username and Password Combo")
    with btnc2:
        if st.button("Register Insted", icon=':material/passkey:', width="stretch", type="primary"):
            st.session_state.teacher_login_type = "register"

    footer_dashboard()



def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All fields are required!"
    
    if check_teacher_exists(teacher_username):
        return False, "Username Already Exists!"

    if teacher_pass != teacher_pass_confirm:
        return False, "Password dosn't matches!"

    try:
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Sucessfully Created!, You can Login now"
    except Exception as e:
        return False, f"Unexpected Error: {e}"

    
def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
    
    with c2:
        if st.button("Go back to Home", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header("Register Your Teacher Profile")
    st.space()
    st.space()
    
    teacher_username = st.text_input("Enter Username", placeholder="username@1")
    teacher_name = st.text_input("Enter Full-Name", placeholder="Enter Full-Name")
    teacher_pass = st.text_input("Enter Password", type="password", placeholder="pass@123")
    teacher_pass_confirm = st.text_input("Enter Confirm Password", type="password", placeholder="Confirm Password")
    
    st.divider()
    
    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button("Register Now", shortcut="control+enter",  icon=':material/passkey:', width="stretch"):
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)
    with btnc2:
        if st.button("Login Insted", icon=':material/passkey:', width="stretch", type="primary"):
            st.session_state.teacher_login_type = "login"
    footer_dashboard()