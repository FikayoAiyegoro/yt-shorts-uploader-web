import os
import time
import random
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# Authenticate with YouTube
def authenticate_youtube():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

# Upload a single video
def upload_video(youtube, file_path, title="My YouTube Short", description="Uploaded automatically"):
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["Shorts"],
                "categoryId": "22"  # People & Blogs
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

def main():
    youtube = authenticate_youtube()
    video_folder = "shorts"

    titles = [
        "Smelling A Bag of 2017 Air!",
        "Smelling A Bag of 2017 Air",
        "Smelling Air from 2017",
        "Smelling 2017 air",
        "bag of air from 2017",
        "He found air from 2017",
        "Air 2017",
        "2017 bag of air",
        "I found air from 2017",
    ]

    while True:
        videos = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
        if not videos:
            print("❌ No videos found in 'shorts/' folder.")
            return

        video = random.choice(videos)
        video_path = os.path.join(video_folder, video)

        title = random.choice(titles)  # Pick a random title
        upload_video(youtube, video_path, title=title)
        #os.remove(video_path)  # Delete after upload

        time.sleep(1800)
if __name__ == "__main__":
    main()
