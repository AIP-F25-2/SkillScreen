import { useCallback, useEffect, useRef, useState } from "react";

interface UseFileUploadProps {
  onUpload?: (file: File, url: string) => void;
  allowedTypes?: string[]; // MIME types
  maxSizeMb?: number;
}

const DEFAULT_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/zip",
  "application/x-zip-compressed",
];

export function useFileUpload({ onUpload, allowedTypes = DEFAULT_TYPES, maxSizeMb = 25 }: UseFileUploadProps = {}) {
  const previewRef = useRef<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const openPicker = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const validate = (file: File): string | null => {
    if (!allowedTypes.includes(file.type)) {
      return "Unsupported file type. Allowed: PDF, DOC, DOCX, ZIP";
    }
    if (file.size > maxSizeMb * 1024 * 1024) {
      return `File too large. Max ${maxSizeMb}MB`;
    }
    return null;
  };

  const onChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      const validationError = validate(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      setFileName(file.name);
      setFileSize(file.size);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      previewRef.current = url;
      onUpload?.(file, url);
    },
    [onUpload],
  );

  const remove = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setFileName(null);
    setFileSize(null);
    previewRef.current = null;
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [previewUrl]);

  useEffect(() => {
    return () => {
      if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    };
  }, []);

  return {
    previewUrl,
    fileName,
    fileSize,
    error,
    fileInputRef,
    openPicker,
    onChange,
    remove,
    allowedTypes,
  };
}


