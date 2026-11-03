# 《不问凡尘》NPC化身mod制作脚本
![](Gemini_Generated_Image_vk8qlavk8qlavk8q.jfif)
## 背景

《不问凡尘》的NPC动作一般有4段，前3段为日常随机动作，第4段为结缘动作。
游戏中本地制作的化身仅支持单段视频循环4遍，同时还存在文件大小(500MB)、视频时长(30S)和分辨率压缩等诸多限制。为了突破此限制，于是有了此脚本。

本脚本用于拼接4段独立动作视频，**每段视频前后自动扩展1秒静帧画面（官方默认首帧、末帧各持续1秒）**，输出烘焙产物 **`b1.mp4` + `b1.mp4.segments.json`**，用来替换游戏自动烘焙生成的文件，实现4段不同动作播放。

## 前置准备

1.**4段视频素材**
- MP4格式、分辨率、帧率**必须完全一致**
- 文件命名：`v1.mp4`、`v2.mp4`、`v3.mp4`、`v4.mp4` 分别对应'idle', 'special_idle_01', 'special_idle_02', 'idle_married'，在游戏中v1，v2，v3出现概率逐步递减，v4为结缘后的固定动画。(ps：目前高人气老板娘苏倾盏怎么只有一段动画，理论上可以升级为4段，期待道友们的发挥。)

2.**执行参数**

- **SpaceID**：5位数字，NPC所在场景的编号，可在游戏目录中查询
- **NpcID**：6位数字，NPC编号，可查阅目录中《NPC索引.md》获取

例如：念乔对应的SpaceID为15011，NpcID为150101
D:\Program Files (x86)\Steam\steamapps\common\A1\WorldApart_Data\StreamingAssets\MergedVideoResources~\spaces\ **15011**\npc_**150101**

## 操作步骤

1. 将 `v1.mp4`、`v2.mp4`、`v3.mp4`、`v4.mp4` 放到文件夹中。

2. 双击运行 `run.bat`。

3. 根据控制台提示依次输入：

   - 5位数字 SpaceID（场景号）
   - 6位数字 NpcID（NPC编号）

4. 脚本自动执行完整流程：

   - 提取每段视频首帧、末帧，生成前后各1秒静帧片段
   - 全部片段进行拼接，输出 `b1.mp4`、`b1.mp4.segments.json`
   - 生成 `tmp_frames` 临时文件夹，存放中间图片与临时视频片段

5. 脚本执行完毕，把output中的 `b1.mp4`、`b1.mp4.segments.json` 复制到本地Mod对应的NPC目录。

   > 示例完整路径：
   > `C:\Users\Administrator\AppData\LocalLow\Nuverse\WorldApart\Mods\念乔\spaces\15011\npc_150101`
   > 将 `b1.mp4`、`b1.mp4.segments.json` 粘贴到此目录。

   Mod文件夹目录结构（必须严格遵守层级），参考官方文档
https://bytedance.larkoffice.com/docx/G056drNvvoQelfxxJLDcyFimnGg

6. 如想要上传至创意工坊，在游戏中的**化身**-**上传作品**-**已有文件夹**中将整个Mod文件夹目录上传即可，理论上没有大小限制。但严重违和的话可能会被steam短暂封禁，不要问我怎么知道的。

## 注意事项

1. `v1.mp4~v4.mp4` 只用于本地脚本运算，**不需要放进Mod文件夹**。
2. `tmp_frames` 是运行产生的临时文件夹，确认输出文件正常后可以直接删除。
3. **风险提醒**：如果在游戏内重新编辑/烘焙化身，游戏会自动覆盖手动放入的 `b1.mp4` 和 `b1.mp4.segments.json`，覆盖后需要重新复制脚本输出产物进去。
4. 音频规则：脚本保留原视频音频；前后扩展出来的1秒静帧片段为静音。

## 故障排查

1. 双击bat窗口一闪而过

   > 确认Python、ffmpeg已经正确配置系统环境变量；可以打开cmd进入脚本目录手动执行命令 `python proc.py 15011 150101`，查看具体报错信息。

2. ffmpeg拼接报错

   > 检查v1‑v4.mp4分辨率、帧率是否完全一致；查看控制台打印的stderr错误日志定位问题。

3. 游戏不加载自定义b1文件

   > 检查文件夹层级完全和示例一致；确认没有放错目录；避免触发游戏自动重烘焙覆盖文件。

4. 运行报 AssertionError

   > ffprobe读取源视频帧数信息异常，尝试更换源视频文件重试。
