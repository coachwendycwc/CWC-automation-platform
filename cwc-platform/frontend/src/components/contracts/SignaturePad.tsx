"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface SignaturePadProps {
  onSignatureChange: (data: string | null, type: "drawn" | "typed") => void;
  disabled?: boolean;
}

export function SignaturePad({ onSignatureChange, disabled = false }: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);
  const [typedName, setTypedName] = useState("");
  const [signatureType, setSignatureType] = useState<"draw" | "type">("draw");

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);

    // Set drawing styles
    ctx.strokeStyle = "#1a1a1a";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // Fill with white background
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }, []);

  const getCoordinates = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();

    if ("touches" in e) {
      const touch = e.touches[0];
      return {
        x: touch.clientX - rect.left,
        y: touch.clientY - rect.top,
      };
    } else {
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    }
  }, []);

  const startDrawing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (disabled) return;

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  }, [disabled, getCoordinates]);

  const draw = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawing || disabled) return;

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasDrawn(true);
  }, [isDrawing, disabled, getCoordinates]);

  const stopDrawing = useCallback(() => {
    if (isDrawing && hasDrawn) {
      const canvas = canvasRef.current;
      if (canvas) {
        const dataUrl = canvas.toDataURL("image/png");
        onSignatureChange(dataUrl, "drawn");
      }
    }
    setIsDrawing(false);
  }, [isDrawing, hasDrawn, onSignatureChange]);

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx || !canvas) return;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
    onSignatureChange(null, "drawn");
  }, [onSignatureChange]);

  // Handle typed signature
  const handleTypedSignature = useCallback((name: string) => {
    setTypedName(name);

    if (!name.trim()) {
      onSignatureChange(null, "typed");
      return;
    }

    // Create canvas for typed signature
    const canvas = document.createElement("canvas");
    canvas.width = 400;
    canvas.height = 100;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Fill background
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw text with signature-like font
    ctx.fillStyle = "#1a1a1a";
    ctx.font = "italic 36px 'Brush Script MT', cursive";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(name, canvas.width / 2, canvas.height / 2);

    const dataUrl = canvas.toDataURL("image/png");
    onSignatureChange(dataUrl, "typed");
  }, [onSignatureChange]);

  useEffect(() => {
    if (signatureType === "type") {
      handleTypedSignature(typedName);
    }
  }, [signatureType, typedName, handleTypedSignature]);

  return (
    <div className="space-y-4">
      <Tabs value={signatureType} onValueChange={(v) => setSignatureType(v as "draw" | "type")}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="draw" disabled={disabled}>Draw Signature</TabsTrigger>
          <TabsTrigger value="type" disabled={disabled}>Type Signature</TabsTrigger>
        </TabsList>

        <TabsContent value="draw" className="space-y-2">
          <div className="text-sm text-gray-500">
            Use your mouse or finger to draw your signature below
          </div>
          <div
            className={`border rounded-lg overflow-hidden bg-white ${disabled ? 'opacity-50' : ''}`}
            style={{ touchAction: 'none' }}
          >
            <canvas
              ref={canvasRef}
              className="w-full cursor-crosshair"
              style={{ height: "150px" }}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
            />
          </div>
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={clearCanvas}
              disabled={disabled || !hasDrawn}
            >
              Clear
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="type" className="space-y-2">
          <div className="text-sm text-gray-500">
            Type your full legal name to create a signature
          </div>
          <Input
            placeholder="Enter your full name"
            value={typedName}
            onChange={(e) => handleTypedSignature(e.target.value)}
            disabled={disabled}
          />
          {typedName && (
            <div className="border rounded-lg p-4 bg-white">
              <p
                className="text-3xl text-center text-gray-800"
                style={{ fontFamily: "'Brush Script MT', cursive", fontStyle: "italic" }}
              >
                {typedName}
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
