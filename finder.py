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
TRACE_KEY_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/get-finder-post-trace-key?_rid=%s'
SEARCH_LOCATION_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_search_location?_rid=%s'
POST_CREATE_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/post_create'


def generate_rid():
    e = int(time.time())
    t = hex(e)[2:]
    e = ''.join(random.choice('01234567') for _ in range(8))
    return t + '-' + e


class WxFinder:
    def __init__(self, cookie, finder_id):
        self.cookie = cookie
        self.finder_id = finder_id
        self.auth_key = None
        self.weixin_num = None
        self.taskid = None
        self.file_key = None
        self.upload_id = None
        self.file_size = 0

        self.__get_upload_params()

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

    def __get_upload_params(self):
        url = UPLOAD_PARAMS % generate_rid()

        headers = {
            'Content-Type': 'application/json',
            'X-WECHAT-UIN': '0000000000',
            'Referer': 'https://channels.weixin.qq.com/platform/post/list',
            'User-Agent': USER_AGENT,
            'Cookie': self.cookie
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

    def get_trace_key(self):
        url = TRACE_KEY_URL % generate_rid()
        params = {
            "objectId": None,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }

        headers = {
            'Content-Type': 'application/json',
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/create',
            'User-Agent': USER_AGENT,
            'Cookie': self.cookie
        }
        response = requests.post(url, headers=headers, json=params)
        print('get trace key response: ', response.text)
        return response.json()['data']['traceKey']

    def search_location(self):
        """获取经纬度和地理位置信息"""
        url = SEARCH_LOCATION_URL % generate_rid()
        params = {
            "query": "",
            "cookies": "",
            "longitude": 0,
            "latitude": 0,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        headers = {
            'Content-Type': 'application/json',
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/create',
            'User-Agent': USER_AGENT,
            'Cookie': self.cookie
        }
        response = requests.post(url, headers=headers, json=params)
        return response.json()['data']

    def post_create(self, video_url):
        """发布视频"""
        url = SEARCH_LOCATION_URL % generate_rid()
        headers = {
            'Content-Type': 'application/json',
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/create',
            'User-Agent': USER_AGENT,
            'Cookie': self.cookie
        }

        params = {
            "objectType": 0,
            "longitude": 0,
            "latitude": 0,
            "feedLongitude": 0,
            "feedLatitude": 0,
            "originalFlag": 0,
            "topics": [
                "早操"
            ],
            "isFullPost": 1,
            "handleFlag": 2,
            "videoClipTaskId": "14486175796297140387",
            "traceInfo": {
                "traceKey": "FPT_1726886706_34012748",
                "uploadCdnStart": 1726886705,
                "uploadCdnEnd": 1726886724
            },
            "objectDesc": {
                "mpTitle": "",
                "description": "test#早操",
                "extReading": {},
                "mediaType": 4,
                "location": {
                    "latitude": 30.25727081298828,
                    "longitude": 120.20523071289062,
                    "city": "杭州市",
                    "poiClassifyId": ""
                },
                "topic": {
                    "finderTopicInfo": "<finder><version>1</version><valuecount>2</valuecount><style><at></at></style><value0><![CDATA[test]]></value0><value1><topic><![CDATA[#早操#]]></topic></value1></finder>"
                },
                "event": {},
                "mentionedUser": [],
                "media": [
                    {
                        "url": video_url,
                        "fileSize": 2763522,
                        "thumbUrl": "https://finder.video.qq.com/251/20304/stodownload?bizid=1023&dotrans=0&encfilekey=rjD5jyTuFrIpZ2ibE8T7YmwgiahniaXswqzKb4w3NnVU953icRb7exZw86aiaLuCVNbSiafVob1LWbThtpVficZukFXGuU3q3FxHmYwxZ1wdtKJyx3owauWlqqA2A&hy=SH&idx=1&m=&scene=2&token=cztXnd9GyrE0mHAvACDCicLTD89dkwBjgG4dcq517ib22MhfUDCSRcSrLIWjG7Xl7A9S3hwriaFICBXl4r2icSzoicA&uzid=2",
                        "fullThumbUrl": "https://finder.video.qq.com/251/20304/stodownload?bizid=1023&dotrans=0&encfilekey=rjD5jyTuFrIpZ2ibE8T7YmwgiahniaXswqzKb4w3NnVU953icRb7exZw86aiaLuCVNbSiafVob1LWbThtpVficZukFXGuU3q3FxHmYwxZ1wdtKJyx3owauWlqqA2A&hy=SH&idx=1&m=&scene=2&token=cztXnd9GyrE0mHAvACDCicLTD89dkwBjgG4dcq517ib22MhfUDCSRcSrLIWjG7Xl7A9S3hwriaFICBXl4r2icSzoicA&uzid=2",
                        "mediaType": 4,
                        "videoPlayLen": 9,
                        "width": 1280,
                        "height": 720,
                        "md5sum": "383f1b32-e2a5-4cae-898c-4b23cd43cc68",
                        "cardShowStyle": 2,
                        "coverUrl": "https://finder.video.qq.com/251/20304/stodownload?bizid=1023&dotrans=0&encfilekey=rjD5jyTuFrIpZ2ibE8T7YmwgiahniaXswqzKb4w3NnVU953icRb7exZw86aiaLuCVNbSiafVob1LWbThtpVficZukFXGuU3q3FxHmYwxZ1wdtKJyx3owauWlqqA2A&hy=SH&idx=1&m=&scene=2&token=cztXnd9GyrE0mHAvACDCicLTD89dkwBjgG4dcq517ib22MhfUDCSRcSrLIWjG7Xl7A9S3hwriaFICBXl4r2icSzoicA&uzid=2",
                        "fullCoverUrl": "https://finder.video.qq.com/251/20304/stodownload?bizid=1023&dotrans=0&encfilekey=rjD5jyTuFrIpZ2ibE8T7YmwgiahniaXswqzKb4w3NnVU953icRb7exZw86aiaLuCVNbSiafVob1LWbThtpVficZukFXGuU3q3FxHmYwxZ1wdtKJyx3owauWlqqA2A&hy=SH&idx=1&m=&scene=2&token=cztXnd9GyrE0mHAvACDCicLTD89dkwBjgG4dcq517ib22MhfUDCSRcSrLIWjG7Xl7A9S3hwriaFICBXl4r2icSzoicA&uzid=2",
                        "urlCdnTaskId": "14486175796297140387"
                    }
                ],
                "member": {}
            },
            "report": {
                "clipKey": "14486175796297140387",
                "draftId": "14486175796297140387",
                "timestamp": "1726886730095",
                "_log_finder_uin": "",
                "_log_finder_id": self.finder_id,
                "rawKeyBuff": None,
                "pluginSessionId": None,
                "scene": 7,
                "reqScene": 7,
                "height": 720,
                "width": 1280,
                "duration": 9.7,
                "fileSize": 2763522,
                "uploadCost": 5826
            },
            "postFlag": 0,
            "mode": 1,
            "clientid": "d4de43fb-756d-4698-bd5e-40f4c88bfaa1",
            "timestamp": "1726887486269",
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }

        response = requests.post(url, headers=headers, json=params)



if __name__ == '__main__':
    file_path = '/Users/dengmin/Desktop/28804_1727070825.mp4'
    finder_id = 'v2_060000231003b20faec8c4e18d1dc5dcce0cea34b0777a2ed442219fded549577d31f6cbbb64@finder'
    cookie = 'cookie....'
    finder = WxFinder(cookie, finder_id)
    finder.upload(file_path)
    #finder.get_trace_key()
    #location = finder.search_location()
    #print(location)
    pass

