import streamlit as st
from src.database.db import create_subject

@st.dialog("Create New Subject")
def create_subject_dialog(teacher_id):
    st.write("Enter the details of new subjects")
    sub_id = st.text_input("Enter Course Code", placeholder="AI5PCC001")
    sub_name = st.text_input("Enter the name of the Subject", placeholder="Introduction to ML")
    sub_section = st.text_input("Enter the Section", placeholder="Section")


    if st.button("Create Subject Now", type="primary", width="stretch"):
        if sub_id and sub_name and sub_section:
            try:
                create_subject(sub_id, sub_name, sub_section, teacher_id)
                st.toast("Subject Created Succesfully...")
            except Exception as e:
                st.error(f"Error: {str(e)}")

        else:
            st.warning("Please fill all the fields!!!")