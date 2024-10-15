import os
from datetime import datetime
from dotenv import load_dotenv
from faker import Faker
from google.cloud import storage

from PIL import Image
from streamlit.errors import StreamlitAPIException
import base64
import requests
import streamlit as st

API_URL = 'https://face-recognition-image-963201605868.us-central1.run.app'
# API_URL = 'http://127.0.0.1:8000'

st.set_page_config(page_title="Face Verification")
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'stored_token' not in st.session_state:
    st.session_state['stored_token'] = None

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'stored_token' not in st.session_state:
    st.session_state['stored_token'] = None

if 'enroll_username' not in st.session_state:
    st.session_state['enroll_username'] = ''
if 'enroll_password' not in st.session_state:
    st.session_state['enroll_password'] = ''
if 'enroll_email' not in st.session_state:
    st.session_state['enroll_email'] = ''
if 'enroll_fullname' not in st.session_state:
    st.session_state['enroll_fullname'] = ''

if 'update_username' not in st.session_state:
    st.session_state['update_username'] = ''
if 'update_name' not in st.session_state:
    st.session_state['update_name'] = ''
if 'update_password' not in st.session_state:
    st.session_state['update_password'] = ''
if 'update_email' not in st.session_state:
    st.session_state['update_email'] = ''

if 'delete_username' not in st.session_state:
    st.session_state['delete_username'] = ''

load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')


def upload_to_gcp(source_file_name, destination_folder):
    bucket_name = 'face-verification-images'
    destination_blob_name = f'{destination_folder}/{source_file_name}'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


def add_bg_from_local(image_file):
    with open(image_file, "rb") as file:
        encoded_image = base64.b64encode(file.read()).decode()
    st.markdown(
        f"""
         <style>
         .stApp {{
             background-image: url("data:image/png;base64,{encoded_image}");
             background-size: cover;
             background-position: center;
         }}
         </style>
         """,
        unsafe_allow_html=True
    )


add_bg_from_local("assets/face_ver.png")  # Replace with your image path

st.markdown("<h1 style='text-align: center; color: white;'>FACE RECOGNITION SYSTEM</h1>", unsafe_allow_html=True)


def capture_image(param):
    name = Faker().name()
    save_path = f'{name}.jpg'
    img_file = st.camera_input(param)

    if img_file is not None:
        img = Image.open(img_file)
        img.save(save_path, format="JPEG")
        st.success(f"Image captured successfully.")
        return save_path

    return None


def generate_token(username, password):
    if username is None or password is None:
        return st.error("Failed to generate token. Please check your credentials.")
    response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
    try:
        if response.status_code == 200:
            st.session_state['stored_token'] = response.json().get('access_token')
            st.success("Token sent to your email. Enter the token below to authenticate.")
        else:
            st.error("Failed to generate token. Please check your credentials.")
    except AttributeError:
        st.error("Failed to generate token. Please check your credentials.")


def enroll_user(username, password, email, fullname, filename):
    try:
        with open(filename, "rb") as image_file:
            files = {
                "image": (filename, image_file, "image/jpg")
            }
            data = {
                "username": username,
                "password": password,
                "email": email,
                "name": fullname,
                'is_admin': 0
            }
            bearer_token = st.session_state.get('stored_token', '')
            headers = {
                'Authorization': f"Bearer {bearer_token}"
            }
            response = requests.post(f"{API_URL}/enroll", headers=headers, data=data, files=files)
            try:
                upload_to_gcp(filename, 'enrollment-images')
            except Exception as e:
                pass
            if response.status_code == 200:
                try:
                    st.session_state.enroll_username = ''
                    st.session_state.enroll_password = ''
                    st.session_state.enroll_email = ''
                    st.session_state.enroll_fullname = ''
                except StreamlitAPIException:
                    pass
                st.success(f'{fullname} enrolled successfully.')
                try:
                    os.remove(filename)
                except Exception as e:
                    pass
                return
            else:
                st.error(f"{response.json()['detail']} Please try again.")
                return
    except PermissionError:
        st.error('Kindly refresh the page and try again.')
        return


