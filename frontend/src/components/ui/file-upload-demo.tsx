'use client';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Upload, FileText, Trash2, CheckCircle, Loader2, X, AlertCircle, Mail } from "lucide-react";
import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api";
import { getDemoJobDescription } from "@/lib/demoHelpers";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface ProcessedFile {
  filename: string;
  url: string;
  size: number;
  status: 'processed' | 'failed' | 'duplicate_email';
  extracted_emails: string[];
  extracted_name: string | null;
  email_count: number;
  id?: string;
  error?: string;
  candidate_save_error?: string;
  emailSent?: boolean;
  emailError?: string;
}

const MAX_FILES = 10;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_ZIP_SIZE = 50 * 1024 * 1024; // 50MB
const SUPPORTED_TYPES = ['.pdf', '.doc', '.docx', '.zip'];

// Cryptographically secure random string generator
// Uses Web Crypto API for secure random number generation
const generateSecureRandomString = (length: number = 9): string => {
  if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues) {
    const array = new Uint8Array(length * 2); // Generate extra to ensure we have enough after filtering
    window.crypto.getRandomValues(array);
    // Convert to base36 and filter out non-alphanumeric, then take the required length
    return Array.from(array, byte => byte.toString(36))
      .join('')
      .replace(/[^a-z0-9]/g, '')
      .substring(0, length)
      .padStart(length, '0'); // Pad if we don't have enough characters
  }
  // Fallback (shouldn't happen in browser, but TypeScript requires it)
  throw new Error('Cryptographically secure random number generator not available');
};

