"""
Web Scraper Service for Question Inspiration
Fetches question ideas from LeetCode, GeeksforGeeks, StackOverflow, Kaggle
"""

import requests
import json
from typing import Dict, List, Optional, Any
import re
from urllib.parse import quote

from utils.logger import log_info, log_error

class WebScraperService:
    """Service for scraping coding question ideas from various platforms"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        log_info("[OK] Web Scraper Service initialized")
    
    async def get_leetcode_questions(self, difficulty: str, topic: str = None) -> List[Dict[str, Any]]:
        """Get LeetCode questions (using public API or scraping)"""
        try:
            # LeetCode GraphQL endpoint
            url = "https://leetcode.com/graphql/"
            
            query = """
            query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                problemsetQuestionList: questionList(
                    categorySlug: $categorySlug
                    limit: $limit
                    skip: $skip
                    filters: $filters
                ) {
                    total: totalNum
                    questions: data {
                        acRate
                        difficulty
                        freqBar
                        frontendQuestionId: questionFrontendId
                        isFavor
                        paidOnly: isPaidOnly
                        status
                        title
                        titleSlug
                        topicTags {
                            name
                            id
                            slug
                        }
                        hasSolution
                        hasVideoSolution
                    }
                }
            }
            """
            
            variables = {
                "categorySlug": "",
                "skip": 0,
                "limit": 10,
                "filters": {
                    "difficulty": difficulty.upper() if difficulty else None
                }
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
                
                # Filter by topic if provided
                if topic:
                    questions = [q for q in questions if any(
                        topic.lower() in tag.get("name", "").lower() 
                        for tag in q.get("topicTags", [])
                    )]
                
                return questions[:5]  # Return top 5
            else:
                log_error(f"LeetCode API error: {response.status_code}")
                return []
                
        except Exception as e:
            log_error(f"Error fetching LeetCode questions: {e}")
            return []
    
    async def get_geeksforgeeks_questions(self, difficulty: str, topic: str = None) -> List[Dict[str, Any]]:
        """Get GeeksforGeeks questions"""
        try:
            # GeeksforGeeks search
            search_url = "https://www.geeksforgeeks.org/search/"
            
            if topic:
                search_query = f"{topic} {difficulty} problems"
            else:
                search_query = f"{difficulty} coding problems"
            
            # Use their API or scrape (simplified version)
            # Note: Actual implementation would require proper scraping or API access
            return [
                {
                    "title": f"Sample {difficulty} Problem",
                    "source": "GeeksforGeeks",
                    "difficulty": difficulty,
                    "topic": topic or "general"
                }
            ]
        except Exception as e:
            log_error(f"Error fetching GeeksforGeeks questions: {e}")
            return []
    
    async def get_stackoverflow_questions(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get StackOverflow questions related to coding challenges"""
        try:
            # StackOverflow API
            api_url = "https://api.stackexchange.com/2.3/questions"
            
            params = {
                "order": "desc",
                "sort": "votes",
                "tagged": ";".join(tags[:3]),
                "site": "stackoverflow",
                "pagesize": 5
            }
            
            response = requests.get(api_url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("items", [])
                
                return [
                    {
                        "title": q.get("title", ""),
                        "source": "StackOverflow",
                        "tags": q.get("tags", []),
                        "score": q.get("score", 0)
                    }
                    for q in questions
                ]
            else:
                return []
                
        except Exception as e:
            log_error(f"Error fetching StackOverflow questions: {e}")
            return []
    
    async def get_question_inspiration(
        self,
        difficulty: str,
        topics: List[str],
        skills: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get question inspiration from multiple sources"""
        try:
            inspiration = {
                "leetcode": [],
                "geeksforgeeks": [],
                "stackoverflow": []
            }
            
            # Get from LeetCode
            leetcode_questions = await self.get_leetcode_questions(
                difficulty=difficulty,
                topic=topics[0] if topics else None
            )
            inspiration["leetcode"] = leetcode_questions
            
            # Get from GeeksforGeeks
            geeksforgeeks_questions = await self.get_geeksforgeeks_questions(
                difficulty=difficulty,
                topic=topics[0] if topics else None
            )
            inspiration["geeksforgeeks"] = geeksforgeeks_questions
            
            # Get from StackOverflow
            stackoverflow_questions = await self.get_stackoverflow_questions(
                tags=skills[:3] if skills else ["programming"]
            )
            inspiration["stackoverflow"] = stackoverflow_questions
            
            return inspiration
            
        except Exception as e:
            log_error(f"Error getting question inspiration: {e}")
            return {
                "leetcode": [],
                "geeksforgeeks": [],
                "stackoverflow": []
            }

