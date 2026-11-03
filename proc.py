import json
import subprocess
import sys
from pathlib import Path

# =====================配置参数=====================
INPUT_VIDEO_PATHS = [
    "./v1.mp4",
    "./v2.mp4",
    "./v3.mp4",
    "./v4.mp4",
]
# 输出文件夹
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

OUT_VIDEO_NAME = OUTPUT_DIR / "b1.mp4"
OUT_JSON_NAME = OUTPUT_DIR / "b1.mp4.segments.json"

TMP_DIR = Path("./tmp_frames")
TMP_DIR.mkdir(exist_ok=True)
# ========== 前后静帧片段时长(单位:秒)，建议选值：0.5 / 1.0 / 1.5 数字越大场景切换可能越生硬 ==========
EXTEND_SEC = 0.5

# 读取命令行参数： space_id(5位)  npc_id(6位)
if len(sys.argv) < 3:
    print("用法：python proc.py 5位SpaceID 6位NpcID")
    print("示例：python proc.py 15011 150101")
    sys.exit(1)

space_id = sys.argv[1]
npc_id = sys.argv[2]

# 严格校验
if not (space_id.isdigit() and len(space_id) == 5):
    raise ValueError(f"SpaceID必须是5位数字，收到：{space_id}")
if not (npc_id.isdigit() and len(npc_id) == 6):
    raise ValueError(f"NpcID必须是6位数字，收到：{npc_id}")

print(f"✅使用 space_id={space_id}, npc_id={npc_id}")
print(f"✅前后扩展时长设置为：{EXTEND_SEC} 秒")
print(f"✅输出文件将保存至目录：{OUTPUT_DIR.resolve()}")
# ================工具函数 ffprobe读取视频元信息================
def get_video_meta(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        str(video_path)
    ]
    out = subprocess.check_output(cmd, encoding="utf8")
    meta = json.loads(out)
    video_stream = [s for s in meta["streams"] if s["codec_type"] == "video"][0]
    audio_streams = [s for s in meta["streams"] if s["codec_type"] == "audio"]

    width = int(video_stream["width"])
    height = int(video_stream["height"])
    fps_frac = video_stream["avg_frame_rate"].split("/")
    fps_num = int(fps_frac[0])
    fps_den = int(fps_frac[1])
    fps = fps_num / fps_den
    duration = float(video_stream["duration"])
    total_frames = int(video_stream["nb_frames"])
    has_audio = len(audio_streams) > 0

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "fps_num": fps_num,
        "fps_den": fps_den,
        "duration": duration,
        "frames": total_frames,
        "has_audio": has_audio
    }


def extract_first_frame(vid_path, out_img):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(vid_path),
        "-vf", "select=eq(n\\,0)",
        "-frames:v", "1",
        str(out_img)
    ]
    subprocess.run(cmd, capture_output=True)


def extract_last_frame(vid_path, out_img):
    cmd = [
        "ffmpeg", "-y",
        "-sseof", "-1",
        "-i", str(vid_path),
        "-vf", "select=eq(n\\,0)",
        "-frames:v", "1",
        str(out_img)
    ]
    subprocess.run(cmd, capture_output=True)


def image_to_duration_video(img_path, out_clip, width, height, fps_num, fps_den, duration_sec):
    """生成指定时长的静帧视频，附带stereo 48000静音aac音轨"""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(img_path),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", str(duration_sec),
        "-vf", f"scale={width}:{height}",
        "-r", f"{fps_num}/{fps_den}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v",
        "-map", "1:a",
        str(out_clip)
    ]
    ret = subprocess.run(cmd, capture_output=True)
    if ret.returncode != 0:
        print(f"⚠️生成静帧片段失败 {out_clip}")
        print(ret.stderr.decode("utf‑8", errors="replace"))


def check_all_integer(output_json):
    """校验json所有PTS/帧数字段为int，防止小数点"""
    assert isinstance(output_json["Timebase"], int)
    assert isinstance(output_json["TotalDurationPTS"], int)
    for seg in output_json["Segments"]:
        assert isinstance(seg["Timebase"], int)
        assert isinstance(seg["StartPTS"], int)
        assert isinstance(seg["EndPTS"], int)
        assert isinstance(seg["FrameCount"], int)
    print("✅校验通过：所有PTS、FrameCount均为整数，无小数点")


