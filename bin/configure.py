import os
import json
from bin import render_config


data = {}


def generate_gcs_config_for_user(data, user):
    if "GCP_BUCKET_PROJECT_IDS" in os.environ and "APP_GCS_BUCKETS" in os.environ:
        data[user]["gcs_buckets"] = {}
        for gcs_bucket_name, gcs_bucket_project_id in zip(
            os.environ.get("APP_GCS_BUCKETS", "").split(','),
            os.environ.get("GCP_BUCKET_PROJECT_IDS", "").split(',')
        ):
            if gcs_bucket_project_id not in data[user]["gcs_buckets"]:
                data[user]["gcs_buckets"][gcs_bucket_project_id] = {}
            data[user]["gcs_buckets"][gcs_bucket_project_id]["buckets"] = (
                data[user]["gcs_buckets"][gcs_bucket_project_id].get("buckets", []) + [gcs_bucket_name]
            )
            os.environ["GCP_BUCKET_PROJECT_ID"] = gcs_bucket_project_id
            render_config(f"env/config/gcs", data[user]["gcs_buckets"][gcs_bucket_project_id])
        del os.environ["APP_GCS_BUCKETS"]
        del os.environ["GCP_BUCKET_PROJECT_IDS"]
        data[user].pop("APP_GCS_BUCKETS")
        data[user].pop("GCP_BUCKET_PROJECT_IDS")
    for key in data[user].keys():
        if key not in ["SFTP_UUID", "gcs_buckets"]:
            del os.environ[key]
        if "GCP_BUCKET_PROJECT_ID" in os.environ:
            del os.environ["GCP_BUCKET_PROJECT_ID"]
    return data


render_config(f"env/{os.environ['ENV']}", data)
render_config(f"env/common", data)

for user in os.listdir("env/users"):
    data[user] = {}
    render_config(f"env/users/{user}", data[user])
    render_config(f"env/config/landing", data[user])
    data[user]["SFTP_UUID"] = int(os.environ["APP_SFTP_UUID"]) + 1
    data["APP_SFTP_UUID"] = int(os.environ["APP_SFTP_UUID"]) + 1
    data = generate_gcs_config_for_user(data, user)
    os.environ["APP_SFTP_UUID"] = f'{data[user]["SFTP_UUID"]}'

with open(f"config/{os.environ['ENV']}", "w") as f:
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            f.write(f'SFTP_USER_{key}=\'{json.dumps(value)}\'\n')
        else:
            f.write(f'{key}={value}\n')