def verify_user(image_data):
    access_token = st.session_state.get('stored_token', '')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    with open(image_data, "rb") as image_file:
        files = {
            "image": (image_data, image_file, "image/jpg")
        }
        face_recognition_url = f'{API_URL}/face_recognition'
        response = requests.post(face_recognition_url, headers=headers, files=files)
    return response


def update_user(username, name, password, email):
    update_url = f"{API_URL}/update"
    bearer_token = st.session_state.get('stored_token', '')
    headers = {
        'Authorization': f"Bearer {bearer_token}"
    }
    data = {
        'username': username,
        'name': name,
        'password': password,
        'email': email
    }
    response = requests.put(update_url, data=data, headers=headers)
    print('update response', response, response.status_code)
    return response


def delete_user(username):
    bearer_token = st.session_state.get('stored_token', '')
    headers = {
        'Authorization': f"Bearer {bearer_token}"
    }
    unenroll_url = f"{API_URL}/unenroll"
    data = {'username': username}
    response = requests.delete(unenroll_url, headers=headers, data=data)
    print('delete response', response, response.status_code)
    return response


def login_page():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Generate Token"):
        if username and password:
            generate_token(username, password)

    token_input = st.text_input("Enter Token")

    if st.button("Authenticate"):
        if token_input == st.session_state.get('stored_token', ''):
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Invalid token.")


def enrollment_tab():
    st.header("User Enrollment")

    enroll_username = st.text_input("Username", value=st.session_state['enroll_username'], key="enroll_username")
    enroll_password = st.text_input("Password", type="password", value=st.session_state['enroll_password'],
                                    key="enroll_password")
    enroll_email = st.text_input("Email", value=st.session_state['enroll_email'], key="enroll_email")
    enroll_fullname = st.text_input("Full Name", value=st.session_state['enroll_fullname'], key="enroll_fullname")

    st.write("Capture User's Face")
    image_data = capture_image('Scan face to enroll.')

    if st.button("Enroll"):
        if image_data:
            enroll_user(enroll_username, enroll_password, enroll_email, enroll_fullname, image_data)


def verification_tab():
    st.header("User Verification")

    st.write("Scan User's Face")
    image_data = capture_image('Scan face for verification.')

    if st.button("Verify"):
        if image_data:
            response = verify_user(image_data)
            if response.status_code == 200:
                if response.json()['message']:
                    st.success(f"Verified successfully at {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
                    # return
                else:
                    st.error(f"Could not verify you. Try again or contact security.")
                    # return
            else:
                st.error("Verification failed. Please try again.")
                # return

        try:
            os.remove(image_data)
        except Exception as e:
            pass
        return


def update_tab():
    st.header("Update User")

    update_username = st.text_input("Update Username", key="update_username")
    update_name = st.text_input("Name", key="update_name")
    update_password = st.text_input("Password", type="password", key="update_password")
    update_email = st.text_input("Email", key="update_email")

    if st.button("Update"):
        response = update_user(update_username, update_name, update_password, update_email)
        if response.status_code == 200:
            st.success("User information updated!")
            return
        else:
            st.error("Failed to update user. Please try again.")
            return


def delete_tab():
    st.header("Delete User")
    delete_username = st.text_input("Delete Username", key="delete_username")

    if st.button("Delete"):
        response = delete_user(delete_username)
        if response.status_code == 200:
            st.success(f"User {delete_username} deleted!")
            return
        else:
            st.error("Failed to delete user. Please try again.")
            return


def main_dashboard():
    tabs = st.tabs(["Enrollment", "Verification", "Update User", 'Delete User'])

    with tabs[0]:
        enrollment_tab()

    with tabs[1]:
        verification_tab()

    with tabs[2]:
        update_tab()

    with tabs[3]:
        delete_tab()


def main():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if st.session_state['authenticated']:
        main_dashboard()
    else:
        login_page()


if __name__ == '__main__':
    main()
