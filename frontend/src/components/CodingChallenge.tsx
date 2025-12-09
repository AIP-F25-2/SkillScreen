import { useState, useEffect } from 'react';
import { Video } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface CodingChallengeProps {
  userType: 'candidate' | 'recruiter';
  participantName: string;
  videoStream?: MediaStream | null;
  challengeData?: any;
  onComplete?: () => void;
}

interface TestCase {
  id: string;
  input: string;
  expectedOutput: string;
  actualOutput?: string;
  passed?: boolean;
  weight?: number;
  stdout?: string;
  stderr?: string;
}

interface ChallengeData {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  testCases: TestCase[];
  starterCode: string;
  language: string;
  languageId: number;
}

export default function CodingChallenge({ userType, participantName, videoStream, challengeData, onComplete }: CodingChallengeProps) {
  const [challenge, setChallenge] = useState<ChallengeData | null>(null);
  const [code, setCode] = useState('');
  const [testResults, setTestResults] = useState<TestCase[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('python'); // Default to Python as per request example

  // Initialize from props or listen for event
  useEffect(() => {
    const initChallenge = (data: any) => {
      console.log('Initializing coding challenge with data:', data);
      if (data) {
        setChallenge({
          id: data.id || '1',
          title: data.title || 'Coding Challenge',
          description: data.description || 'Solve the problem.',
          difficulty: data.difficulty || 'Medium',
          testCases: data.testCases || [],
          starterCode: data.starterCode || '# Write your code here\n',
          language: data.language || 'python',
          languageId: data.languageId || 71 // Default to Python (71)
        });
        setCode(data.starterCode || '# Write your code here\n');
        if (data.language) setSelectedLanguage(data.language);
      }
    };

    if (challengeData) {
      initChallenge(challengeData);
    }

    const handleData = (e: CustomEvent) => {
      console.log('Received coding challenge data event:', e.detail);
      initChallenge(e.detail);
    };

    window.addEventListener('coding-challenge-data' as any, handleData);
    return () => {
      window.removeEventListener('coding-challenge-data' as any, handleData);
    };
  }, [challengeData]);

  const runTests = async () => {
    if (!challenge) return;
    setIsRunning(true);
    setOutput('Running code...');

    try {
      const response = await apiClient.runCode({
        languageId: challenge.languageId,
        sourceCode: code,
        testCases: challenge.testCases
      }) as any; // Cast to any to avoid type errors for now, or define proper response type

      if (response.success && response.data) {
        setOutput(response.data.stdout || response.data.stderr || 'No output');
      } else {
        setOutput('Error running code');
      }
    } catch (error) {
      console.error('Run code error:', error);
      setOutput('Failed to run code');
    } finally {
      setIsRunning(false);
    }
  };

  const submitSolution = async () => {
    if (!challenge) return;
    setIsRunning(true);
    setOutput('Evaluating solution...');

    try {
      const response = await apiClient.evaluateCode({
        languageId: challenge.languageId,
        sourceCode: code,
        testCases: challenge.testCases
      }) as any; // Cast to any

      if (response.success && response.data) {
        const results = response.data.results || [];
        setTestResults(results);

        const allPassed = results.every((r: any) => r.passed);
        if (allPassed) {
          alert('All test cases passed! Submitting...');
          if (onComplete) onComplete();
        } else {
          alert('Some test cases failed. Please check the results.');
        }
      }
    } catch (error) {
      console.error('Evaluation error:', error);
      alert('Failed to evaluate solution');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex-1 flex h-full">
      {/* Main Code Editor Area */}
      <div className="flex-1 flex flex-col h-full">
        {/* Language Selection and Actions */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-[#1E1E1E]">
          <div className="flex items-center space-x-4">
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-[#2A2A2A] text-white text-sm px-3 py-1.5 rounded-md border border-white/10 focus:outline-none focus:border-white/20"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </select>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={runTests}
              disabled={isRunning}
              className="px-4 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-md text-sm font-medium transition-all disabled:opacity-50"
            >
              Run
            </button>
            <button
              onClick={submitSolution}
              disabled={isRunning}
              className="px-4 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-md text-sm font-medium transition-all disabled:opacity-50"
            >
              Submit
            </button>
          </div>
        </div>

        {/* Code Editor */}
        <div className="flex-1 bg-[#1E1E1E] relative">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-full bg-transparent text-white font-mono text-sm p-4 resize-none focus:outline-none"
            placeholder="Write your solution here..."
            readOnly={userType === 'recruiter'}
            spellCheck={false}
          />

          {/* Camera Overlay */}
          <div className="absolute bottom-4 right-4 w-48 h-36 bg-black/50 rounded-lg overflow-hidden border border-white/10 shadow-lg">
            {videoStream ? (
              <video
                autoPlay
                playsInline
                muted
                ref={(video) => {
                  if (video) video.srcObject = videoStream;
                }}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Video className="w-8 h-8 text-white/30" />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - Question and Terminal */}
      <div className="w-[400px] flex flex-col border-l border-white/10 bg-[#1E1E1E]">
        {/* Question Section */}
        <div className="h-1/2 border-b border-white/10 p-4 overflow-y-auto">
          {challenge ? (
            <>
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-white mb-2">{challenge.title}</h2>
                <span className={`px-2 py-1 rounded text-xs font-medium ${challenge.difficulty === 'Easy' ? 'bg-green-500/20 text-green-300' :
                  challenge.difficulty === 'Medium' ? 'bg-yellow-500/20 text-yellow-300' :
                    'bg-red-500/20 text-red-300'
                  }`}>
                  {challenge.difficulty}
                </span>
              </div>
              <div className="text-white/80 text-sm whitespace-pre-line leading-relaxed">
                {challenge.description}
              </div>
            </>
          ) : (
            <div className="text-white/60 text-center mt-10">Loading challenge...</div>
          )}
        </div>

        {/* Terminal Section */}
        <div className="h-1/2 bg-[#0A0A0A] p-4 overflow-y-auto font-mono text-sm">
          <h3 className="text-xs font-semibold text-white/50 mb-2 uppercase tracking-wider">Console Output</h3>
          {output && (
            <div className="mb-4 text-white/80 whitespace-pre-wrap border-b border-white/10 pb-4">
              {output}
            </div>
          )}

          {testResults.length > 0 && (
            <div className="space-y-3">
              {testResults.map((result, index) => (
                <div key={index} className="bg-white/5 p-3 rounded">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-white/60 text-xs">Test Case {index + 1}</span>
                    <span className={`text-xs font-bold ${result.passed ? 'text-green-400' : 'text-red-400'}`}>
                      {result.passed ? 'PASSED' : 'FAILED'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-white/40 block">Input</span>
                      <span className="text-white/80">{result.input || '""'}</span>
                    </div>
                    <div>
                      <span className="text-white/40 block">Expected</span>
                      <span className="text-white/80">{result.expectedOutput}</span>
                    </div>
                  </div>
                  {!result.passed && (
                    <div className="mt-2 pt-2 border-t border-white/10">
                      <span className="text-white/40 block text-xs">Actual Output</span>
                      <span className="text-red-300 text-xs">{result.stdout || result.stderr || 'No output'}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
