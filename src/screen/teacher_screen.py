import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.database.db import check_teacher_exists, create_teacher, teacher_login

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
    st.header("bhwdcd")


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