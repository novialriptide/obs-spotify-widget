from flask import Flask, render_template, request
import requests
import webbrowser
import schedule
import base64
from config import *


app = Flask(__name__)

accessToken = ""
refreshToken = ""

@app.route("/spotify/callback/code")
def callback():
    global accessToken, refreshToken

    authBasic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {authBasic}"},
        data={
            "code": request.args["code"],
            "redirect_uri": "http://127.0.0.1:5000/spotify/callback/code",
            "grant_type": "authorization_code",
        },
    ).json()
    try:
        accessToken = data["access_token"]
        refreshToken = data["refresh_token"]
    except KeyError:
        print(data)
        return data

    return "<h1> You can now close this window. </h1>"


def refresh():
    global accessToken
    accessToken = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {authBasic}"},
        data={"grant_type": "refresh_token", "refresh_token": refreshToken},
    ).json()["access_token"]


@app.route("/song")
def currentPlaying():
    global accessToken

    render_template("index.html")
    with app.app_context():
        while True:
            schedule.every(60).minutes.do(refresh)
            track_info = requests.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers={"Authorization": f"Bearer {accessToken}"},
            )
            status = track_info.status_code
            if status == 200:
                try:
                    track_info = track_info.json()
                    music = track_info["item"]["name"]
                    artists = ", ".join(
                        [x["name"] for x in track_info["item"]["artists"]]
                    )
                    album_cover = track_info["item"]["album"]["images"][0]["url"]

                    a = track_info["progress_ms"] / track_info["item"]["duration_ms"]
                    current_time = int(a * 100)

                    return render_template(
                        "index.html",
                        current_percent=current_time,
                        album_cover=album_cover,
                        artist_names=artists,
                        song_name=music,
                    )
                except:
                    pass  # if something goes wrong the viewers won't know about it.
            else:
                return render_template(
                    "index.html",
                    current_percent=50,
                    album_cover=None,
                    artist_names="No song detected.",
                    song_name="Error",
                )


if __name__ == "__main__":
    webbrowser.open(
        f"https://accounts.spotify.com/en-US/authorize?client_id={client_id}&scope=user-read-currently-playing&redirect_uri=http://127.0.0.1:5000/spotify/callback/code&response_type=code"
    )
    app.run()
