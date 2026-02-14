"""
LeetCode Integration Service for SkillScreen
Fetches coding questions from LeetCode based on job requirements and candidate skills
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import re
from urllib.parse import quote

from utils.logger import log_info, log_error, log_warning

class LeetCodeService:
    """Service for fetching and managing LeetCode coding questions"""
    
    def __init__(self):
        # LeetCode GraphQL API endpoint
        self.graphql_endpoint = "https://leetcode.com/graphql/"
        self.base_url = "https://leetcode.com"
        
        # Difficulty mapping
        self.difficulty_map = {
            'easy': 'EASY',
            'medium': 'MEDIUM',
            'hard': 'HARD'
        }
        
        # Topic tags mapping (LeetCode tags to our categories)
        self.topic_tags = {
            'array': ['array', 'arrays'],
            'string': ['string', 'strings', 'text processing'],
            'hash-table': ['hash', 'dictionary', 'map'],
            'dynamic-programming': ['dp', 'dynamic programming', 'optimization'],
            'math': ['math', 'mathematics', 'algorithm'],
            'tree': ['tree', 'binary tree', 'data structures'],
            'graph': ['graph', 'graphs', 'networks'],
            'two-pointers': ['two pointers', 'pointers'],
            'binary-search': ['binary search', 'search'],
            'greedy': ['greedy', 'optimization'],
            'backtracking': ['backtracking', 'recursion'],
            'stack': ['stack', 'lifo'],
            'queue': ['queue', 'fifo'],
            'linked-list': ['linked list', 'list'],
            'heap': ['heap', 'priority queue'],
            'sorting': ['sort', 'sorting', 'algorithm'],
            'bit-manipulation': ['bit', 'bitwise', 'binary'],
            'sliding-window': ['sliding window', 'window'],
            'trie': ['trie', 'prefix tree'],
            'union-find': ['union find', 'disjoint set']
        }
        
        log_info("✅ LeetCode Service initialized")
    
    async def fetch_question_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific LeetCode question by slug"""
        try:
            query = """
            query questionContent($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    questionFrontendId
                    title
                    titleSlug
                    content
                    difficulty
                    likes
                    dislikes
                    isLiked
                    similarQuestions
                    contributors {
                        username
                        profileUrl
                        avatarUrl
                        __typename
                    }
                    topicTags {
                        name
                        slug
                        translatedName
                        __typename
                    }
                    companyTagStats
                    codeSnippets {
                        lang
                        langSlug
                        code
                        __typename
                    }
                    stats
                    hints
                    solution {
                        id
                        canSeeDetail
                        paidOnly
                        __typename
                    }
                    status
                    sampleTestCase
                    metaData
                    judgerAvailable
                    judgeType
                    mysqlSchemas
                    enableRunCode
                    enableTestMode
                    enableDebugger
                    envInfo
                    libraryUrl
                    adminUrl
                    __typename
                }
            }
            """
            
            variables = {"titleSlug": slug}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_endpoint,
                    json={"query": query, "variables": variables},
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    },
                    timeout=10.0
                )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'question' in data['data']:
                    question = data['data']['question']
                    return self._format_question(question)
            
            log_warning(f"Failed to fetch question {slug}: {response.status_code}")
            return None
            
        except Exception as e:
            log_error(f"Error fetching LeetCode question: {e}")
            return None
    
    async def search_questions(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]: # nosonar
        """Search for LeetCode questions by difficulty and tags"""
        try:
            # LeetCode doesn't have a public search API, so we'll use a curated list
            # In production, you might want to maintain a local database of LeetCode questions
            
            # For now, return a curated list based on common interview questions
            curated_questions = self._get_curated_questions(difficulty, tags, limit)
            
            return curated_questions
            
        except Exception as e:
            log_error(f"Error searching LeetCode questions: {e}")
            return []
    
    async def get_question_by_requirements(
        self,
        job_skills: List[str],
        candidate_skills: List[str],
        difficulty: str = 'medium',
        question_type: str = 'algorithm'
    ) -> Optional[Dict[str, Any]]:
        """Get a coding question based on job requirements and candidate skills"""
        try:
            # Map skills to LeetCode topics
            relevant_topics = self._map_skills_to_topics(job_skills + candidate_skills)
            
            # Search for questions matching the topics and difficulty
            questions = await self.search_questions(
                difficulty=difficulty,
                tags=relevant_topics,
                limit=20
            )
            
            if questions:
                # Select a question (could add more sophisticated selection logic)
                import random
                selected = random.choice(questions)
                return selected
            
            # Fallback to a generic question
            return await self._get_fallback_question(difficulty, question_type)
            
        except Exception as e:
            log_error(f"Error getting question by requirements: {e}")
            return await self._get_fallback_question(difficulty, question_type)
    
    def _map_skills_to_topics(self, skills: List[str]) -> List[str]:
        """Map candidate/job skills to LeetCode topic tags"""
        topics = set()
        
        skills_lower = [s.lower() for s in skills]
        
        for skill in skills_lower:
            for tag, keywords in self.topic_tags.items():
                if any(keyword in skill for keyword in keywords):
                    topics.add(tag)
        
        # Default topics if no match
        if not topics:
            topics = {'array', 'string', 'hash-table'}
        
        return list(topics)
    
    def _format_question(self, question_data: Dict) -> Dict[str, Any]:
        """Format LeetCode question data into our format"""
        try:
            # Extract code snippets
            code_snippets = {}
            if 'codeSnippets' in question_data:
                for snippet in question_data['codeSnippets']:
                    code_snippets[snippet['langSlug']] = snippet['code']
            
            # Extract topic tags
            topics = []
            if 'topicTags' in question_data:
                topics = [tag['name'] for tag in question_data['topicTags']]
            
            # Parse content to extract problem description
            content = question_data.get('content', '')
            description = self._extract_description(content)
            
            # Extract examples from content
            examples = self._extract_examples(content)
            
            return {
                'leetcode_id': question_data.get('questionFrontendId', ''),
                'title': question_data.get('title', ''),
                'slug': question_data.get('titleSlug', ''),
                'difficulty': question_data.get('difficulty', 'MEDIUM').lower(),
                'description': description,
                'examples': examples,
                'topics': topics,
                'code_templates': code_snippets,
                'constraints': self._extract_constraints(content),
                'source': 'leetcode',
                'url': f"{self.base_url}/problems/{question_data.get('titleSlug', '')}"
            }
            
        except Exception as e:
            log_error(f"Error formatting question: {e}")
            return {}
    
    def _extract_description(self, content: str) -> str:
        """Extract problem description from HTML content"""
        try:
            # Remove HTML tags
            import re
            text = re.sub(r'<[^>]+>', '', content)
            # Remove extra whitespace
            text = ' '.join(text.split())
            # Get first paragraph (usually the description)
            paragraphs = text.split('\n\n')
            return paragraphs[0] if paragraphs else text[:500]
        except Exception:
            return content[:500] if content else ""
    
    def _extract_examples(self, content: str) -> List[Dict[str, Any]]:
        """Extract examples from problem content"""
        examples = []
        try:
            # Look for example patterns in HTML
            example_pattern = r'<strong>Example \d+:</strong>'
            matches = re.finditer(example_pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Extract example text (simplified)
                start = match.end()
                end = content.find('<strong>', start)
                if end == -1:
                    end = len(content)
                
                example_text = content[start:end]
                example_text = re.sub(r'<[^>]+>', '', example_text)
                
                # Try to extract input/output
                input_match = re.search(r'Input[:\s]+([^\n]+)', example_text, re.IGNORECASE)
                output_match = re.search(r'Output[:\s]+([^\n]+)', example_text, re.IGNORECASE)
                
                examples.append({
                    'input': input_match.group(1) if input_match else '',
                    'output': output_match.group(1) if output_match else '',
                    'explanation': example_text
                })
        except Exception as e:
            log_warning(f"Error extracting examples: {e}")
        
        return examples if examples else [
            {'input': 'Example input', 'output': 'Example output', 'explanation': 'Example explanation'}
        ]
    
    def _extract_constraints(self, content: str) -> List[str]:
        """Extract constraints from problem content"""
        constraints = []
        try:
            constraint_pattern = r'<li>([^<]+)</li>'
            matches = re.findall(constraint_pattern, content)
            constraints = [m.strip() for m in matches[:10]]  # Limit to 10
        except Exception:
            pass
        
        return constraints if constraints else [
            '1 <= n <= 10^4',
            'All values are unique'
        ]
    
    def _get_curated_questions(
        self,
        difficulty: Optional[str],
        tags: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get curated list of common interview questions"""
        
        # Curated list of popular LeetCode questions
        curated = [
            {
                'leetcode_id': '1',
                'title': 'Two Sum',
                'slug': 'two-sum',
                'difficulty': 'easy',
                'topics': ['array', 'hash-table'],
                'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.'
            },
            {
                'leetcode_id': '2',
                'title': 'Add Two Numbers',
                'slug': 'add-two-numbers',
                'difficulty': 'medium',
                'topics': ['linked-list', 'math'],
                'description': 'You are given two non-empty linked lists representing two non-negative integers. Add them and return the sum as a linked list.'
            },
            {
                'leetcode_id': '3',
                'title': 'Longest Substring Without Repeating Characters',
                'slug': 'longest-substring-without-repeating-characters',
                'difficulty': 'medium',
                'topics': ['string', 'sliding-window', 'hash-table'],
                'description': 'Given a string s, find the length of the longest substring without repeating characters.'
            },
            {
                'leetcode_id': '20',
                'title': 'Valid Parentheses',
                'slug': 'valid-parentheses',
                'difficulty': 'easy',
                'topics': ['stack', 'string'],
                'description': 'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.'
            },
            {
                'leetcode_id': '21',
                'title': 'Merge Two Sorted Lists',
                'slug': 'merge-two-sorted-lists',
                'difficulty': 'easy',
                'topics': ['linked-list', 'recursion'],
                'description': 'Merge two sorted linked lists and return it as a sorted list.'
            },
            {
                'leetcode_id': '53',
                'title': 'Maximum Subarray',
                'slug': 'maximum-subarray',
                'difficulty': 'easy',
                'topics': ['array', 'dynamic-programming'],
                'description': 'Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.'
            },
            {
                'leetcode_id': '121',
                'title': 'Best Time to Buy and Sell Stock',
                'slug': 'best-time-to-buy-and-sell-stock',
                'difficulty': 'easy',
                'topics': ['array', 'dynamic-programming'],
                'description': 'You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.'
            },
            {
                'leetcode_id': '206',
                'title': 'Reverse Linked List',
                'slug': 'reverse-linked-list',
                'difficulty': 'easy',
                'topics': ['linked-list', 'recursion'],
                'description': 'Reverse a singly linked list.'
            },
            {
                'leetcode_id': '217',
                'title': 'Contains Duplicate',
                'slug': 'contains-duplicate',
                'difficulty': 'easy',
                'topics': ['array', 'hash-table'],
                'description': 'Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.'
            },
            {
                'leetcode_id': '238',
                'title': 'Product of Array Except Self',
                'slug': 'product-of-array-except-self',
                'difficulty': 'medium',
                'topics': ['array', 'prefix-sum'],
                'description': 'Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].'
            }
        ]
        
        # Filter by difficulty
        if difficulty:
            difficulty_lower = difficulty.lower()
            curated = [q for q in curated if q['difficulty'] == difficulty_lower]
        
        # Filter by tags (if any question has matching tag)
        if tags:
            curated = [
                q for q in curated
                if any(tag in q.get('topics', []) for tag in tags)
            ]
        
        # Limit results
        return curated[:limit]
    
    async def _get_fallback_question( # nosonar
        self,
        difficulty: str,
        question_type: str
    ) -> Dict[str, Any]:
        """Get a fallback question if LeetCode fetch fails"""
        return {
            'leetcode_id': 'fallback',
            'title': f'{difficulty.title()} Coding Challenge',
            'slug': 'fallback-question',
            'difficulty': difficulty.lower(),
            'description': f'Write a function to solve the given problem. This is a {difficulty} level {question_type} question.',
            'topics': ['algorithm'],
            'examples': [
                {'input': 'Example input', 'output': 'Example output', 'explanation': 'Example explanation'}
            ],
            'constraints': ['1 <= n <= 10^4'],
            'code_templates': {
                'python': 'def solution():\n    # Your code here\n    pass',
                'javascript': 'function solution() {\n    // Your code here\n}',
                'java': 'class Solution {\n    public void solution() {\n        // Your code here\n    }\n}'
            },
            'source': 'fallback',
            'url': ''
        }

# Global instance
leetcode_service = LeetCodeService()

