import time
import requests
import uuid
import os
import math
from helper import generate_rid, create_qc_code, convert_cookie
from urllib.parse import urlencode

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
CHUNK_SIZE = 1024 * 1024 * 8

QRCODE_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_login_code?_rid=%s'
AUTH_LOGIN_STATUE = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_login_status'
UPLOAD_PARAMS = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_upload_params?_rid=%s'
APPLY_UPLOAD_URL = 'https://finderassistancea.video.qq.com/applyuploaddfs'
UPLOAD_FILE_URL = 'https://finderassistancec.video.qq.com/uploadpartdfs?PartNumber=%d&UploadID=%s&QuickUpload=2'
UPLOAD_COMPLETE_URL = 'https://finderassistancea.video.qq.com/completepartuploaddfs?UploadID=%s'
AUTH_DATA_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_data?_rid=%s'
TRACE_KEY_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/get-finder-post-trace-key?_rid=%s'
SEARCH_LOCATION_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_search_location?_rid=%s'
POST_CREATE_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/post_create'
POST_LIST_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/post_list?_rid=%s'
POST_DRAFT_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/get_draft_list?_rid=%s'
COLLECTION_LIST_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/collection/get_collection_list?_rid=%s'
POST_DELETE_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/post_delete?_rid=%s'
COMMENT_LIST_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/comment/comment_list?_rid=%s'
UPDATE_COMMENT_AUTH = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/post_update_comment_auth?_rid=%s'
CREATE_COMMENT = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/comment/create_comment?_rid=%s'
LIKE_COMMENT_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/comment/like_comment?_rid=%s'
DELETE_COMMENT_URL = 'https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/comment/del_comment?_rid=%s'


