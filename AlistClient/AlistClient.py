import httpx
import urllib.parse


class AlistClient:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.__username__ = username
        self.__password__ = password
        self.client = httpx.Client(base_url=f"https://{self.host}", timeout=120)
        self.__token__ = self.__get_token__()

    def __get_token__(self):
        response = self.client.post("/api/auth/login",
                                    json={"username": self.__username__,
                                          "password": self.__password__
                                          })
        response_json = response.json()
        if response_json["code"] == 200:
            return response_json["data"]["token"]
        else:
            raise ValueError(f"Failed to get token; {response_json['message']}")

    def stream_upload(self, local_file_path: str, target_dir: str, overwrite: bool = True):
        file_name = local_file_path.split("/")[-1]
        if file_name.endswith(".png"):
            MMIE_type = "image/png"
        else:
            MMIE_type = "application/octet-stream"
        remote_path = f"{target_dir}/{file_name}"
        if not overwrite:
            metadata_response = self.fetch_metadata(remote_path)
            if metadata_response["code"] == 200:
                file_bytes = open(local_file_path, "rb").read()
                local_file_size = len(file_bytes)
                if metadata_response["data"]["size"] == local_file_size:
                    return {"code": 204, "message": "File already exist, skip as user defined setting."}
        file_bytes = open(local_file_path, "rb").read()
        url_encoded_path = urllib.parse.quote(remote_path)
        header = {
            "Authorization": self.__token__,
            "Content-Type": MMIE_type,
            "Content-Length": str(len(file_bytes)),
            "File-Path": url_encoded_path,
            "As-Task": "false"
        }
        response = self.client.put("/api/fs/put", headers=header, content=file_bytes, timeout=120)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to upload file; {response.content}")

    def list_path(self, path: str, password: str = None):
        header = {
            "Authorization": self.__token__,
        }
        body = {
            "path": path,
        }
        if password:
            body["password"] = password
        res = self.client.post("/api/fs/dirs", headers=header, json=body)
        return res.json()

    def fetch_metadata(self, path: str, password: str = None):
        header = {
            "Authorization": self.__token__,
        }
        body = {
            "path": path,
        }
        if password:
            body["password"] = password
        res = self.client.post("/api/fs/get", headers=header, json=body)
        return res.json()

    def delete_file(self, file_name: str | list[str], target_dir: str):
        header = {
            "Authorization": self.__token__,
        }
        if type(file_name) is str:
            file_name = [file_name]
        body = {
            "name": file_name,
            "dir": target_dir,
        }
        res = self.client.post("/api/fs/remove", headers=header, json=body)
        return res.json()

    def create_dir(self, target_dir: str):
        header = {
            "Authorization": self.__token__,
            "Content-Type": "application/json"
        }
        body = {
            "path": target_dir,
        }
        res = self.client.post("/api/fs/mkdir", headers=header, json=body)
        return res.json()
