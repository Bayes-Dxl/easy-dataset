"""
services/video_service.py
视频处理：读取视频信息 + 按帧间隔抽帧
"""
import os
import cv2


class VideoService:

    @staticmethod
    def get_info(video_path: str) -> dict:
        """读取视频基本元信息（分辨率、帧率、总帧数、时长）"""
        if not os.path.isfile(video_path):
            return {"success": False, "message": f"文件不存在: {video_path}"}
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"success": False, "message": "无法打开视频文件，请确认格式受支持（mp4/avi/mov/mkv 等）"}
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        duration = round(total_frames / fps, 2) if fps > 0 else 0
        return {
            "success": True,
            "fps": round(fps, 3),
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "duration": duration,
        }

    @staticmethod
    def extract_frames(
        video_path: str,
        output_dir: str,
        interval_frames: int = 30,
        fmt: str = "jpg",
        quality: int = 95,
        prefix: str = "frame",
    ) -> dict:
        """
        按帧间隔抽帧，将结果图片输出到 output_dir。
        interval_frames: 每隔多少帧取一帧（1 表示每帧都取）
        """
        if not os.path.isfile(video_path):
            return {"success": False, "message": f"文件不存在: {video_path}"}
        if not output_dir:
            return {"success": False, "message": "请指定输出目录"}

        interval_frames = max(1, int(interval_frames))
        ext = fmt.lower().lstrip(".")
        if ext not in ("jpg", "jpeg", "png", "bmp"):
            ext = "jpg"

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"success": False, "message": "无法打开视频文件"}

        os.makedirs(output_dir, exist_ok=True)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_idx = 0
        saved = 0
        write_params = [cv2.IMWRITE_JPEG_QUALITY, max(1, min(100, int(quality)))] if ext in ("jpg", "jpeg") else []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % interval_frames == 0:
                filename = f"{prefix}_{saved:06d}.{ext}"
                out_path = os.path.join(output_dir, filename)
                cv2.imwrite(out_path, frame, write_params)
                saved += 1
            frame_idx += 1

        cap.release()
        duration = round(total_frames / fps, 2) if fps > 0 else 0
        return {
            "success": True,
            "message": (
                f"抽帧完成：从 {total_frames} 帧（{duration}s）中"
                f"按每 {interval_frames} 帧间隔共抽取了 {saved} 张图片，已保存至 {output_dir}"
            ),
            "total_frames": total_frames,
            "saved_count": saved,
            "fps": round(fps, 3),
            "duration": duration,
            "output_dir": output_dir,
        }