class WxFinder:
    def __init__(self):
        self.finder_id = None
        self.cookie = None
        self.auth_key = None
        self.weixin_num = None
        self.taskid = None
        self.file_key = None
        self.upload_id = None
        self.file_size = 0
        self.upload_params = None

        self.headers = {
            'Content-Type': 'application/json',
            'X-WECHAT-UIN': '0000000000',
            'Referer': 'https://channels.weixin.qq.com/platform',
            'User-Agent': USER_AGENT
        }

    def get_qrcode(self):
        url = QRCODE_URL % generate_rid()
        params = {
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": "",
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'Referer': 'https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1',
        })
        response = requests.post(url, headers=self.headers, json=params)
        token = response.json()['data']['token']
        login_url = f"https://channels.weixin.qq.com/mobile/confirm_login.html?token={token}"
        create_qc_code(login_url)
        self.auth_login_status(token)

    def __login(self, cookies):
        self.cookie = convert_cookie(cookies)
        auth_data = self.get_auth_data()
        self.finder_id = auth_data['finderUser']['finderUsername']
        self.__get_upload_params()

    def set_cookie(self, find_id, cookie):
        self.cookie = cookie
        self.finder_id = find_id
        self.__get_upload_params()

    def auth_login_status(self, token):
        params = {
            "token": token,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": "",
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7,
            "_rid": generate_rid()
        }
        self.headers.update({
            'Referer': 'https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1',
        })

        url = AUTH_LOGIN_STATUE + '?' + urlencode(params)
        while True:
            response = requests.post(url, headers=self.headers, json=params)
            ret = response.json()
            print(ret)
            if ret['errCode'] != 0:
                return

            data = ret['data']
            if data['status'] == 0 and data['acctStatus'] == 0:
                print('未扫码')
            elif data['status'] == 5 and data['acctStatus'] == 1:
                print('已扫码 未确认')
            elif data['status'] == 1 and data['acctStatus'] == 1:
                print('登录成功')
                cookies = response.cookies.items()
                self.__login(cookies)
                return
            elif data['status'] == 4:
                print("二维码已经过期")
            else:
                print('login error')
            time.sleep(1)

    def upload_video(self, file_path):
        return self.__upload(file_path, 20302)

    def upload_picture(self, file_path):
        return self.__upload(file_path, 20304)

    def upload_music(self, file_path):
        return self.__upload(file_path, 20305)

    def __upload(self, file_path,file_type):
        self.taskid = uuid.uuid4()
        self.file_size = os.path.getsize(file_path)
        self.file_key = os.path.basename(file_path)

        chunks = self.split_file()

        file_size_array = [x['end'] for x in chunks]

        self.upload_id = self.apply_upload_fs(file_type, file_size_array)

        part_num = 0
        part_info = []
        for item in chunks:
            part = part_num + 1
            with open(file_path, 'rb') as f:
                f.seek(item['start'])
                file_chunk_data = f.read(item['end'] - item['start'])
            upload_resp = self.upload_file(file_type, part, file_chunk_data)
            part_info.append({'PartNumber': part, 'ETag': upload_resp['ETag']})
            part_num += 1

        return self.upload_complete(file_type, part_info)

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

    def __gen_x_args(self, file_type):
        args = {
            'apptype': 251,
            'filetype': file_type,
            'weixinnum': self.weixin_num,
            'filekey': self.file_key,
            'filesize': self.file_size,
            'taskid': self.taskid,
            'scene': 2
        }
        return urlencode(args)

    def apply_upload_fs(self, file_type, file_size_array):
        payload = {"BlockSum": len(file_size_array), "BlockPartLength": file_size_array}
        headers = {
            'Authorization': self.auth_key,
            'Content-MD5': 'null',
            'X-Arguments': self.__gen_x_args(file_type),
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT

        }
        print('apply_upload_fs request: ', payload)
        response = requests.put(APPLY_UPLOAD_URL, headers=headers, json=payload)
        print('apply_upload_fs request: ', response.json())
        return response.json()['UploadID']

    def upload_file(self, file_type, part_num, file_chunk):
        url = UPLOAD_FILE_URL % (part_num, self.upload_id)

        headers = {
            'Authorization': self.auth_key,
            'Content-MD5': 'null',
            'X-Arguments': self.__gen_x_args(file_type),
            'Content-Type': 'application/octet-stream',
            'User-Agent': USER_AGENT
        }
        print("upload_file : ", url)
        print("X-Arguments: ", headers['X-Arguments'])
        resp = requests.put(url, headers=headers, data=file_chunk)
        print('upload response: ', resp.text)
        return resp.json()

    def upload_complete(self, file_type, part_info):
        url = UPLOAD_COMPLETE_URL % self.upload_id
        headers = {
            'Authorization': self.auth_key,
            'Content-MD5': 'null',
            'X-Arguments': self.__gen_x_args(file_type),
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
        """
        "data": {
            "authKey": "303e020101043730350201010201010204af34dd6c020100020100020404030201020320141d02044a124475020419efe97902046743dda802049fa9bbd40400",
            "uin": 2939477356,
            "appType": 251,
            "videoFileType": 20302,
            "pictureFileType": 20304,
            "thumbFileType": 20350,
            "musicType": 20305,
            "scene": 2
        }
        :return:
        """
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
        response = requests.post(UPLOAD_PARAMS % generate_rid(), headers=headers, json=params)
        print(response.text)
        data = response.json()['data']
        self.auth_key = data['authKey']
        self.weixin_num = data['uin']
        self.upload_params = data

    def get_auth_data(self):
        """
        获取当前登录的用户信息
        :return:
        """
        params = {
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform',
            'Cookie': self.cookie
        })
        response = requests.post(AUTH_DATA_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def get_post_list(self, page=1):
        """视频列表"""
        params = {
            "pageSize": 20,
            "currentPage": page,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/list',
            'Cookie': self.cookie
        })
        response = requests.post(POST_LIST_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def get_draft_list(self, page=1):
        """草稿列表"""
        params = {
            "pageSize": 20,
            "currentPage": page,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/list?tab=draft',
            'Cookie': self.cookie
        })
        response = requests.post(POST_DRAFT_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def get_collection_list(self, page=1):
        """合集列表"""
        params = {
            "pageNum": page,
            "pageSize": 20,
            "collectionScene": 0,
            "collectionBusinessType": 0,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/list?tab=collection',
            'Cookie': self.cookie
        })
        response = requests.post(COLLECTION_LIST_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def delete_post(self, export_id):
        """删除视频"""
        params = {
            "objectId": export_id,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/list',
            'Cookie': self.cookie
        })
        response = requests.post(POST_DELETE_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def get_comment_list(self, export_id, comment_selection=False):
        """
        视频的评论列表
        comment_selection=True 精选评论
        """
        params = {
            "lastBuff": "",
            "exportId": export_id,
            "commentSelection": comment_selection,
            "forMcn": False,
            "timestamp": "1727315193214",
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/comment',
            'Cookie': self.cookie
        })
        response = requests.post(COMMENT_LIST_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def update_comment_auth(self, export_id, comment_flag=0, comment_selection_flag=0):
        """
        修改视频评论的权限
        comment_flag=0 开启评论  comment_flag=1 关闭评论
        comment_selection_flag=0 将仅公开已精选的评论 comment_selection_flag=1 关闭
        """
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/comment',
            'Cookie': self.cookie
        })
        params = {
            "objectId": export_id,
            "commentFlag": comment_flag,
            "commentSelectionFlag": comment_selection_flag,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        response = requests.post(UPDATE_COMMENT_AUTH % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def create_comment(self, export_id, content, reply_comment_id=None):
        """添加评论"""
        params = {
            "replyCommentId": "" if reply_comment_id is None else reply_comment_id,
            "content": content,
            "clientId": uuid.uuid4(),
            "rootCommentId": "",
            "comment": {},
            "exportId": export_id,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "scene": 7,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/comment',
            'Cookie': self.cookie
        })
        response = requests.post(CREATE_COMMENT % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def like_comment(self, export_id, comment_id, scene=1):
        """
        评论点赞
        scene=1 点赞 scene=2取消点赞
        """
        params = {
            "commentId": comment_id,
            "scene": scene,
            "exportId": export_id,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None,
            "pluginSessionId": None,
            "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/comment',
            'Cookie': self.cookie
        })
        response = requests.post(LIKE_COMMENT_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def delete_comment(self, export_id, comment_id):
        """删除评论"""
        params = {
            "exportId": export_id,
            "commentId": comment_id,
            "timestamp": int(time.time() * 1000),
            "_log_finder_uin": "",
            "_log_finder_id": self.finder_id,
            "rawKeyBuff": None, "pluginSessionId": None, "scene": 7, "reqScene": 7
        }
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/comment',
            'Cookie': self.cookie
        })
        response = requests.post(DELETE_COMMENT_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def get_trace_key(self):
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
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/create',
            'Cookie': self.cookie
        })
        response = requests.post(TRACE_KEY_URL % generate_rid(), headers=self.headers, json=params)
        print('get trace key response: ', response.text)
        return response.json()['data']['traceKey']

    def search_location(self):
        """获取经纬度和地理位置信息"""
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
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/create',
            'Cookie': self.cookie
        })
        response = requests.post(SEARCH_LOCATION_URL % generate_rid(), headers=self.headers, json=params)
        return response.json()['data']

    def post_create(self, video_url):
        """发布视频"""
        url = SEARCH_LOCATION_URL % generate_rid()
        self.headers.update({
            'X-WECHAT-UIN': str(self.weixin_num),
            'Referer': 'https://channels.weixin.qq.com/platform/post/create',
            'Cookie': self.cookie
        })

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

        response = requests.post(url, headers=self.headers, json=params)


if __name__ == '__main__':
    file_path = '/Users/dengmin/Desktop/28804_1727070825.mp4'
    finder = WxFinder()
    # finder.upload(file_path)
    # finder.get_trace_key()
    # location = finder.search_location()
    # print(location)
    # print(finder.get_draft_list())
    # print(finder.get_auth_data())
    finder.get_qrcode()
    # location = finder.search_location()
    # print(location)
    # print(finder.get_post_list())
    # print(finder.upload_video(file_path))
    pass
