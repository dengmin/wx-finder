### 微信视频号助手

- 2024-09-25 文件分片上传
- 2024-09-25 获取经纬度和位置信息
- 2024-09-25 获取发表视频需要的参数traceKey
- 发布视频(未完成)
- 2024-09-26 新增评论相关接口 (评论列表 设置评论权限 回复评论 点赞 删除)

#### 接口列表

##### get_auth_data() 
获取当前登录的用户信息

##### get_post_list()
获取视频列表
- page 当前页数

##### get_draft_list
获取草稿列表

- page 当前页数

##### get_collection_list
获取合集列表

- page 当前页数

##### delete_post
删除视频
- export_id 视频ID

##### get_comment_list
获取评论列表
- export_id 视频ID
- comment_selection(True/False) 精选评论

##### update_comment_auth
更改视频评论的权限
- export_id 视频ID
- comment_flag comment_flag=0 开启评论  comment_flag=1 关闭评论
- comment_selection_flag comment_selection_flag=0 将仅公开已精选的评论 comment_selection_flag=1 关闭

##### create_comment
创建评论
- export_id 视频ID
- content 评论内容
- reply_comment_id 回复的评论ID

##### like_comment
评论点赞
- export_id 视频ID
- comment_id 评论id
- scene scene=1 点赞 scene=2取消点赞

##### delete_comment
删除评论
- export_id 视频ID
- comment_id 评论id

##### search_location
获取当前请求的位置信息


##### post_create
创建视频git
- video_url 视频url

##### upload
视频文件上传


#### 运行代码
```python
file_path = '/Users/dengmin/Desktop/28804_1727070825.mp4'
finder = WxFinder()
finder.get_qrcode() # 生成登录的二维码, 扫码登录
finder.upload(file_path)
```
