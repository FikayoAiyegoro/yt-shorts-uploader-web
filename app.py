from flask import Flask, request, render_template, redirect, session, url_for
import os
import threading
import time
import random
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import Flow

# Setup
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session cookies

UPLOAD_FOLDER = "uploads"
TOKEN_FOLDER = "tokens"
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/userinfo.email"
]


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TOKEN_FOLDER, exist_ok=True)

# ========== Google OAuth Routes ==========
@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    import requests  # move to the top if you prefer

    state = session["state"]
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials

    # Request user profile info using the access token
    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    )

    if not userinfo_response.ok:
        return "❌ Failed to fetch user info."

    user_info = userinfo_response.json()
    user_email = user_info.get("email")
    if not user_email:
        return "❌ Could not retrieve user email."

    token_path = os.path.join(TOKEN_FOLDER, f"{user_email}_token.pkl")
    with open(token_path, "wb") as token_file:
        pickle.dump(credentials, token_file)

    session["user_email"] = user_email
    return redirect(url_for("upload"))



# ========== YouTube Upload Logic ==========

def get_youtube_client(user_email):
    token_path = os.path.join(TOKEN_FOLDER, f"{user_email}_token.pkl")
    if not os.path.exists(token_path):
        return None

    with open(token_path, "rb") as token_file:
        creds = pickle.load(token_file)
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, file_path, title="My YouTube Short", description="Uploaded automatically"):
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["Shorts"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public",
                "madeForKids": False
            }
        },
        media_body=MediaFileUpload(file_path)
    )
    response = request.execute()
    print(f"✅ Uploaded: {file_path} with title: {title}")
    return response

def schedule_upload(user_email, video_path, delay_minutes):
    print(f"⏳ Waiting {delay_minutes} minutes to upload {video_path}")
    time.sleep(delay_minutes * 60)

    youtube = get_youtube_client(user_email)
    if not youtube:
        print(f"❌ Could not find token for user: {user_email}")
        return

    titles = [
        "Smelling A Bag of 2017 Air!",
        "He found air from 2017",
        "Air 2017",
        "What did I just watch?",
        "2023 vs 2017 Air 😂",
        "This smells like 2017...",
    ]
    title = random.choice(titles)
    upload_video(youtube, video_path, title=title)
    os.remove(video_path)

# ========== Main Upload Page ==========

@app.route("/", methods=["GET", "POST"])
def upload():
    user_email = session.get("user_email")
    if not user_email:
        return redirect("/login")

    if request.method == "POST":
        video = request.files["video"]
        delay = int(request.form["delay"])
        filename = video.filename
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        video.save(path)

        threading.Thread(target=schedule_upload, args=(user_email, path, delay)).start()

        return f"✅ Scheduled: {filename} in {delay} minutes!"
    return render_template("upload_form.html")

if __name__ == "__main__":
    app.run(debug=True)
