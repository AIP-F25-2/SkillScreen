'use client';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Upload, FileText, Trash2, CheckCircle, Loader2, X, AlertCircle, Mail, Edit2, Save, Video, Mic, MessageCircle } from "lucide-react";
import { useState, useCallback, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { getDemoJobDescription } from "@/lib/demoHelpers";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface JobPosition {
  id: string;
  title: string;
  department?: string;
  is_active?: boolean;
}

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
  // Editable fields
  editedName?: string;
  editedEmail?: string;
  selectedJobPositionId?: string;
  selectedMode?: 'audio' | 'video' | 'chat';
  isEditing?: boolean;
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
  const [processedFiles, setProcessedFiles] = useState<ProcessedFile[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [jobPositions, setJobPositions] = useState<JobPosition[]>([]);
  const [loadingJobPositions, setLoadingJobPositions] = useState(false);

  // Default organization ID - in production this should come from auth context
  const DEFAULT_ORGANIZATION_ID = "ecf369b2-caae-4962-85a8-404db7ab0d7e";

  // Fetch job positions on mount for the current organization
  useEffect(() => {
    const fetchJobPositions = async () => {
      setLoadingJobPositions(true);
      try {
        const response = await apiClient.getJobPositions(DEFAULT_ORGANIZATION_ID);
        console.log('Job positions response:', response);
        if (response.success && response.data?.job_positions) {
          setJobPositions(response.data.job_positions.filter((jp: JobPosition) => jp.is_active !== false));
        }
      } catch (error) {
        console.error('Failed to fetch job positions:', error);
      } finally {
        setLoadingJobPositions(false);
      }
    };
    fetchJobPositions();
  }, []);

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
      
      // Initialize editable fields with extracted values
      const filesWithEditableFields = files.map((file: ProcessedFile) => ({
        ...file,
        editedName: file.extracted_name || '',
        editedEmail: file.extracted_emails?.[0] || '',
        selectedJobPositionId: '',
        isEditing: false,
      }));
      
      setProcessedFiles(filesWithEditableFields);
      setUploadSuccess(true);
      
      console.log(`Successfully processed ${files.length} file(s). Ready for review before sending invitations.`);
        
    } catch (error: any) {
      console.error("Upload error:", error);
      setUploadError(error.message || "Upload failed. Please try again.");
      setUploadSuccess(false);
    } finally {
      setIsUploading(false);
    }
  };

  const toggleEditMode = (index: number) => {
    setProcessedFiles((prev) => 
      prev.map((file, i) => 
        i === index ? { ...file, isEditing: !file.isEditing } : file
      )
    );
  };

  const updateCandidateField = (index: number, field: 'editedName' | 'editedEmail' | 'selectedJobPositionId' | 'selectedMode', value: string) => {
    setProcessedFiles((prev) => 
      prev.map((file, i) => 
        i === index ? { ...file, [field]: value } : file
      )
    );
  };

  const handleProcess = async () => {
    if (processedFiles.length === 0) return;

    setIsProcessing(true);
    try {
      // Filter candidates that are ready to process
      const processedCandidates = processedFiles.filter(
        (f: ProcessedFile) => f.status === 'processed' && 
        (f.editedEmail || (f.extracted_emails && f.extracted_emails.length > 0)) && 
        (f.editedName || f.extracted_name)
      );
      
      if (processedCandidates.length === 0) {
        alert("No valid candidates found. Please ensure each candidate has a name and email.");
        setIsProcessing(false);
        return;
      }

      // Check if all candidates have a job position selected
      const candidatesWithoutPosition = processedCandidates.filter(c => !c.selectedJobPositionId);
      if (candidatesWithoutPosition.length > 0) {
        const proceed = window.confirm(
          `${candidatesWithoutPosition.length} candidate(s) don't have a job position selected. Continue anyway?`
        );
        if (!proceed) {
          setIsProcessing(false);
          return;
        }
      }

      console.log(`Processing ${processedCandidates.length} candidate(s) and sending invitations...`);
      
      const emailResults: Array<{ candidate: ProcessedFile; success: boolean; error?: string }> = [];
      
      // Add a small delay to ensure database operations complete
      await new Promise(resolve => setTimeout(resolve, 500));
      
      for (const candidate of processedCandidates) {
        try {
          // Use edited values if available, otherwise fall back to extracted
          const candidateName = candidate.editedName || candidate.extracted_name || 'Candidate';
          const candidateEmail = candidate.editedEmail || candidate.extracted_emails?.[0];
          
          if (!candidateEmail) {
            console.warn(`Skipping candidate ${candidateName} - no email address`);
            emailResults.push({ 
              candidate, 
              success: false, 
              error: 'No email address provided' 
            });
            continue;
          }
          
          // Use database ID if available, otherwise generate a temporary one
          const candidateId = candidate.id || `temp_${Date.now()}_${generateSecureRandomString(9)}`;
          
          // Generate unique session_id for the interview
          const sessionId = `session_${Date.now()}_${generateSecureRandomString(9)}_${candidateId}`;
          
          console.log(`📧 Sending invitation email to ${candidateEmail} for candidate ${candidateName}...`);
          
          const invitationData: any = {
            candidate_email: candidateEmail,
            candidate_name: candidateName,
            candidate_id: candidateId,
            session_id: sessionId,
            // Explicitly send interviewer mode chosen by recruiter (default to chat)
            mode: candidate.selectedMode || 'chat',
            recruiter_name: "Hiring Team",
            company_name: "SkillScreen",
            expires_in_hours: 48
          };
          
          // Add job_position_id if selected
          if (candidate.selectedJobPositionId) {
            invitationData.job_position_id = candidate.selectedJobPositionId;
          }
          
          const emailResponse = await apiClient.sendInterviewInvitation(invitationData);
          
          if (emailResponse.success || emailResponse.data) {
            console.log(`✅ Email sent successfully to ${candidateEmail}`);
            emailResults.push({ candidate, success: true });
          } else {
            console.warn(`❌ Failed to send email to ${candidateEmail}`);
            emailResults.push({ 
              candidate, 
              success: false, 
              error: 'Email sending failed' 
            });
          }
        } catch (emailError: any) {
          console.error(`Error sending email to candidate:`, emailError);
          emailResults.push({ 
            candidate, 
            success: false, 
            error: emailError.message || 'Email sending failed' 
          });
        }
      }
      
      // Update processed files with email status
      const updatedFiles = processedFiles.map((file: ProcessedFile) => {
        const emailResult = emailResults.find(r => 
          r.candidate.id === file.id || 
          (r.candidate.editedEmail === file.editedEmail && r.candidate.editedName === file.editedName)
        );
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
      
      const successCount = emailResults.filter(r => r.success).length;
      const failCount = emailResults.filter(r => !r.success).length;
      
      console.log(`Email sending complete: ${successCount} sent, ${failCount} failed`);
      
      if (successCount > 0) {
        setProcessSuccess(true);
        alert(`Successfully sent ${successCount} invitation email(s)!${failCount > 0 ? ` (${failCount} failed)` : ''}`);
      } else {
        alert("Failed to send any invitation emails. Please check the errors and try again.");
      }
      
      // Reset after delay if all successful
      if (failCount === 0 && successCount > 0) {
        setTimeout(() => {
          setSelectedFiles([]);
          setProcessedFiles([]);
          setUploadSuccess(false);
          setProcessSuccess(false);
          setUploadError(null);
        }, 3000);
      }
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
                <h4 className="text-sm font-semibold text-white">📋 Review & Edit Candidate Details</h4>
                <span className="text-xs text-white/50">
                  {processedFiles.filter(f => f.status === 'processed').length} of {processedFiles.length} processed
                </span>
              </div>
              
              <p className="text-xs text-white/60 mb-4">
                Review and edit candidate details below. Select a job position and interview mode for each candidate, then click "Send Invitations" to email them.
              </p>
              
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

              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {processedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border ${
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
                        {file.status === 'processed' && !file.emailSent && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => toggleEditMode(index)}
                            className="text-white/70 hover:text-white"
                          >
                            {file.isEditing ? <Save className="h-4 w-4" /> : <Edit2 className="h-4 w-4" />}
                          </Button>
                        )}
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
                      <div className="space-y-3 mt-3 pt-3 border-t border-white/10">
                        {/* Editable Name Field */}
                        <div>
                          <label className="text-xs text-white/70 block mb-1">Candidate Name</label>
                          {file.isEditing ? (
                            <Input
                              value={file.editedName || ''}
                              onChange={(e) => updateCandidateField(index, 'editedName', e.target.value)}
                              className="bg-white/10 border-white/20 text-white text-sm h-8"
                              placeholder="Enter candidate name"
                            />
                          ) : (
                            <span className="text-sm text-white">{file.editedName || file.extracted_name || 'N/A'}</span>
                          )}
                        </div>
                        
                        {/* Editable Email Field */}
                        <div>
                          <label className="text-xs text-white/70 block mb-1">Email Address</label>
                          {file.isEditing ? (
                            <Input
                              type="email"
                              value={file.editedEmail || ''}
                              onChange={(e) => updateCandidateField(index, 'editedEmail', e.target.value)}
                              className="bg-white/10 border-white/20 text-white text-sm h-8"
                              placeholder="Enter email address"
                            />
                          ) : (
                            <span className="text-sm text-blue-300">{file.editedEmail || file.extracted_emails?.[0] || 'N/A'}</span>
                          )}
                        </div>
                        
                        {/* Job Position Selector */}
                        <div>
                          <label className="text-xs text-white/70 block mb-1">Job Position <span className="text-yellow-400">*</span></label>
                          <Select
                            value={file.selectedJobPositionId || ''}
                            onValueChange={(value) => updateCandidateField(index, 'selectedJobPositionId', value)}
                            disabled={file.emailSent === true}
                          >
                            <SelectTrigger className="w-full bg-white/10 border-white/20 text-white text-sm h-9">
                              <SelectValue placeholder={loadingJobPositions ? "Loading positions..." : "Select a job position"} />
                            </SelectTrigger>
                            <SelectContent>
                              {jobPositions.length === 0 ? (
                                <SelectItem value="none" disabled>No job positions available</SelectItem>
                              ) : (
                                jobPositions.map((position) => (
                                  <SelectItem key={position.id} value={position.id}>
                                    {position.title}{position.department ? ` (${position.department})` : ''}
                                  </SelectItem>
                                ))
                              )}
                            </SelectContent>
                          </Select>
                          {!file.selectedJobPositionId && (
                            <p className="text-xs text-yellow-400/70 mt-1">Please select a job position for this candidate</p>
                          )}
                        </div>

                        {/* Interview Mode Selector */}
                        <div>
                          <label className="text-xs text-white/70 block mb-1">Interview Mode</label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {[
                              { value: 'chat' as const, label: 'Chat', icon: MessageCircle },
                              { value: 'audio' as const, label: 'Audio', icon: Mic },
                              { value: 'video' as const, label: 'Video', icon: Video },
                            ].map(({ value, label, icon: Icon }) => (
                              <button
                                key={value}
                                type="button"
                                onClick={() => updateCandidateField(index, 'selectedMode', value)}
                                disabled={file.emailSent === true}
                                className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs transition ${
                                  (file.selectedMode || 'chat') === value
                                    ? 'border-blue-400 bg-blue-500/20 text-blue-100'
                                    : 'border-white/20 bg-white/5 text-white/70 hover:bg-white/10'
                                }`}
                              >
                                <Icon className="h-3 w-3" />
                                <span>{label}</span>
                              </button>
                            ))}
                          </div>
                          <p className="text-[10px] text-white/40 mt-1">
                            Default is <span className="font-medium">Chat</span> if no mode is selected.
                          </p>
                        </div>
                        
                        {file.id && (
                          <div>
                            <span className="text-xs text-white/50">Candidate ID: </span>
                            <span className="text-xs text-white/70 font-mono">{file.id}</span>
                          </div>
                        )}
                        
                        {file.emailSent !== undefined && (
                          <div className="mt-2 pt-2 border-t border-white/10">
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
                    Sending Invitations...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                        Send Invitations ({processedFiles.filter(f => f.status === 'processed' && (f.editedEmail || f.extracted_emails?.length)).length})
                  </>
                )}
              </Button>
                <Button 
                    onClick={resetForm}
                  variant="outline"
                    className="border-white/20 text-white hover:bg-white/10"
                >
                  Start Over
                </Button>
            </div>
          )}

          {/* Success Message */}
          {processSuccess && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
              <CheckCircle className="h-8 w-8 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-green-300 font-medium">Invitations Sent Successfully!</p>
              <p className="text-xs text-white/60 mt-1">Candidates will receive their interview links via email.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