# ================主逻辑================
def main():
    segments = []
    concat_file_list = []

    base_meta = get_video_meta(Path(INPUT_VIDEO_PATHS[0]))
    base_w = base_meta["width"]
    base_h = base_meta["height"]
    base_fps_num = base_meta["fps_num"]
    base_fps_den = base_meta["fps_den"]
    base_fps = base_meta["fps"]

    TIMEBASE = base_fps_num * 512
    current_start_pts = 0
    # 根据配置秒数计算扩展片段帧数（取整，必须整数帧）
    extend_frames = base_fps * EXTEND_SEC
    extend_frames = int(extend_frames)
    
    print(f"扩展片段帧数：{extend_frames} 帧")    
    print(f"基准参数：width={base_w}, height={base_h}, fps={base_fps_num}/{base_fps_den}")
    print(f"计算得到 Timebase = {base_fps_num} *512 = {TIMEBASE}")

    # 校验全部输入视频分辨率、帧率一致
    for vid_path in INPUT_VIDEO_PATHS:
        m = get_video_meta(Path(vid_path))
        if m["width"] != base_w or m["height"] != base_h:
            raise Exception(f"视频 {vid_path} 分辨率与基准不一致！要求四段视频分辨率相同")
        if abs(m["fps"] - base_fps) > 1e-6:
            raise Exception(f"视频 {vid_path} 帧率与基准不一致！要求四段视频帧率相同")

    vid_name = ['idle', 'special_idle_01', 'special_idle_02', 'idle_married']
    for idx, vid_path in enumerate(INPUT_VIDEO_PATHS):
        vid_path = Path(vid_path)
        meta = get_video_meta(vid_path)
        print(f"\n处理视频 {vid_path.name} |原始帧数:{meta['frames']} |源视频是否有音频:{meta['has_audio']}")

        first_img = TMP_DIR / f"{idx}_first.jpg"
        last_img = TMP_DIR / f"{idx}_last.jpg"
        extract_first_frame(vid_path, first_img)
        extract_last_frame(vid_path, last_img)

        clip_first = TMP_DIR / f"{idx}_clip_first.mp4"
        clip_last = TMP_DIR / f"{idx}_clip_last.mp4"
        # 生成前后静帧片段
        image_to_duration_video(first_img, clip_first, base_w, base_h, base_fps_num, base_fps_den, EXTEND_SEC)
        image_to_duration_video(last_img, clip_last, base_w, base_h, base_fps_num, base_fps_den, EXTEND_SEC)
        # 拼接顺序：首帧1s ->原视频 ->尾帧1s
        concat_file_list.append(str(clip_first.resolve()))
        concat_file_list.append(str(vid_path.resolve()))
        concat_file_list.append(str(clip_last.resolve()))

        framecnt_orig = meta["frames"]
        dur_orig_pts = framecnt_orig / base_fps * TIMEBASE
        current_start_pts = current_start_pts + EXTEND_SEC * TIMEBASE
        seg = {
            "VPath": f"spaces/{space_id}/npc_{npc_id}:{vid_name[idx]}",
            "SourceIdentifier": f"spaces/{space_id}/npc_{npc_id}:{vid_name[idx]}",
            "FrameCount": int(framecnt_orig  + 2 * base_fps),
            "Timebase": TIMEBASE,
            "StartPTS": current_start_pts,
            "EndPTS": int(current_start_pts + dur_orig_pts)
        }
        segments.append(seg)
        current_start_pts = seg["EndPTS"] + EXTEND_SEC * TIMEBASE
        
    # ----------------filter_complex concat 拼接视频音频----------------
    ffmpeg_args = ["ffmpeg", "-y"]
    for file_path in concat_file_list:
        ffmpeg_args.extend(["-i", str(file_path)])

    n_seg = len(concat_file_list)
    filter_parts = []
    for i in range(n_seg):
        filter_parts.append(f"[{i}:v][{i}:a]")
    filter_str = "".join(filter_parts) + f"concat=n={n_seg}:v=1:a=1[vout][aout]"

    ffmpeg_args.extend([
        "-filter_complex", filter_str,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        OUT_VIDEO_NAME
    ])

    print("\n开始ffmpeg filter_complex拼接输出 b1.mp4 ...")
    ret = subprocess.run(ffmpeg_args, capture_output=True)
    if ret.returncode != 0:
        print("❌ffmpeg拼接错误 stderr:")
        print(ret.stderr.decode("utf‑8", errors="replace"))
        raise RuntimeError("ffmpeg拼接失败")

    # ----------------输出segments json----------------
    output_json = {
        "Version": "v12",
        "EncodingProfile": "p3",
        "Timebase": TIMEBASE,
        "Parameters": {
            "Width": base_w,
            "Height": base_h,
            "FrameRate": f"{base_fps_num}/{base_fps_den}",
            "CodecName": "h264",
            "TimeBase": f"1/{TIMEBASE}"
        },
        "Segments": segments,
        "TotalDurationPTS": current_start_pts
    }

    # check_all_integer(output_json)

    out_file = Path(OUT_JSON_NAME)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"\n输出视频：{Path(OUT_VIDEO_NAME).resolve()}")
    print(f"输出json：{out_file.resolve()}")
    print(f"Timebase={TIMEBASE}，总PTS时长 {current_start_pts}，总秒数 {current_start_pts / TIMEBASE:.3f}s")

    print("\n=====校验各段PTS与帧数匹配=====")
    for seg in segments:
        delta = seg["EndPTS"] - seg["StartPTS"]
        ok = delta == seg["FrameCount"] * 512
        print(f"{seg['VPath']} |FrameCount={seg['FrameCount']} |pts_delta={delta} |match:{ok}")


if __name__ == "__main__":
    main()
