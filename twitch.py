import json
import requests
from datetime import datetime

with open("conf.json") as conf_file:
    conf = json.load(conf_file)


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
        "Authorization": "Bearer {}".format(conf["access_token"]),
        "Client-id": conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
    return response.json()


def get_streams(user):
    params = {
        'user_login': user
    }

    headers = {
        "Authorization": "Bearer {}".format(conf["access_token"]),
        "Client-id": conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers)
    return {entry["user_login"]: entry for entry in response.json()["data"]}
user=get_user(conf["streamer"])
stream=get_streams(conf["streamer"])
print(user)
print(stream)


def get_followers(user):
    params = {
        "total": user
    }

    headers = {
        "Authorization": "Bearer {}".format(conf["user_access_token"]),
        "Client-id": conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/users/follows?to_id=448248320&first=1", params=params, headers=headers)
    return response.json()


online_users = {}


def get_redemption_reward(broadcaster_id, reward_id):
    params = {
        "broadcaster_id": broadcaster_id,
        "reward_id": reward_id,
        "status": "UNFULFILLED"
    }

    headers = {
        'Authorization': "Bearer {}".format(conf["user_access_token"]),
        'Client-Id': conf["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions", params=params, headers=headers)
    return response.json()
reward=get_redemption_reward(conf["broadcaster_id"], conf["reward_id"])
print(reward)


def get_connections():

    url = "https://api.twitch.tv/helix/users/@me/connections"

    headers = {"Authorization": "Bearer " + conf["access_token"]}
    response = requests.get(url, headers=headers)
    return response.json()
con=get_connections()
print(con)

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