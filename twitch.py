import json
import requests
from datetime import datetime

with open("conf.json") as conf_file:
    conf = json.load(conf_file)

#account_id = 397517649
#url = f"https://api.opendota.com/api/players/{account_id}"
#response = requests.get(url)
#print(response.json())

def get_app_access_token():
    params = {
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "grant_type": "client_credentials"
    }

    response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
    access_token = response.json()["access_token"]
    return access_token


def get_user(login_name):
    params = {
        "login": login_name
    }

    headers = {
        "Authorization": "Bearer {}".format(conf["user_access_token"]),
        "Client-id": conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
    return {entry["login"]: entry["id"] for entry in response.json()["data"]}


def get_streams(user):
    params = {
        'user_login': user
    }

    headers = {
        "Authorization": "Bearer {}".format(conf["user_access_token"]),
        "Client-id": conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers)
    print(response.json)
    return {entry["user_login"]: entry for entry in response.json()["data"]}


def get_followers(user):
    params = {
        "total": user
    }

    headers = {
        "Authorization": "Bearer {}".format(conf["user_access_token"]),
        "Client-id": conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/channels/followers?broadcaster_id=448248320", params=params, headers=headers)
    return response.json()


online_users = {}


def get_notifications():
    user_name = conf["streamer"]
    streams = get_streams(user_name)
    followers = get_followers(user_name)
    info = {}
    info |= streams
    info |= followers

    global online_users

    notifications = []
    if user_name not in online_users:
        online_users[user_name] = datetime.utcnow()

    if user_name not in streams:
        online_users[user_name] = None
        print("online since is None")
    else:
        started_at = datetime.strptime(streams[user_name]["started_at"], "%Y-%m-%dT%H:%M:%SZ")
        formatted_date = started_at.strftime("%B %d, %Y at %I:%M%p")
        info["formatted_date"] = formatted_date
        online_users[user_name] = formatted_date
        if online_users[user_name] is not None or formatted_date > online_users[user_name]:
            notifications.append(dict(info))

        print(online_users[user_name])
        print(started_at)
        print(notifications)
    return notifications


def get_redemption_reward():
    params = {
        "broadcaster_id": conf["broadcaster_id"],
        "reward_id": conf["reward_id"],
        "status": "UNFULFILLED"
    }

    headers = {
        'Authorization': "Bearer {}".format(conf["user_access_token"]),
        'Client-Id': conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions", params=params, headers=headers)
    return response.json()


def update_redemption_status(rr_id, status):
    params = {
        "broadcaster_id": conf["broadcaster_id"],
        "reward_id": conf["reward_id"],
        "id": rr_id
    }

    headers = {
        'Authorization': "Bearer {}".format(conf["user_access_token"]),
        'Client-Id': conf["client_id"]
    }

    data = {
        'status': status
    }

    response = requests.patch("https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions", params=params, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка при обновлении статуса награды: {response.status_code} {response.reason}")

