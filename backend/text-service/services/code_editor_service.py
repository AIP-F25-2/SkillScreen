"""
Code Editor Service for SkillScreen
Provides a separate service for managing code editor sessions, syntax highlighting, and code assessment
This service integrates with the coding question workflow
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

from utils.logger import log_info, log_error, log_warning
from services.code_execution_service import code_execution_service

class CodeEditorService:
    """Service for managing code editor sessions and assessments"""
    
    def __init__(self):
        # Supported languages for the code editor
        self.supported_languages = {
            'python': {
                'name': 'Python',
                'extension': '.py',
                'syntax': 'python',
                'default_template': 'def solution():\n    # Write your solution here\n    pass'
            },
            'javascript': {
                'name': 'JavaScript',
                'extension': '.js',
                'syntax': 'javascript',
                'default_template': 'function solution() {\n    // Write your solution here\n}'
            },
            'java': {
                'name': 'Java',
                'extension': '.java',
                'syntax': 'java',
                'default_template': 'public class Solution {\n    public void solution() {\n        // Write your solution here\n    }\n}'
            },
            'cpp': {
                'name': 'C++',
                'extension': '.cpp',
                'syntax': 'cpp',
                'default_template': '#include <iostream>\nusing namespace std;\n\nint solution() {\n    // Write your solution here\n    return 0;\n}'
            },
            'sql': {
                'name': 'SQL',
                'extension': '.sql',
                'syntax': 'sql',
                'default_template': '-- Write your SQL query here\nSELECT * FROM table_name;'
            }
        }
        
        # Store active editor sessions in memory (can be moved to database later)
        self._editor_sessions = {}
        
        log_info("[OK] Code Editor Service initialized")
    
    def create_editor_session(
        self,
        coding_session_id: str,
        question_data: Dict[str, Any],
        language: str = 'python'
    ) -> Dict[str, Any]:
        """Create a new code editor session for a coding question"""
        try:
            session_id = str(uuid.uuid4())
            
            # Validate language
            if language not in self.supported_languages:
                language = 'python'
                log_warning(f"Unsupported language, defaulting to Python")
            
            language_info = self.supported_languages[language]
            
            # Create editor session
            editor_session = {
                'session_id': session_id,
                'coding_session_id': coding_session_id,
                'question_data': question_data,
                'language': language,
                'language_info': language_info,
                'code': language_info['default_template'],
                'test_cases': question_data.get('test_cases', []),
                'expected_outputs': question_data.get('expected_outputs', []),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'last_modified': datetime.now(timezone.utc).isoformat(),
                'execution_history': [],
                'status': 'active'
            }
            
            self._editor_sessions[session_id] = editor_session
            
            log_info(f"[CODE EDITOR] Created editor session {session_id} for coding session {coding_session_id}")
            
            return {
                'editor_session_id': session_id,
                'coding_session_id': coding_session_id,
                'language': language,
                'language_info': language_info,
                'code_template': language_info['default_template'],
                'question_data': question_data,
                'supported_languages': list(self.supported_languages.keys())
            }
            
        except Exception as e:
            log_error(f"Error creating editor session: {e}")
            raise
    
    def update_code(
        self,
        editor_session_id: str,
        code: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update code in an editor session"""
        try:
            if editor_session_id not in self._editor_sessions:
                raise ValueError(f"Editor session {editor_session_id} not found")
            
            session = self._editor_sessions[editor_session_id]
            
            # Update code
            session['code'] = code
            session['last_modified'] = datetime.now(timezone.utc).isoformat()
            
            # Update language if provided
            if language and language in self.supported_languages:
                session['language'] = language
                session['language_info'] = self.supported_languages[language]
            
            log_info(f"[CODE EDITOR] Updated code in session {editor_session_id}")
            
            return {
                'status': 'success',
                'editor_session_id': editor_session_id,
                'code_length': len(code),
                'language': session['language']
            }
            
        except Exception as e:
            log_error(f"Error updating code: {e}")
            raise
    
    async def execute_code(
        self,
        editor_session_id: str,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute code from an editor session"""
        try:
            if editor_session_id not in self._editor_sessions:
                raise ValueError(f"Editor session {editor_session_id} not found")
            
            session = self._editor_sessions[editor_session_id]
            
            # Use provided code or code from session
            code_to_execute = code or session['code']
            language = session['language']
            
            log_info(f"[CODE EDITOR] Executing {language} code in session {editor_session_id}")
            
            # Execute using code execution service
            execution_result = await code_execution_service.execute_code(
                code=code_to_execute,
                language=language
            )
            
            # Store execution history
            execution_record = {
                'execution_id': execution_result.get('execution_id'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': execution_result.get('status'),
                'output': execution_result.get('output', ''),
                'error': execution_result.get('error', ''),
                'execution_time': execution_result.get('execution_time', 0)
            }
            
            session['execution_history'].append(execution_record)
            session['last_modified'] = datetime.now(timezone.utc).isoformat()
            
            return {
                'status': 'success',
                'execution_result': execution_result,
                'editor_session_id': editor_session_id
            }
            
        except Exception as e:
            log_error(f"Error executing code: {e}")
            raise
    
    async def run_tests(
        self,
        editor_session_id: str,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run test cases against the code"""
        try:
            if editor_session_id not in self._editor_sessions:
                raise ValueError(f"Editor session {editor_session_id} not found")
            
            session = self._editor_sessions[editor_session_id]
            code_to_test = code or session['code']
            language = session['language']
            test_cases = session.get('test_cases', [])
            expected_outputs = session.get('expected_outputs', [])
            
            log_info(f"[CODE EDITOR] Running {len(test_cases)} test cases for session {editor_session_id}")
            
            # Execute code for each test case
            test_results = []
            passed = 0
            failed = 0
            
            for i, test_case in enumerate(test_cases):
                # Modify code to include test case input
                test_code = self._prepare_test_code(code_to_test, test_case, language)
                
                # Execute test
                execution_result = await code_execution_service.execute_code(
                    code=test_code,
                    language=language
                )
                
                # Compare output with expected
                actual_output = execution_result.get('output', '').strip()
                expected_output = expected_outputs[i] if i < len(expected_outputs) else ''
                expected_output = str(expected_output).strip()
                
                is_passed = actual_output == expected_output
                
                if is_passed:
                    passed += 1
                else:
                    failed += 1
                
                test_results.append({
                    'test_case_number': i + 1,
                    'input': test_case,
                    'expected_output': expected_output,
                    'actual_output': actual_output,
                    'passed': is_passed,
                    'error': execution_result.get('error', ''),
                    'execution_time': execution_result.get('execution_time', 0)
                })
            
            # Calculate overall score
            total_tests = len(test_cases)
            score = (passed / total_tests * 100) if total_tests > 0 else 0
            
            result = {
                'status': 'success',
                'editor_session_id': editor_session_id,
                'total_tests': total_tests,
                'passed': passed,
                'failed': failed,
                'score': round(score, 2),
                'test_results': test_results
            }
            
            # Store test results in session
            session['last_test_results'] = result
            session['last_modified'] = datetime.now(timezone.utc).isoformat()
            
            log_info(f"[CODE EDITOR] Test results: {passed}/{total_tests} passed (score: {score:.1f}%)")
            
            return result
            
        except Exception as e:
            log_error(f"Error running tests: {e}")
            raise
    
    def _prepare_test_code(self, code: str, test_input: Any, language: str) -> str:
        """Prepare code with test input for execution"""
        if language == 'python':
            # For Python, assume function takes input as parameter
            return f"{code}\n\n# Test execution\nresult = solution({test_input})\nprint(result)"
        elif language == 'javascript':
            return f"{code}\n\n// Test execution\nconsole.log(solution({test_input}));"
        elif language == 'java':
            # Java requires more complex setup
            return f"{code}\n\n// Test execution\npublic static void main(String[] args) {{\n    System.out.println(solution({test_input}));\n}}"
        else:
            # Default: append test input
            return f"{code}\n\n// Test: {test_input}"
    
    def get_editor_session(self, editor_session_id: str) -> Optional[Dict[str, Any]]:
        """Get editor session details"""
        return self._editor_sessions.get(editor_session_id)
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages"""
        return [
            {
                'key': key,
                'name': info['name'],
                'extension': info['extension'],
                'syntax': info['syntax']
            }
            for key, info in self.supported_languages.items()
        ]
    
    def delete_editor_session(self, editor_session_id: str) -> bool:
        """Delete an editor session"""
        if editor_session_id in self._editor_sessions:
            del self._editor_sessions[editor_session_id]
            log_info(f"[CODE EDITOR] Deleted editor session {editor_session_id}")
            return True
        return False

# Global instance
code_editor_service = CodeEditorService()

