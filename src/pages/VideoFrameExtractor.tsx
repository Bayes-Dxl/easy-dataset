/**
 * VideoFrameExtractor.tsx
 * 视频抽帧页：导入视频文件，按帧间隔抽取图片帧，输出到指定目录作为预标注数据集。
 */
import { useState } from "react";
import { Film, FolderOpen, RefreshCw, Info } from "lucide-react";
import { browseFile, browseDirectory, api } from "@/lib/tauri-bridge";
import { ResultBox } from "@/components/ResultBox";
import { createPortal } from "react-dom";
import { useSidebarEl } from "@/lib/sidebar-context";

interface VideoInfo {
  fps: number;
  total_frames: number;
  width: number;
  height: number;
  duration: number;
}

function DirInput({
  label, value, onChange, onBrowse,
}: {
  label: string; value: string; onChange: (v: string) => void; onBrowse: () => void;
}) {
  return (
    <div>
      <label className="block text-[10px] font-semibold uppercase tracking-[0.1em] mb-1.5"
        style={{ color: "hsl(var(--muted-foreground))" }}>{label}</label>
      <div className="flex gap-1.5">
        <input
          className="flex-1 px-3 py-2 rounded-md text-sm min-w-0"
          style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={`请输入${label}路径`}
        />
        <button
          className="px-2.5 py-2 rounded-md flex-shrink-0 flex items-center"
          style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))" }}
          onClick={onBrowse}
        >
          <FolderOpen className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default function VideoFrameExtractor() {
  const [videoPath, setVideoPath] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [intervalFrames, setIntervalFrames] = useState(30);
  const [format, setFormat] = useState<"jpg" | "png">("jpg");
  const [quality, setQuality] = useState(95);
  const [prefix, setPrefix] = useState("frame");

  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoError, setInfoError] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string; saved_count?: number } | null>(null);

  const sidebarEl = useSidebarEl();

  const handleLoadInfo = async () => {
    if (!videoPath) return;
    setInfoLoading(true);
    setInfoError(null);
    setVideoInfo(null);
    try {
      const res = await api.videoInfo({ video_path: videoPath }) as { success: boolean; message?: string } & VideoInfo;
      if (!res.success) { setInfoError(res.message || "读取失败"); return; }
      setVideoInfo(res);
    } catch (e) {
      setInfoError(String(e));
    } finally {
      setInfoLoading(false);
    }
  };

  const handleExtract = async () => {
    if (!videoPath || !outputDir) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await api.videoExtractFrames({
        video_path: videoPath,
        output_dir: outputDir,
        interval_frames: intervalFrames,
        format,
        quality,
        prefix,
      }) as { success: boolean; message: string; saved_count?: number };
      setResult(res);
      if (res.success) setVideoInfo(null); // 抽帧完成后清除信息面板，由结果接管
    } catch (e) {
      setResult({ success: false, message: String(e) });
    } finally {
      setLoading(false);
    }
  };

  // 预估抽帧数量
  const estimatedCount = videoInfo
    ? Math.ceil(videoInfo.total_frames / Math.max(1, intervalFrames))
    : null;

  const configPortal = (
    <div className="py-4 flex flex-col gap-4">
      {/* 视频文件 */}
      <div>
        <label className="block text-[10px] font-semibold uppercase tracking-[0.1em] mb-1.5"
          style={{ color: "hsl(var(--muted-foreground))" }}>视频文件</label>
        <div className="flex gap-1.5">
          <input
            className="flex-1 px-3 py-2 rounded-md text-sm min-w-0"
            style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
            value={videoPath}
            onChange={(e) => { setVideoPath(e.target.value); setVideoInfo(null); }}
            placeholder="mp4 / avi / mov / mkv / dav …"
          />
          <button
            className="px-2.5 py-2 rounded-md flex-shrink-0 flex items-center"
            style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))" }}
            onClick={async () => {
              const f = await browseFile([
                { name: "视频文件", extensions: ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v", "dav"] },
              ]);
              if (f) { setVideoPath(f); setVideoInfo(null); }
            }}
          >
            <FolderOpen className="w-4 h-4" />
          </button>
        </div>
        <button
          className="mt-2 w-full flex items-center justify-center gap-1.5 py-1.5 rounded text-xs font-medium disabled:opacity-40"
          style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
          disabled={!videoPath || infoLoading}
          onClick={handleLoadInfo}
        >
          {infoLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Info className="w-3 h-3" />}
          {infoLoading ? "读取中…" : "加载视频信息"}
        </button>
      </div>

      {/* 输出目录 */}
      <DirInput label="输出目录"
        value={outputDir}
        onChange={setOutputDir}
        onBrowse={async () => { const d = await browseDirectory(); if (d) setOutputDir(d); }}
      />

      {/* 抽帧间隔 */}
      <div>
        <label className="block text-[10px] font-semibold uppercase tracking-[0.1em] mb-1.5"
          style={{ color: "hsl(var(--muted-foreground))" }}>抽帧间隔（帧）</label>
        <div className="flex items-center gap-3">
          <input
            type="number"
            min={1}
            max={10000}
            className="w-24 px-3 py-2 rounded-md text-sm"
            style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
            value={intervalFrames}
            onChange={(e) => setIntervalFrames(Math.max(1, parseInt(e.target.value) || 1))}
          />
          <span className="text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
            每 {intervalFrames} 帧取一张
            {videoInfo ? `，约 ${(intervalFrames / videoInfo.fps).toFixed(2)}s 间隔` : ""}
          </span>
        </div>
      </div>

      {/* 输出格式 */}
      <div>
        <label className="block text-[10px] font-semibold uppercase tracking-[0.1em] mb-1.5"
          style={{ color: "hsl(var(--muted-foreground))" }}>输出格式</label>
        <div className="flex gap-2">
          {(["jpg", "png"] as const).map((f) => (
            <button
              key={f}
              className="flex-1 py-1.5 rounded text-sm font-medium"
              style={{
                background: format === f ? "hsl(var(--primary) / 0.12)" : "hsl(var(--muted))",
                border: `1px solid ${format === f ? "hsl(var(--primary))" : "hsl(var(--border))"}`,
                color: format === f ? "hsl(var(--primary))" : "hsl(var(--foreground))",
              }}
              onClick={() => setFormat(f)}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* JPEG 质量 */}
      {format === "jpg" && (
        <div>
          <label className="block text-[10px] font-semibold uppercase tracking-[0.1em] mb-1.5"
            style={{ color: "hsl(var(--muted-foreground))" }}>JPEG 质量 {quality}</label>
          <input
            type="range" min={50} max={100} step={1}
            value={quality}
            onChange={(e) => setQuality(parseInt(e.target.value))}
            className="w-full"
          />
        </div>
      )}

      {/* 文件名前缀 */}
      <div>
        <label className="block text-[10px] font-semibold uppercase tracking-[0.1em] mb-1.5"
          style={{ color: "hsl(var(--muted-foreground))" }}>文件名前缀</label>
        <input
          className="w-full px-3 py-2 rounded-md text-sm"
          style={{ background: "hsl(var(--muted))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
          value={prefix}
          placeholder="frame"
          onChange={(e) => setPrefix(e.target.value || "frame")}
        />
        <p className="text-[11px] mt-1" style={{ color: "hsl(var(--muted-foreground))" }}>
          输出文件名格式：{prefix}_000000.{format}
        </p>
      </div>

      {/* 开始按钮 */}
      <button
        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-semibold disabled:opacity-50"
        style={{ background: "hsl(var(--primary))", color: "#fff" }}
        onClick={handleExtract}
        disabled={loading || !videoPath || !outputDir}
      >
        {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Film className="w-4 h-4" />}
        {loading ? "抽帧中…" : "开始抽帧"}
      </button>
    </div>
  );

  return (
    <>
      {sidebarEl && createPortal(configPortal, sidebarEl)}

      <div className="space-y-4">
        {/* 视频信息卡片 */}
        {infoError && (
          <div className="px-4 py-3 rounded-md text-sm"
            style={{ background: "hsl(var(--destructive) / 0.1)", border: "1px solid hsl(var(--destructive) / 0.3)", color: "hsl(var(--destructive))" }}>
            {infoError}
          </div>
        )}

        {videoInfo && (
          <div className="rounded-md p-4 space-y-3"
            style={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Film className="w-4 h-4" style={{ color: "hsl(var(--primary))" }} />
              视频信息
            </h3>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              {[
                ["分辨率", `${videoInfo.width} × ${videoInfo.height}`],
                ["帧率", `${videoInfo.fps} fps`],
                ["总帧数", videoInfo.total_frames.toLocaleString()],
                ["时长", `${videoInfo.duration}s`],
                ["当前间隔", `每 ${intervalFrames} 帧`],
                ["预计抽出", `${estimatedCount?.toLocaleString()} 张`],
              ].map(([k, v]) => (
                <div key={k as string} className="flex justify-between">
                  <span style={{ color: "hsl(var(--muted-foreground))" }}>{k}</span>
                  <span className="font-mono font-medium">{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 结果 */}
        {result && <ResultBox success={result.success} message={result.message} />}
        {result?.success && result.saved_count !== undefined && (
          <div className="px-4 py-3 rounded-md text-sm"
            style={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}>
            <span style={{ color: "hsl(var(--muted-foreground))" }}>共输出图片：</span>
            <span className="font-semibold" style={{ color: "hsl(var(--primary))" }}>
              {result.saved_count.toLocaleString()} 张
            </span>
            <span className="ml-3 text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
              → {outputDir}
            </span>
          </div>
        )}

        {/* 空状态 */}
        {!videoInfo && !result && !infoError && (
          <div className="flex flex-col items-center justify-center py-20 gap-3"
            style={{ color: "hsl(var(--muted-foreground))" }}>
            <Film className="w-12 h-12 opacity-20" />
            <p className="text-sm">在左侧选择视频文件并配置参数，点击「开始抽帧」</p>
          </div>
        )}
      </div>
    </>
  );
}
