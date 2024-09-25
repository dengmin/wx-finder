### 微信视频号助手

- 2024-09-25 文件分片上传
- 2024-09-25 获取经纬度和位置信息
- 2024-09-25 获取发表视频需要的参数traceKey


#### 运行代码
```python
file_path = '/Users/dengmin/Desktop/28804_1727070825.mp4'
finder_id = 'v2_060000231003b20faec8c4e18d1dc5dcce0cea34b0777a2ed442219fded549577d31f6cbbb64@finder'
finder = WxFinder(finder_id)
finder.upload(file_path)
```
