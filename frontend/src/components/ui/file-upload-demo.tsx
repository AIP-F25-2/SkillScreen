'use client';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useFileUpload } from "@/components/ui/use-file-upload";
import { Upload, FileText, Trash2, CheckCircle, Loader2 } from "lucide-react";
import { useCallback, useState } from "react";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";
import { getDemoJobDescription } from "@/lib/demoHelpers";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function FileUploadDemo() {
  const router = useRouter();
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedCandidate, setUploadedCandidate] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processSuccess, setProcessSuccess] = useState(false);
  const [candidateName, setCandidateName] = useState("");
  const [selectedJob, setSelectedJob] = useState<string>("");
  const [jobOptions] = useState<string[]>([
    'Senior Software Engineer',
    'Product Manager',
    'UX Designer'
  ]);
  
  // Parsed data states (editable by recruiter)
  const [parsedName, setParsedName] = useState("");
  const [parsedEmail, setParsedEmail] = useState("");
  const [parsedPhone, setParsedPhone] = useState("");
  const [parsedSkills, setParsedSkills] = useState<string[]>([]);
  const [parsedExperience, setParsedExperience] = useState(0);
  const [showParsedData, setShowParsedData] = useState(false);

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
    onUpload: (file) => {
      setUploadedFile(file);
      setUploadSuccess(false);
      setProcessSuccess(false);
    },
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

  const handleUpload = async () => {
    if (!uploadedFile) return;

    setIsUploading(true);
    try {
      // Step 1: Upload to media service for storage
      console.log("Uploading resume to media service...");
      const uploadResponse = await apiClient.uploadResume(uploadedFile, candidateName || undefined);
      
      if (!uploadResponse.success) {
        throw new Error("Failed to upload resume to media service");
      }

      console.log("Resume uploaded to media service:", uploadResponse.data);

      // Step 2: Parse resume using Interview Service (resume upload)
      console.log("Parsing resume via interview-service...");
      try {
        const parseResponse = await apiClient.uploadResumeForParsing(uploadedFile);
        console.log("Interview-service parse response:", parseResponse);

        // Extract parsed data from interview-service response
        const firstFile = parseResponse?.data?.files?.[0];
        const parsedData = {
          name: firstFile?.extracted_name || uploadResponse.data.candidate_name || candidateName || "Unknown Candidate",
          email: firstFile?.extracted_emails?.[0] || "candidate@example.com",
          phone: "",
          raw_text: "",
          skills: [],
          experience_years: 0,
          education: []
        };
        const resumeSkills: string[] = [];

        // Step 3: Create candidate in AI service
        const candidateData = {
          name: parsedData.name || candidateName || uploadResponse.data.candidate_name || "Candidate",
          email: parsedData.email || "candidate@example.com",
          phone: parsedData.phone || "",
          resume_text: parsedData.raw_text || "",
          skills: resumeSkills,
          experience_years: parsedData.experience_years || 0,
          education: parsedData.education || []
        };

        console.log("Creating AI candidate with data:", candidateData);
        const aiCandidateResponse = await apiClient.createAICandidate(candidateData);
        console.log("AI candidate created:", aiCandidateResponse);

        // Step 4: Create demo job based on skills
        const demoJob = getDemoJobDescription(resumeSkills);
        // Use selected job title from dropdown if provided
        if (selectedJob) {
          demoJob.title = selectedJob;
        }
        console.log("Creating demo job:", demoJob);
        const aiJobResponse = await apiClient.createAIJob(demoJob);
        console.log("AI job created:", aiJobResponse);

        // Step 5: Start AI interview to generate questions
        const candidateId = (aiCandidateResponse as any).candidate_id || aiCandidateResponse.data?.candidate_id;
        const jobId = (aiJobResponse as any).job_id || aiJobResponse.data?.job_id;
        
        const aiInterviewResponse = await apiClient.startAIInterview({
          candidate_id: candidateId,
          job_id: jobId,
          interview_type: "standard",
          difficulty: "medium",
          max_questions: 9
        });
        console.log("AI interview started:", aiInterviewResponse);

        const sessionId = (aiInterviewResponse as any).session_id || aiInterviewResponse.data?.session_id;

        // Populate parsed data fields for recruiter review/edit
        // Use manual input as fallback if AI parsing returns generic/default values
        const aiName = parsedData.name || candidateData.name || "";
        const isGenericName = aiName === "Unknown Candidate" || aiName === "Candidate" || aiName === "";
        
        setParsedName(isGenericName && candidateName ? candidateName : aiName);
        setParsedEmail(parsedData.email === "candidate@example.com" ? "" : (parsedData.email || candidateData.email || ""));
        setParsedPhone(parsedData.phone || "");
        setParsedSkills(resumeSkills);
        setParsedExperience(parsedData.experience_years || 0);
        setShowParsedData(true);
        
        // Combine all data for frontend use
        setUploadedCandidate({
          ...uploadResponse.data,
          ai_candidate_id: candidateId,
          ai_job_id: jobId,
          ai_session_id: sessionId,
          parsed_skills: resumeSkills,
          parsed_experience: parsedData.experience_years,
          parsed_name: parsedData.name,
          parsed_email: parsedData.email,
          parsed_phone: parsedData.phone,
          job_title: demoJob.title
        });
        setUploadSuccess(true);
        console.log("Resume upload and AI processing completed successfully!");
      } catch (aiError) {
        console.warn("AI service not available, using basic upload:", aiError);
        // Fallback to basic upload if AI service is unavailable
        
        // Set basic data from upload response
        setParsedName(uploadResponse.data.candidate_name || candidateName || "");
        setParsedEmail("");
        setParsedPhone("");
        setParsedSkills([]);
        setParsedExperience(0);
        setShowParsedData(true);
        
        setUploadedCandidate(uploadResponse.data);
        setUploadSuccess(true);
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcess = async () => {
    if (!uploadedCandidate) return;

    setIsProcessing(true);
    try {
      // Step 1: Schedule the candidate (creates interview record)
      const response = await apiClient.scheduleCandidate(uploadedCandidate.candidate_id);
      if (!response.success) {
        throw new Error("Failed to schedule candidate");
      }
      
      console.log("Interview scheduled:", response.data);
      
      // Step 2: Send email invitation with parsed data
      const candidateEmail = parsedEmail || uploadedCandidate.candidate_email || "candidate@example.com";
      const candidateName = parsedName || uploadedCandidate.candidate_name || "Candidate";
      
      // Only send email if we have a valid email address
      if (candidateEmail && candidateEmail !== "candidate@example.com") {
        console.log("Sending interview invitation to:", candidateEmail);
        
        const emailResponse = await fetch('http://localhost:8003/api/email/send-invitation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            candidate_email: candidateEmail,
            candidate_name: candidateName,
            candidate_id: uploadedCandidate.candidate_id,
            session_id: response.data.session_id,
            recruiter_name: "Hiring Team",
            company_name: "SkillScreen"
          })
        });
        
        if (emailResponse.ok) {
          const emailData = await emailResponse.json();
          console.log("Email invitation sent:", emailData);
          alert(`Interview scheduled for ${candidateName}!\n\nInterview invitation sent to: ${candidateEmail}\nSession ID: ${response.data.session_id}`);
        } else {
          console.warn("Failed to send email invitation, but interview is scheduled");
          alert(`Interview scheduled for ${candidateName}!\n\nNote: Email invitation failed to send.\nSession ID: ${response.data.session_id}`);
        }
      } else {
        console.warn("No valid email address found, skipping email invitation");
        alert(`Interview scheduled for ${candidateName}!\n\nNote: No valid email address found, no invitation sent.\nSession ID: ${response.data.session_id}`);
      }
      
      setProcessSuccess(true);
      
      // Reset form after delay
      setTimeout(() => {
        remove();
        setUploadedFile(null);
        setUploadedCandidate(null);
        setUploadSuccess(false);
        setProcessSuccess(false);
        setCandidateName("");
        setParsedName("");
        setParsedEmail("");
        setParsedPhone("");
        setParsedSkills([]);
        setParsedExperience(0);
        setShowParsedData(false);
      }, 2000);
    } catch (error) {
      console.error("Process error:", error);
      alert("Failed to process candidate. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="w-full rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-4 space-y-1">
        <h3 className="text-lg font-medium text-white">Upload Candidate Resume</h3>
        <p className="text-sm text-white/70">Upload PDF resume and process for interview scheduling (assigned to ashish)</p>
      </div>

      {/* Candidate Name Input */}
      {!uploadSuccess && (
        <div className="mb-4">
          <label className="text-sm text-white/80 mb-2 block">Candidate Name (optional)</label>
          <Input
            type="text"
            value={candidateName}
            onChange={(e) => setCandidateName(e.target.value)}
            placeholder="Enter candidate name..."
            className="bg-white/5 border-white/10 text-white"
          />
        </div>
      )}

      <Input
        type="file"
        accept=".pdf"
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
            <p className="text-sm font-medium text-white">Click to select PDF</p>
            <p className="text-xs text-white/60">or drag and drop resume here</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-4 rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="rounded-md bg-white/10 p-2">
              <FileText className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <div className="text-white text-sm font-medium">{fileName}</div>
              {fileSize !== null && (
                <div className="text-xs text-white/60">{(fileSize / (1024 * 1024)).toFixed(2)} MB</div>
              )}
              {uploadSuccess && (
                <div className="flex items-center gap-1 text-xs text-green-400 mt-1">
                  <CheckCircle className="h-3 w-3" />
                  Uploaded successfully
                </div>
              )}
            </div>
            {!uploadSuccess && (
              <div className="flex items-center gap-2">
                <Button size="sm" variant="secondary" onClick={openPicker}>
                  Replace
                </Button>
                <Button size="sm" variant="destructive" onClick={remove}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            )}
            <div className="flex items-center gap-2">
              <label className="text-xs text-white/70">Job:</label>
              <Select onValueChange={setSelectedJob}>
                <SelectTrigger className="w-[220px]">
                  <SelectValue placeholder="Select job from Active Listings" />
                </SelectTrigger>
                <SelectContent>
                  {jobOptions.map((opt) => (
                    <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Upload Button */}
          {!uploadSuccess && (
            <Button 
              onClick={handleUpload} 
              disabled={isUploading}
              className="w-full"
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Resume
                </>
              )}
            </Button>
          )}

          {/* Parsed Data Review Section */}
          {uploadSuccess && !processSuccess && showParsedData && (
            <div className="space-y-4 bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-white">📋 Parsed Resume Data</h4>
                <span className="text-xs text-white/50">Review & Edit</span>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                {/* Name */}
                <div>
                  <label className="text-xs text-white/70 mb-1 block">Name</label>
                  <Input
                    type="text"
                    value={parsedName}
                    onChange={(e) => setParsedName(e.target.value)}
                    placeholder="Full name"
                    className="bg-white/10 border-white/20 text-white text-sm"
                  />
                </div>
                
                {/* Email */}
                <div>
                  <label className="text-xs text-white/70 mb-1 block">Email</label>
                  <Input
                    type="email"
                    value={parsedEmail}
                    onChange={(e) => setParsedEmail(e.target.value)}
                    placeholder="email@example.com"
                    className="bg-white/10 border-white/20 text-white text-sm"
                  />
                </div>
                
                {/* Phone */}
                <div>
                  <label className="text-xs text-white/70 mb-1 block">Phone</label>
                  <Input
                    type="text"
                    value={parsedPhone}
                    onChange={(e) => setParsedPhone(e.target.value)}
                    placeholder="+1 (555) 123-4567"
                    className="bg-white/10 border-white/20 text-white text-sm"
                  />
                </div>
                
                {/* Experience */}
                <div>
                  <label className="text-xs text-white/70 mb-1 block">Years of Experience</label>
                  <Input
                    type="number"
                    value={parsedExperience}
                    onChange={(e) => setParsedExperience(parseInt(e.target.value) || 0)}
                    placeholder="0"
                    className="bg-white/10 border-white/20 text-white text-sm"
                  />
                </div>
              </div>
              
              {/* Skills */}
              <div>
                <label className="text-xs text-white/70 mb-1 block">Skills Detected</label>
                <div className="flex flex-wrap gap-2 min-h-[32px] p-2 bg-white/10 border border-white/20 rounded-md">
                  {parsedSkills.length > 0 ? (
                    parsedSkills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full border border-blue-500/30"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-white/40">No skills detected</span>
                  )}
                </div>
                <p className="text-xs text-white/50 mt-1">
                  {parsedSkills.length} skill{parsedSkills.length !== 1 ? 's' : ''} found
                </p>
              </div>
            </div>
          )}

          {/* Process Button */}
          {uploadSuccess && !processSuccess && (
            <div className="space-y-2">
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                <p className="text-sm text-blue-300">
                  <strong>Ready to Schedule:</strong> {parsedName || uploadedCandidate?.candidate_name || 'Unknown'}<br />
                  <strong>Email:</strong> {parsedEmail || 'Not provided'}<br />
                  <strong>Assigned to:</strong> ashish
                </p>
              </div>
              
              <div className="flex gap-3">
              <Button 
                onClick={handleProcess} 
                disabled={isProcessing}
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
                    Process & Schedule Interview
                  </>
                )}
              </Button>
                
                <Button 
                  onClick={openPicker}
                  variant="outline"
                  className="flex-1 border-white/20 text-white hover:bg-white/10"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Upload More
                </Button>
              </div>
            </div>
          )}

          {/* Success Message */}
          {processSuccess && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
              <CheckCircle className="h-8 w-8 text-green-400 mx-auto mb-2" />
              <p className="text-sm text-green-300 font-medium">Interview Scheduled Successfully!</p>
              <p className="text-xs text-white/60 mt-1">Resetting form...</p>
            </div>
          )}
        </div>
      )}

      {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
    </div>
  );
}


