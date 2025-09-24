'use client';

import { useState } from 'react';
import { Video } from 'lucide-react';

interface CodingChallengeProps {
  userType: 'candidate' | 'recruiter';
  participantName: string;
}

interface TestCase {
  input: string;
  expectedOutput: string;
  actualOutput?: string;
  passed?: boolean;
}

const mockChallenges = [
  {
    id: 1,
    title: 'Two Sum',
    difficulty: 'Easy',
    description: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Example 3:
Input: nums = [3,3], target = 6
Output: [0,1]`,
    testCases: [
      { input: '[2,7,11,15], 9', expectedOutput: '[0,1]' },
      { input: '[3,2,4], 6', expectedOutput: '[1,2]' },
      { input: '[3,3], 6', expectedOutput: '[0,1]' }
    ],
    starterCode: `function twoSum(nums, target) {
    // Your code here
}`,
    language: 'javascript'
  },
  {
    id: 2,
    title: 'Valid Parentheses',
    difficulty: 'Easy',
    description: `Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

Example 1:
Input: s = "()"
Output: true

Example 2:
Input: s = "()[]{}"
Output: true

Example 3:
Input: s = "(]"
Output: false`,
    testCases: [
      { input: '"()"', expectedOutput: 'true' },
      { input: '"()[]{}"', expectedOutput: 'true' },
      { input: '"(]"', expectedOutput: 'false' }
    ],
    starterCode: `function isValid(s) {
    // Your code here
}`,
    language: 'javascript'
  }
];

export default function CodingChallenge({ userType, participantName }: CodingChallengeProps) {
  const [selectedChallenge, setSelectedChallenge] = useState(mockChallenges[0]);
  const [code, setCode] = useState(selectedChallenge.starterCode);
  const [testResults, setTestResults] = useState<TestCase[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('javascript');

  const runTests = () => {
    setIsRunning(true);
    // Simulate test execution
    setTimeout(() => {
      const results = selectedChallenge.testCases.map((testCase, index) => ({
        ...testCase,
        actualOutput: index === 0 ? '[0,1]' : index === 1 ? '[1,2]' : '[0,1]',
        passed: Math.random() > 0.3 // Simulate some tests passing
      }));
      setTestResults(results);
      setIsRunning(false);
    }, 2000);
  };

  const submitSolution = () => {
    setIsRunning(true);
    // Simulate submission
    setTimeout(() => {
      alert('Solution submitted successfully!');
      setIsRunning(false);
    }, 1500);
  };

  return (
    <div className="flex-1 flex">
      {/* Main Code Editor Area */}
      <div className="flex-1 flex flex-col">
        {/* Language Selection and Actions */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center space-x-4">
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-[#2A2A2A] text-white text-sm px-3 py-1.5 rounded-md border border-white/10 focus:outline-none focus:border-white/20"
            >
              <option value="javascript">JavaScript</option>
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </select>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={runTests}
              disabled={isRunning}
              className="px-4 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-md text-sm font-medium transition-all"
            >
              Run
            </button>
            <button
              onClick={runTests}
              disabled={isRunning}
              className="px-4 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-md text-sm font-medium transition-all"
            >
              Debug
            </button>
            <button
              onClick={submitSolution}
              disabled={isRunning}
              className="px-4 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-md text-sm font-medium transition-all"
            >
              Submit
            </button>
          </div>
        </div>

        {/* Code Editor */}
        <div className="flex-1 bg-[#1E1E1E]">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-full bg-transparent text-white font-mono text-sm p-4 resize-none focus:outline-none"
            placeholder="Write your solution here..."
            readOnly={userType === 'recruiter'}
          />
        </div>
      </div>

      {/* Right Panel - Question and Terminal */}
      <div className="w-[400px] flex flex-col border-l border-white/10">
        {/* Question Section */}
        <div className="h-1/2 border-b border-white/10 p-4 overflow-y-auto">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-white mb-2">{selectedChallenge.title}</h2>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              selectedChallenge.difficulty === 'Easy' ? 'bg-green-500/20 text-green-300' :
              selectedChallenge.difficulty === 'Medium' ? 'bg-yellow-500/20 text-yellow-300' :
              'bg-red-500/20 text-red-300'
            }`}>
              {selectedChallenge.difficulty}
            </span>
          </div>
          <div className="text-white/80 text-sm whitespace-pre-line leading-relaxed">
            {selectedChallenge.description}
          </div>
        </div>

        {/* Terminal Section */}
        <div className="h-1/2 bg-[#1E1E1E] p-4 overflow-y-auto">
          <h3 className="text-lg font-semibold text-white mb-4">TERMINAL</h3>
          {testResults.length === 0 ? (
            <div className="text-white/60 text-sm">
              Run your code to see the output here...
            </div>
          ) : (
            <div className="space-y-4">
              {testResults.map((result, index) => (
                <div key={index} className="font-mono text-sm">
                  <div className="text-white/80">Test Case {index + 1}:</div>
                  <div className="text-white/60 ml-4">Input: {result.input}</div>
                  <div className="text-white/60 ml-4">Expected: {result.expectedOutput}</div>
                  <div className={`ml-4 ${result.passed ? 'text-green-400' : 'text-red-400'}`}>
                    Output: {result.actualOutput}
                  </div>
                </div>
              ))}
              {testResults.length > 0 && (
                <div className="pt-4 border-t border-white/10 text-sm">
                  <div className="text-white/80">Summary:</div>
                  <div className="text-white/60">Runtime: 2ms</div>
                  <div className="text-white/60">Memory: 42.1 MB</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
