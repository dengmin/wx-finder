import time
import requests
import uuid
import os
import math
import random
from urllib.parse import urlencode

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
CHUNK_SIZE = 1024 * 1024 * 8

UPLOAD_PARAMS = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_upload_params?_rid=%s'
APPLY_UPLOAD_URL = 'https://finderassistancea.video.qq.com/applyuploaddfs'
UPLOAD_FILE_URL = 'https://finderassistancec.video.qq.com/uploadpartdfs?PartNumber=%d&UploadID=%s&QuickUpload=2'
UPLOAD_COMPLETE_URL = 'https://finderassistancea.video.qq.com/completepartuploaddfs?UploadID=%s'

COOKIE = 'cookie'


def generate_rid():
    e = int(time.time())
    t = hex(e)[2:]
    e = ''.join(random.choice('01234567') for _ in range(8))
    return t + '-' + e


class WxFinder:
    def __init__(self, finder_id):
        self.finder_id = finder_id
        self.auth_key = None
        self.weixin_num = None
        self.taskid = None
        self.file_key = None
        self.upload_id = None
        self.file_size = 0

    def upload(self, file_path):
        self.taskid = uuid.uuid4()
        self.file_size = os.path.getsize(file_path)
        self.file_key = os.path.basename(file_path)

        chunks = self.split_file()

        file_size_array = [x['end'] for x in chunks]

        self.upload_id = self.apply_upload_fs(file_size_array)

        part_num = 0
        part_info = []
        for item in chunks:
            part = part_num + 1
            with open(file_path, 'rb') as f:
                f.seek(item['start'])
                file_chunk_data = f.read(item['end'] - item['start'])
            upload_resp = self.upload_file(part, file_chunk_data)
            part_info.append({'PartNumber': part, 'ETag': upload_resp['ETag']})
            part_num += 1

        self.upload_complete(part_info)

    def split_file(self):
        """文件按照8M分片"""
        total_chunk = math.ceil(self.file_size / CHUNK_SIZE)

        chunks = []
        current_chunk = 1
        while current_chunk <= total_chunk:
            start = (current_chunk - 1) * CHUNK_SIZE
            end = min(self.file_size, start + CHUNK_SIZE)
            chunks.append({'start': start, 'end': end})
            current_chunk = current_chunk + 1
        print('文件分片结果', chunks)
        return chunks

    def __gen_x_args(self):
        args = {
            'apptype': 251,
            'filetype': 20302,
            'weixinnum': self.weixin_num,
            'filekey': self.file_key,
            'filesize': self.file_size,
            'taskid': self.taskid,
            'scene': 2
        }
        return urlencode(args)

    def apply_upload_fs(self, file_size_array):
        payload = {"BlockSum": len(file_size_array), "BlockPartLength": file_size_array}
        headers = {
            'Authorization': self.auth_key,
            'Content-MD5': 'null',
            'X-Arguments': self.__gen_x_args(),
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT

        }
        print('apply_upload_fs request: ', payload)
        response = requests.put(APPLY_UPLOAD_URL, headers=headers, json=payload)
        print('apply_upload_fs request: ', response.json())
        return response.json()['UploadID']

    def upload_file(self, part_num, file_chunk):
        url = UPLOAD_FILE_URL % (part_num, self.upload_id)

        headers = {
            'Authorization': self.auth_key,
            'Content-MD5': 'null',
            'X-Arguments': self.__gen_x_args(),
            'Content-Type': 'application/octet-stream',
            'User-Agent': USER_AGENT
        }
        print("upload_file : ", url)
        print("X-Arguments: ", headers['X-Arguments'])
        resp = requests.put(url, headers=headers, data=file_chunk)
        print('upload response: ', resp.text)
        return resp.json()

    def upload_complete(self, part_info):
        url = UPLOAD_COMPLETE_URL % self.upload_id
        headers = {
            'Authorization': self.auth_key,
            'Content-MD5': 'null',
            'X-Arguments': self.__gen_x_args(),
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT
        }

        params = {
            'TransFlag': "0_0",
            'PartInfo': part_info
        }
        print('upload_complete request: ', params)
        response = requests.post(url, headers=headers, json=params)
        print('upload_complete response: ', response.text)
        return response.json()['DownloadURL']

    def get_upload_params(self):
        url = UPLOAD_PARAMS % generate_rid()

        headers = {
            'Content-Type': 'application/json',
            'X-WECHAT-UIN': '0000000000',
            'Referer': 'https://channels.weixin.qq.com/platform/post/list',
            'User-Agent': USER_AGENT,
            'Cookie': COOKIE
        }

        params = {
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        response = requests.post(url, headers=headers, json=params)
        print(response.text)
        data = response.json()['data']
        self.auth_key = data['authKey']
        self.weixin_num = data['uin']


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    file_path = '/Users/dengmin/Desktop/28804_1727070825.mp4'
    finder_id = 'v2_0600002'
    finder = WxFinder(finder_id)
    finder.get_upload_params()
    finder.upload(file_path)
    pass

