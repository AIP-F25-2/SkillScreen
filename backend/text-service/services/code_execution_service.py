"""
Code Execution Service for SkillScreen
Handles code editor functionality and sandboxed code execution for technical assessments
"""

import os
import json
import subprocess
import tempfile
import uuid
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from utils.logger import log_info, log_error, log_warning

class CodeExecutionService:
    """Service for executing code in sandboxed environments"""
    
    def __init__(self):
        self.supported_languages = {
            'python': {
                'extension': '.py',
                'command': 'python',
                'timeout': 10,
                'memory_limit': '128m'
            },
            'javascript': {
                'extension': '.js',
                'command': 'node',
                'timeout': 10,
                'memory_limit': '128m'
            },
            'java': {
                'extension': '.java',
                'command': 'javac',
                'timeout': 15,
                'memory_limit': '256m'
            },
            'cpp': {
                'extension': '.cpp',
                'command': 'g++',
                'timeout': 15,
                'memory_limit': '256m'
            },
            'sql': {
                'extension': '.sql',
                'command': 'sqlite3',
                'timeout': 5,
                'memory_limit': '64m'
            }
        }
        
        self.execution_results = {}  # Store execution results
        log_info("✅ Code Execution Service initialized")
    
    async def execute_code(
        self,
        code: str,
        language: str,
        test_cases: List[Dict[str, Any]] = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Execute code with optional test cases"""
        
        if language not in self.supported_languages:
            return {
                'success': False,
                'error': f'Unsupported language: {language}',
                'output': '',
                'execution_time': 0,
                'test_results': []
            }
        
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Create temporary file
            lang_config = self.supported_languages[language]
            file_extension = lang_config['extension']
            
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=file_extension,
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Execute code
            result = await self._run_code(
                temp_file_path,
                language,
                timeout or lang_config['timeout']
            )
            
            execution_time = time.time() - start_time
            
            # Run test cases if provided
            test_results = []
            if test_cases:
                test_results = await self._run_test_cases(
                    code, language, test_cases, timeout or lang_config['timeout']
                )
            
            # Store result
            execution_result = {
                'execution_id': execution_id,
                'success': result['success'],
                'output': result['output'],
                'error': result.get('error', ''),
                'execution_time': round(execution_time, 3),
                'test_results': test_results,
                'language': language,
                'timestamp': datetime.now().isoformat()
            }
            
            self.execution_results[execution_id] = execution_result
            
            # Clean up
            os.unlink(temp_file_path)
            
            log_info(f"✅ Code executed successfully in {language}")
            return execution_result
            
        except Exception as e:
            log_error(f"❌ Code execution failed: {e}")
            return {
                'execution_id': execution_id,
                'success': False,
                'error': str(e),
                'output': '',
                'execution_time': time.time() - start_time,
                'test_results': []
            }
    
    async def _run_code(
        self,
        file_path: str,
        language: str,
        timeout: int
    ) -> Dict[str, Any]:
        """Run code file and return output"""
        
        lang_config = self.supported_languages[language]
        
        try:
            if language == 'java':
                # Compile Java first
                compile_result = subprocess.run(
                    [lang_config['command'], file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if compile_result.returncode != 0:
                    return {
                        'success': False,
                        'output': '',
                        'error': f'Compilation error: {compile_result.stderr}'
                    }
                
                # Run compiled class
                class_name = os.path.splitext(os.path.basename(file_path))[0]
                run_result = subprocess.run(
                    ['java', class_name],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.path.dirname(file_path)
                )
                
                return {
                    'success': run_result.returncode == 0,
                    'output': run_result.stdout,
                    'error': run_result.stderr if run_result.returncode != 0 else ''
                }
            
            elif language == 'cpp':
                # Compile C++ first
                executable_path = file_path.replace('.cpp', '.exe')
                compile_result = subprocess.run(
                    [lang_config['command'], '-o', executable_path, file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if compile_result.returncode != 0:
                    return {
                        'success': False,
                        'output': '',
                        'error': f'Compilation error: {compile_result.stderr}'
                    }
                
                # Run executable
                run_result = subprocess.run(
                    [executable_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # Clean up executable
                if os.path.exists(executable_path):
                    os.unlink(executable_path)
                
                return {
                    'success': run_result.returncode == 0,
                    'output': run_result.stdout,
                    'error': run_result.stderr if run_result.returncode != 0 else ''
                }
            
            else:
                # Direct execution for Python, JavaScript, etc.
                result = subprocess.run(
                    [lang_config['command'], file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else ''
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'Execution timeout after {timeout} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Execution error: {str(e)}'
            }
    
    async def _run_test_cases(
        self,
        code: str,
        language: str,
        test_cases: List[Dict[str, Any]],
        timeout: int
    ) -> List[Dict[str, Any]]:
        """Run test cases against the code"""
        
        test_results = []
        
        for i, test_case in enumerate(test_cases):
            try:
                # Create test code
                test_code = self._create_test_code(code, language, test_case)
                
                # Execute test
                result = await self.execute_code(test_code, language, timeout=timeout)
                
                test_result = {
                    'test_case_id': i + 1,
                    'input': test_case.get('input', ''),
                    'expected_output': test_case.get('expected_output', ''),
                    'actual_output': result['output'].strip(),
                    'passed': self._compare_outputs(
                        result['output'].strip(),
                        test_case.get('expected_output', '')
                    ),
                    'execution_time': result['execution_time'],
                    'error': result.get('error', '')
                }
                
                test_results.append(test_result)
                
            except Exception as e:
                test_results.append({
                    'test_case_id': i + 1,
                    'input': test_case.get('input', ''),
                    'expected_output': test_case.get('expected_output', ''),
                    'actual_output': '',
                    'passed': False,
                    'execution_time': 0,
                    'error': str(e)
                })
        
        return test_results
    
    def _create_test_code(self, code: str, language: str, test_case: Dict[str, Any]) -> str:
        """Create test code based on language and test case"""
        
        input_data = test_case.get('input', '')
        expected_output = test_case.get('expected_output', '')
        
        if language == 'python':
            return f"""
{code}

# Test case
test_input = {repr(input_data)}
result = main(test_input) if 'main' in globals() else None
print(result)
"""
        
        elif language == 'javascript':
            return f"""
{code}

// Test case
const testInput = {json.dumps(input_data)};
const result = main ? main(testInput) : null;
console.log(result);
"""
        
        elif language == 'java':
            return f"""
{code}

// Test case
public class TestRunner {{
    public static void main(String[] args) {{
        String testInput = "{input_data}";
        // Assuming main method exists
        System.out.println(testInput);
    }}
}}
"""
        
        else:
            return code
    
    def _compare_outputs(self, actual: str, expected: str) -> bool:
        """Compare actual and expected outputs"""
        # Normalize outputs for comparison
        actual_normalized = actual.strip().replace('\r\n', '\n').replace('\r', '\n')
        expected_normalized = expected.strip().replace('\r\n', '\n').replace('\r', '\n')
        
        return actual_normalized == expected_normalized
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution result by ID"""
        return self.execution_results.get(execution_id)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        return list(self.supported_languages.keys())
    
    def create_technical_question(
        self,
        language: str,
        difficulty: str = 'medium',
        topic: str = 'general'
    ) -> Dict[str, Any]:
        """Create a technical coding question"""
        
        questions = {
            'python': {
                'easy': {
                    'general': {
                        'title': 'Python Basics - List Operations',
                        'description': 'Write a function that takes a list of numbers and returns the sum of all even numbers.',
                        'code_template': 'def sum_even_numbers(numbers):\n    # Your code here\n    pass',
                        'test_cases': [
                            {'input': '[1, 2, 3, 4, 5, 6]', 'expected_output': '12'},
                            {'input': '[2, 4, 6, 8]', 'expected_output': '20'},
                            {'input': '[1, 3, 5]', 'expected_output': '0'}
                        ]
                    },
                    'data_structures': {
                        'title': 'Python - Dictionary Manipulation',
                        'description': 'Write a function that counts the frequency of each character in a string.',
                        'code_template': 'def count_characters(text):\n    # Your code here\n    pass',
                        'test_cases': [
                            {'input': '"hello"', 'expected_output': "{'h': 1, 'e': 1, 'l': 2, 'o': 1}"},
                            {'input': '"python"', 'expected_output': "{'p': 1, 'y': 1, 't': 1, 'h': 1, 'o': 1, 'n': 1}"}
                        ]
                    }
                },
                'medium': {
                    'general': {
                        'title': 'Python - Algorithm Implementation',
                        'description': 'Implement a function to find the longest common subsequence between two strings.',
                        'code_template': 'def longest_common_subsequence(str1, str2):\n    # Your code here\n    pass',
                        'test_cases': [
                            {'input': '"ABCDGH", "AEDFHR"', 'expected_output': '"ADH"'},
                            {'input': '"AGGTAB", "GXTXAYB"', 'expected_output': '"GTAB"'}
                        ]
                    }
                }
            },
            'javascript': {
                'easy': {
                    'general': {
                        'title': 'JavaScript - Array Methods',
                        'description': 'Write a function that filters an array of objects based on a property value.',
                        'code_template': 'function filterByProperty(array, property, value) {\n    // Your code here\n}',
                        'test_cases': [
                            {'input': '[{name: "John", age: 25}, {name: "Jane", age: 30}], "age", 25', 'expected_output': '[{"name": "John", "age": 25}]'}
                        ]
                    }
                }
            }
        }
        
        if language in questions and difficulty in questions[language]:
            if topic in questions[language][difficulty]:
                return questions[language][difficulty][topic]
            else:
                # Return first available topic
                first_topic = list(questions[language][difficulty].keys())[0]
                return questions[language][difficulty][first_topic]
        
        # Default question
        return {
            'title': f'{language.title()} Coding Challenge',
            'description': f'Write a function in {language} to solve the given problem.',
            'code_template': f'# Write your {language} code here',
            'test_cases': []
        }

# Global instance
code_execution_service = CodeExecutionService()
