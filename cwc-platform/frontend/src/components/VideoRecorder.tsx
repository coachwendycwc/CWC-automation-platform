"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Video,
  Square,
  RotateCcw,
  Upload,
  Camera,
  Mic,
  MicOff,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

interface VideoRecorderProps {
  maxDuration?: number; // in seconds
  onUpload: (file: File) => Promise<{
    url: string;
    public_id: string;
    duration: number;
    thumbnail_url: string | null;
  }>;
  onComplete: (data: {
    video_url: string;
    video_public_id: string;
    video_duration_seconds: number;
    thumbnail_url: string | null;
  }) => void;
}

type RecordingState = "idle" | "requesting" | "ready" | "recording" | "stopped" | "uploading" | "complete" | "error";

export default function VideoRecorder({
  maxDuration = 120,
  onUpload,
  onComplete,
}: VideoRecorderProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [state, setState] = useState<RecordingState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Timer for recording duration
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (state === "recording") {
      interval = setInterval(() => {
        setDuration((prev) => {
          if (prev >= maxDuration - 1) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [state, maxDuration]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (recordedUrl) {
        URL.revokeObjectURL(recordedUrl);
      }
    };
  }, [recordedUrl]);

  const requestPermissions = useCallback(async () => {
    setState("requesting");
    setError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
        await videoRef.current.play();
      }

      setState("ready");
    } catch (err) {
      console.error("Permission error:", err);
      setError("Could not access camera or microphone. Please allow permissions and try again.");
      setState("error");
    }
  }, []);

  const startRecording = useCallback(() => {
    if (!streamRef.current) return;

    chunksRef.current = [];
    setDuration(0);

    const mediaRecorder = new MediaRecorder(streamRef.current, {
      mimeType: "video/webm;codecs=vp9,opus",
    });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      setRecordedBlob(blob);
      const url = URL.createObjectURL(blob);
      setRecordedUrl(url);

      if (videoRef.current) {
        videoRef.current.srcObject = null;
        videoRef.current.src = url;
        videoRef.current.muted = false;
      }

      setState("stopped");
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start(1000); // Collect data every second
    setState("recording");
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const restartRecording = useCallback(async () => {
    if (recordedUrl) {
      URL.revokeObjectURL(recordedUrl);
    }
    setRecordedBlob(null);
    setRecordedUrl(null);
    setDuration(0);
    await requestPermissions();
  }, [recordedUrl, requestPermissions]);

  const handleUpload = useCallback(async () => {
    if (!recordedBlob) return;

    setState("uploading");
    setUploadProgress(0);

    try {
      // Convert blob to file
      const file = new File([recordedBlob], "testimonial.webm", { type: "video/webm" });

      // Simulate progress (actual upload doesn't provide progress)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 500);

      const result = await onUpload(file);

      clearInterval(progressInterval);
      setUploadProgress(100);

      onComplete({
        video_url: result.url,
        video_public_id: result.public_id,
        video_duration_seconds: result.duration || duration,
        thumbnail_url: result.thumbnail_url,
      });

      setState("complete");
    } catch (err) {
      console.error("Upload error:", err);
      setError("Failed to upload video. Please try again.");
      setState("stopped");
    }
  }, [recordedBlob, duration, onUpload, onComplete]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-4">
      {/* Video Preview */}
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          playsInline
          controls={state === "stopped"}
        />

        {/* Overlay states */}
        {state === "idle" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 text-white">
            <Camera className="h-16 w-16 mb-4 opacity-50" />
            <p className="text-lg mb-4">Ready to record your testimonial?</p>
            <Button onClick={requestPermissions} size="lg">
              <Video className="h-5 w-5 mr-2" />
              Start Camera
            </Button>
          </div>
        )}

        {state === "requesting" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 text-white">
            <div className="animate-pulse">
              <Camera className="h-16 w-16 mb-4" />
            </div>
            <p className="text-lg">Requesting camera access...</p>
          </div>
        )}

        {state === "error" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 text-white">
            <AlertCircle className="h-16 w-16 mb-4 text-red-400" />
            <p className="text-lg text-center max-w-sm">{error}</p>
            <Button onClick={requestPermissions} className="mt-4">
              Try Again
            </Button>
          </div>
        )}

        {state === "recording" && (
          <div className="absolute top-4 left-4 flex items-center gap-2 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
            Recording {formatTime(duration)} / {formatTime(maxDuration)}
          </div>
        )}

        {state === "uploading" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 text-white">
            <Upload className="h-16 w-16 mb-4 animate-bounce" />
            <p className="text-lg mb-4">Uploading video...</p>
            <div className="w-48">
              <Progress value={uploadProgress} className="h-2" />
            </div>
          </div>
        )}

        {state === "complete" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-green-900/80 text-white">
            <CheckCircle className="h-16 w-16 mb-4 text-green-400" />
            <p className="text-lg">Upload complete!</p>
          </div>
        )}
      </div>

      {/* Recording progress bar */}
      {state === "recording" && (
        <Progress value={(duration / maxDuration) * 100} className="h-1" />
      )}

      {/* Controls */}
      <div className="flex justify-center gap-3">
        {state === "ready" && (
          <Button onClick={startRecording} size="lg" className="bg-red-600 hover:bg-red-700">
            <Video className="h-5 w-5 mr-2" />
            Start Recording
          </Button>
        )}

        {state === "recording" && (
          <Button onClick={stopRecording} size="lg" variant="destructive">
            <Square className="h-5 w-5 mr-2" />
            Stop Recording
          </Button>
        )}

        {state === "stopped" && (
          <>
            <Button onClick={restartRecording} variant="outline" size="lg">
              <RotateCcw className="h-5 w-5 mr-2" />
              Record Again
            </Button>
            <Button onClick={handleUpload} size="lg">
              <Upload className="h-5 w-5 mr-2" />
              Use This Video
            </Button>
          </>
        )}
      </div>

      {/* Tips */}
      {(state === "idle" || state === "ready") && (
        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
          <h4 className="font-medium mb-2">Tips for a great testimonial:</h4>
          <ul className="space-y-1">
            <li>Find a quiet place with good lighting</li>
            <li>Look directly at the camera</li>
            <li>Speak clearly and naturally</li>
            <li>Keep it under 2 minutes</li>
          </ul>
        </div>
      )}
    </div>
  );
}
