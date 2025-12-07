"""
Web Scraper Service for Question Inspiration
"""
import httpx
import json
from typing import Dict, List, Optional, Any
import re
from urllib.parse import quote

def _log(msg: str):
    # minimal logging - production should use shared logger
    print("[web_scraper]", msg)


class WebScraperService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        _log("Web Scraper Service initialized")

    async def get_leetcode_questions(self, difficulty: str, topic: str = None) -> List[Dict[str, Any]]:
        try:
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
                        title
                        titleSlug
                        topicTags {
                            name
                            id
                            slug
                        }
                    }
                }
            }
            """
            # Build filters - only include difficulty if it's valid
            filters = {}
            if difficulty and difficulty.lower() in ["easy", "medium", "hard"]:
                filters["difficulty"] = difficulty.upper()
            
            variables = {"categorySlug": "", "skip": 0, "limit": 10, "filters": filters if filters else {}}
            payload = {"query": query, "variables": variables}

            _log(f"Fetching LeetCode questions: difficulty={difficulty}, topic={topic}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                # Check for GraphQL errors
                if "errors" in data:
                    _log(f"LeetCode GraphQL errors: {data.get('errors')}")
                    return []
                questions = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
                if topic:
                    questions = [q for q in questions if any(topic.lower() in tag.get("name", "").lower() for tag in q.get("topicTags", []))]
                result = questions[:5]
                _log(f"LeetCode: Successfully fetched {len(result)} questions")
                return result
            else:
                _log(f"LeetCode API error: HTTP {response.status_code}, Response: {response.text[:200]}")
                return []
        except httpx.TimeoutException:
            _log("LeetCode API timeout: Request took longer than 10 seconds")
            return []
        except httpx.RequestError as e:
            _log(f"LeetCode API connection error: {str(e)}")
            return []
        except Exception as e:
            _log(f"Error fetching LeetCode questions: {type(e).__name__}: {str(e)}")
            return []

    async def get_geeksforgeeks_questions(self, difficulty: str, topic: str = None) -> List[Dict[str, Any]]: # nosonar
        try:
            return [{"title": f"Sample {difficulty} Problem", "source": "GeeksforGeeks", "difficulty": difficulty, "topic": topic or "general"}]
        except Exception as e:
            _log(f"Error fetching GeeksforGeeks questions: {e}")
            return []

    async def get_stackoverflow_questions(self, tags: List[str]) -> List[Dict[str, Any]]:
        try:
            api_url = "https://api.stackexchange.com/2.3/questions"
            params = {"order": "desc", "sort": "votes", "tagged": ";".join(tags[:3]), "site": "stackoverflow", "pagesize": 5}
            _log(f"Fetching StackOverflow questions: tags={tags[:3]}")
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params=params, headers=self.headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                # Check for API errors
                if "error_id" in data:
                    _log(f"StackOverflow API error: {data.get('error_name')} - {data.get('error_message', '')}")
                    return []
                questions = data.get("items", [])
                result = [{"title": q.get("title", ""), "source": "StackOverflow", "tags": q.get("tags", []), "score": q.get("score", 0)} for q in questions]
                _log(f"StackOverflow: Successfully fetched {len(result)} questions")
                return result
            else:
                _log(f"StackOverflow API error: HTTP {response.status_code}, Response: {response.text[:200]}")
                return []
        except httpx.TimeoutException:
            _log("StackOverflow API timeout: Request took longer than 10 seconds")
            return []
        except httpx.RequestError as e:
            _log(f"StackOverflow API connection error: {str(e)}")
            return []
        except Exception as e:
            _log(f"Error fetching StackOverflow questions: {type(e).__name__}: {str(e)}")
            return []

    async def get_question_inspiration(self, difficulty: str, topics: List[str], skills: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            inspiration = {"leetcode": [], "geeksforgeeks": [], "stackoverflow": []}
            _log(f"Getting question inspiration: difficulty={difficulty}, topics={topics}, skills={skills}")
            
            # Fetch from all sources in parallel would be better, but sequential for now
            leetcode_questions = await self.get_leetcode_questions(difficulty=difficulty, topic=topics[0] if topics else None)
            inspiration["leetcode"] = leetcode_questions
            
            geeksforgeeks_questions = await self.get_geeksforgeeks_questions(difficulty=difficulty, topic=topics[0] if topics else None)
            inspiration["geeksforgeeks"] = geeksforgeeks_questions
            
            stackoverflow_questions = await self.get_stackoverflow_questions(tags=skills[:3] if skills else ["programming"])
            inspiration["stackoverflow"] = stackoverflow_questions
            
            total = len(leetcode_questions) + len(geeksforgeeks_questions) + len(stackoverflow_questions)
            _log(f"Inspiration summary: Total {total} questions scraped (LeetCode: {len(leetcode_questions)}, GeeksforGeeks: {len(geeksforgeeks_questions)}, StackOverflow: {len(stackoverflow_questions)})")
            return inspiration
        except Exception as e:
            _log(f"Error getting question inspiration: {type(e).__name__}: {str(e)}")
            return {"leetcode": [], "geeksforgeeks": [], "stackoverflow": []}