export function FileUploadDemo() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processSuccess, setProcessSuccess] = useState(false);
  const [selectedJob, setSelectedJob] = useState<string>("");
  const [jobOptions] = useState<string[]>([
    'Senior Software Engineer',
    'Product Manager',
    'UX Designer'
  ]);
  const [processedFiles, setProcessedFiles] = useState<ProcessedFile[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const validateFile = (file: File): string | null => {
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!SUPPORTED_TYPES.includes(fileExt)) {
      return `File type ${fileExt} not supported. Supported: PDF, DOC, DOCX, ZIP`;
    }

    const isZip = fileExt === '.zip';
    const maxSize = isZip ? MAX_ZIP_SIZE : MAX_FILE_SIZE;
    
    if (file.size > maxSize) {
      const maxSizeMB = Math.round(maxSize / (1024 * 1024));
      return `File size exceeds ${maxSizeMB}MB limit`;
    }

    return null;
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    const fileArray = Array.from(files);
    const totalFiles = selectedFiles.length + fileArray.length;

    if (totalFiles > MAX_FILES) {
      setUploadError(`Maximum ${MAX_FILES} files allowed. You selected ${fileArray.length} additional files.`);
      return;
    }

    const validFiles: File[] = [];
    const errors: string[] = [];

    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        errors.push(`${file.name}: ${error}`);
      } else {
        validFiles.push(file);
      }
    });

    if (errors.length > 0) {
      setUploadError(errors.join('\n'));
    } else {
      setUploadError(null);
      setSelectedFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
    setUploadError(null);
  };

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

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  }, [selectedFiles]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadError(null);
    
    try {
      console.log(`Uploading ${selectedFiles.length} file(s) to interview-service...`);
      const parseResponse = await apiClient.uploadResumeForParsing(selectedFiles);
      console.log("Interview-service parse response:", parseResponse);
      
      if (!parseResponse.success) {
        throw new Error("Failed to parse resumes");
      }

      const files = parseResponse.data?.files || [];
      console.log(`Raw files data:`, files);
      
      setProcessedFiles(files);
      
      console.log(`Successfully processed ${files.length} file(s)`);

      // Send invitation emails to successfully processed candidates
      // Note: We send emails even if database save failed (id might be missing)
      const processedCandidates = files.filter(
        (f: ProcessedFile) => f.status === 'processed' && 
        f.extracted_emails && 
        f.extracted_emails.length > 0 && 
        f.extracted_name
      );

      console.log(`Candidates eligible for email (${processedCandidates.length}):`, processedCandidates.map((c: ProcessedFile) => ({
        name: c.extracted_name,
        email: c.extracted_emails?.[0],
        id: c.id,
        status: c.status
      })));
      
      const emailResults: Array<{ candidate: ProcessedFile; success: boolean; error?: string }> = [];

      // Add a small delay to ensure database operations complete
      if (processedCandidates.length > 0) {
        console.log(`⏳ Waiting for database operations to complete...`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      for (const candidate of processedCandidates) {
        try {
          // Use database ID if available, otherwise generate a temporary one using cryptographically secure random
          const candidateId = candidate.id || `temp_${Date.now()}_${generateSecureRandomString(9)}`;
          
          // Generate unique session_id for the interview using cryptographically secure random
          const sessionId = `session_${Date.now()}_${generateSecureRandomString(9)}_${candidateId}`;
          
          console.log(`📧 Sending invitation email to ${candidate.extracted_emails[0]} for candidate ${candidateId}...`);
        
          const emailResponse = await apiClient.sendInterviewInvitation({
            candidate_email: candidate.extracted_emails[0],
            candidate_name: candidate.extracted_name || 'Candidate',
          candidate_id: candidateId,
            session_id: sessionId,
            recruiter_name: "Hiring Team",
            company_name: "SkillScreen",
            expires_in_hours: 48
          });
          
          if (emailResponse.success || emailResponse.data) {
            console.log(`Email sent successfully to ${candidate.extracted_emails[0]}`);
            emailResults.push({ candidate, success: true });
          } else {
            console.warn(`Failed to send email to ${candidate.extracted_emails[0]}`);
            emailResults.push({ 
              candidate, 
              success: false, 
              error: 'Email sending failed' 
            });
          }
        } catch (emailError: any) {
          console.error(`Error sending email to ${candidate.extracted_emails[0]}:`, emailError);
          emailResults.push({ 
            candidate, 
            success: false, 
            error: emailError.message || 'Email sending failed' 
          });
        }
      }
      
      // Update processed files with email status
      const updatedFiles = files.map((file: ProcessedFile) => {
        const emailResult = emailResults.find(r => r.candidate.id === file.id);
        if (emailResult) {
          return {
            ...file,
            emailSent: emailResult.success,
            emailError: emailResult.error
          };
        }
        return file;
      });
      
      setProcessedFiles(updatedFiles);
        setUploadSuccess(true);
      
      const successCount = emailResults.filter(r => r.success).length;
      const failCount = emailResults.filter(r => !r.success).length;
      
      console.log(`Email sending complete: ${successCount} sent, ${failCount} failed`);
      
      if (successCount > 0 && failCount === 0) {
        console.log(`✅ All invitation emails sent successfully!`);
      } else if (successCount > 0) {
        console.warn(`⚠️ ${successCount} emails sent, ${failCount} failed`);
      }
      
    } catch (error: any) {
      console.error("Upload error:", error);
      setUploadError(error.message || "Upload failed. Please try again.");
      setUploadSuccess(false);
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcess = async () => {
    if (processedFiles.length === 0) return;

    setIsProcessing(true);
    try {
      // Process each successfully parsed file
      const processedCount = processedFiles.filter(f => f.status === 'processed' && f.extracted_emails?.length > 0).length;
      
      if (processedCount === 0) {
        alert("No valid candidates found in uploaded files. Please check the extracted data.");
        return;
      }

      // For now, just show success message
      // In the future, this could schedule interviews for each candidate
      alert(`Successfully processed ${processedCount} candidate(s) from uploaded resumes.`);
      
      setProcessSuccess(true);
      
      // Reset after delay
      setTimeout(() => {
        setSelectedFiles([]);
        setProcessedFiles([]);
        setUploadSuccess(false);
        setProcessSuccess(false);
        setUploadError(null);
      }, 2000);
    } catch (error) {
      console.error("Process error:", error);
      alert("Failed to process candidates. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const resetForm = () => {
    setSelectedFiles([]);
    setProcessedFiles([]);
    setUploadSuccess(false);
    setProcessSuccess(false);
    setUploadError(null);
  };

  return (
    <div className="w-full rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-4 space-y-1">
        <h3 className="text-lg font-medium text-white">Upload Candidate Resume(s)</h3>
        <p className="text-sm text-white/70">
          Upload PDF, DOC, DOCX, or ZIP files (max {MAX_FILES} files, {MAX_FILE_SIZE / (1024 * 1024)}MB per file, {MAX_ZIP_SIZE / (1024 * 1024)}MB for ZIP)
        </p>
      </div>

      {/* Job Selection */}
        <div className="mb-4">
        <label className="text-sm text-white/80 mb-2 block">Job Listing (optional)</label>
        <Select onValueChange={setSelectedJob}>
          <SelectTrigger className="w-full bg-white/5 border-white/10 text-white">
            <SelectValue placeholder="Select job from Active Listings" />
          </SelectTrigger>
          <SelectContent>
            {jobOptions.map((opt) => (
              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        </div>

      {/* File Input */}
      <Input
        type="file"
        accept=".pdf,.doc,.docx,.zip"
        multiple
        className="hidden"
        id="file-upload-input"
        onChange={(e) => handleFileSelect(e.target.files)}
      />

      {/* Upload Area */}
      {selectedFiles.length === 0 ? (
        <div
          onClick={() => document.getElementById('file-upload-input')?.click()}
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
            <p className="text-sm font-medium text-white">Click to select files</p>
            <p className="text-xs text-white/60">or drag and drop resumes here</p>
            <p className="text-xs text-white/50 mt-1">Supports: PDF, DOC, DOCX, ZIP (up to {MAX_FILES} files)</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Selected Files List */}
          <div className="space-y-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-4 rounded-lg border border-white/10 bg-white/5 p-4"
              >
            <div className="rounded-md bg-white/10 p-2">
              <FileText className="h-6 w-6 text-white" />
            </div>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium truncate">{file.name}</div>
                  <div className="text-xs text-white/60">{formatFileSize(file.size)}</div>
                  {file.name.toLowerCase().endsWith('.zip') && (
                    <div className="text-xs text-blue-400 mt-1">ZIP archive - will extract and process all resumes</div>
              )}
            </div>
            {!uploadSuccess && (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => removeFile(index)}
                    className="flex-shrink-0"
                  >
                    <X className="h-4 w-4" />
                </Button>
                )}
              </div>
            ))}
          </div>

          {/* Upload Button */}
          {!uploadSuccess && (
            <div className="flex items-center justify-between">
              <div className="text-xs text-white/60">
                {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
                {selectedFiles.length >= MAX_FILES && (
                  <span className="text-yellow-400 ml-2">(Maximum reached)</span>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => document.getElementById('file-upload-input')?.click()}
                  variant="outline"
                  size="sm"
                  disabled={selectedFiles.length >= MAX_FILES}
                  className="border-white/20 text-white hover:bg-white/10"
                >
                  Add More
                </Button>
            <Button 
              onClick={handleUpload} 
                  disabled={isUploading || selectedFiles.length === 0}
                  className="bg-blue-600 hover:bg-blue-700"
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                      Upload & Parse {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
                </>
              )}
            </Button>
              </div>
            </div>
          )}

          {/* Error Display */}
          {uploadError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-400 font-medium">Upload Error</p>
                <pre className="text-xs text-red-300 mt-1 whitespace-pre-wrap">{uploadError}</pre>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setUploadError(null)}
                className="text-red-400 hover:text-red-300"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Processed Files Results */}
          {uploadSuccess && processedFiles.length > 0 && (
            <div className="space-y-4 bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-white">📋 Parsed Resume Results</h4>
                <span className="text-xs text-white/50">
                  {processedFiles.filter(f => f.status === 'processed').length} of {processedFiles.length} processed
                </span>
              </div>
              
              {/* Email Summary */}
              {processedFiles.some(f => f.emailSent !== undefined) && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Mail className="h-4 w-4 text-blue-400" />
                    <span className="text-sm font-semibold text-white">Email Invitations</span>
                  </div>
                  <div className="text-xs text-white/70 space-y-1">
                <div>
                      ✅ Sent: {processedFiles.filter(f => f.emailSent === true).length}
                    </div>
                    {processedFiles.filter(f => f.emailSent === false).length > 0 && (
                      <div className="text-red-400">
                        ❌ Failed: {processedFiles.filter(f => f.emailSent === false).length}
                      </div>
                    )}
                </div>
                </div>
              )}

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {processedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      file.status === 'processed'
                        ? 'bg-green-500/10 border-green-500/30'
                        : file.status === 'duplicate_email'
                        ? 'bg-yellow-500/10 border-yellow-500/30'
                        : 'bg-red-500/10 border-red-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <div className="text-white text-sm font-medium truncate">{file.filename}</div>
                        <div className="text-xs text-white/60 mt-1">{formatFileSize(file.size)}</div>
                </div>
                      <div className="flex items-center gap-2">
                        {file.status === 'processed' && (
                          <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                        )}
                        {file.status === 'failed' && (
                          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                        )}
                        {file.status === 'duplicate_email' && (
                          <AlertCircle className="h-5 w-5 text-yellow-400 flex-shrink-0" />
                        )}
                </div>
              </div>
              
                    {file.status === 'processed' && (
                      <div className="space-y-2 mt-3 pt-3 border-t border-white/10">
                        {file.extracted_name && (
                          <div>
                            <span className="text-xs text-white/70">Name:</span>
                            <span className="text-xs text-white ml-2">{file.extracted_name}</span>
                          </div>
                        )}
                        {file.extracted_emails && file.extracted_emails.length > 0 && (
              <div>
                            <span className="text-xs text-white/70">Email{file.extracted_emails.length > 1 ? 's' : ''}:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {file.extracted_emails.map((email, emailIndex) => (
                      <span
                                  key={emailIndex}
                                  className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded border border-blue-500/30"
                      >
                                  {email}
                      </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {file.id && (
                          <div>
                            <span className="text-xs text-white/70">Candidate ID:</span>
                            <span className="text-xs text-white ml-2 font-mono">{file.id}</span>
                          </div>
                        )}
                        {file.emailSent !== undefined && (
                          <div className="mt-2">
                            {file.emailSent ? (
                              <div className="flex items-center gap-2 text-xs text-green-400">
                                <CheckCircle className="h-4 w-4" />
                                <span>Invitation email sent successfully</span>
                              </div>
                            ) : (
                              <div className="flex items-start gap-2 text-xs text-red-400">
                                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                <div>
                                  <span>Failed to send invitation email</span>
                                  {file.emailError && (
                                    <div className="text-xs text-red-300 mt-1">{file.emailError}</div>
                                  )}
                                </div>
                              </div>
                  )}
                </div>
                        )}
              </div>
                    )}

                    {file.status === 'failed' && file.error && (
                      <div className="mt-2 pt-2 border-t border-red-500/20">
                        <p className="text-xs text-red-300">{file.error}</p>
            </div>
          )}

                    {file.status === 'duplicate_email' && (
                      <div className="mt-2 pt-2 border-t border-yellow-500/20">
                        <p className="text-xs text-yellow-300">
                          Candidate with this email already exists in database
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {/* Process Button */}
              {!processSuccess && (
                <div className="flex gap-3 pt-4 border-t border-white/10">
              <Button 
                onClick={handleProcess} 
                    disabled={isProcessing || processedFiles.filter(f => f.status === 'processed').length === 0}
                  className="flex-1 bg-green-600 hover:bg-green-700"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                        Process Candidates
                  </>
                )}
              </Button>
                <Button 
                    onClick={resetForm}
                  variant="outline"
                    className="border-white/20 text-white hover:bg-white/10"
                >
                  Upload More
                </Button>
            </div>
          )}

          {/* Success Message */}
          {processSuccess && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
              <CheckCircle className="h-8 w-8 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-green-300 font-medium">Candidates Processed Successfully!</p>
              <p className="text-xs text-white/60 mt-1">Resetting form...</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
