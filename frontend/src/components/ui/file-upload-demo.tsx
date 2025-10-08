'use client';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useFileUpload } from "@/components/ui/use-file-upload";
import { Upload, FileText, Trash2 } from "lucide-react";
import { useCallback, useState } from "react";

export function FileUploadDemo() {
  const {
    previewUrl,
    fileName,
    fileSize,
    error,
    fileInputRef,
    openPicker,
    onChange,
    remove,
  } = useFileUpload({
    onUpload: (file) => console.log("Uploaded file:", file.name),
  });

  const [isDragging, setIsDragging] = useState(false);

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const onDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) {
        const fakeEvent = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        onChange(fakeEvent);
      }
    },
    [onChange]
  );

  return (
    <div className="w-full rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-4 space-y-1">
        <h3 className="text-lg font-medium text-white">Upload Candidate Document</h3>
        <p className="text-sm text-white/70">Allowed: PDF, DOC, DOCX, ZIP. Max 25MB.</p>
      </div>

      <Input
        type="file"
        accept=".pdf,.doc,.docx,.zip"
        className="hidden"
        ref={fileInputRef}
        onChange={onChange}
      />

      {!previewUrl ? (
        <div
          onClick={openPicker}
          onDragOver={onDragOver}
          onDragEnter={onDragEnter}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className={`flex h-40 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-white/15 bg-white/5 transition-colors hover:bg-white/10 ${
            isDragging ? 'border-blue-400/60 bg-blue-500/10' : ''
          }`}
        >
          <div className="rounded-full bg-black/40 p-3">
            <Upload className="h-5 w-5 text-white/80" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">Click to select</p>
            <p className="text-xs text-white/60">or drag and drop file here</p>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-4 rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="rounded-md bg-white/10 p-2">
            <FileText className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1">
            <div className="text-white text-sm font-medium">{fileName}</div>
            {fileSize !== null && (
              <div className="text-xs text-white/60">{(fileSize / (1024 * 1024)).toFixed(2)} MB</div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" onClick={openPicker}>
              Replace
            </Button>
            <Button size="sm" variant="destructive" onClick={remove}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
    </div>
  );
}


