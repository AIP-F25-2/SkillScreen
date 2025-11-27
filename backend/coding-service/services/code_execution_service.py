import os
import base64
import asyncio
from typing import List, Dict, Any, Optional

import httpx
from fastapi import HTTPException


class CodeExecutionService:
    def __init__(self):
        self.base_url = os.getenv("JUDGE0_BASE_URL", "https://judge0-ce.p.rapidapi.com")
        self.rapidapi_key = os.getenv("JUDGE0_RAPIDAPI_KEY")
        self.rapidapi_host = os.getenv("JUDGE0_RAPIDAPI_HOST", "judge0-ce.p.rapidapi.com")

        if not self.rapidapi_key:
            raise RuntimeError("JUDGE0_RAPIDAPI_KEY is not set")

    def _headers(self) -> Dict[str, str]:
        return {
            "x-rapidapi-host": self.rapidapi_host,
            "x-rapidapi-key": self.rapidapi_key,
            "content-type": "application/json",
        }

    async def _submit_to_judge0(
        self,
        language_id: int,
        source_code: str,
        stdin: str = "",
    ) -> str:
        """
        Creates a submission and returns the Judge0 token.
        Equivalent to:
          curl --request POST \
               --url 'https://judge0-ce.p.rapidapi.com/submissions?base64_encoded=true&fields=*' ...
        """
        encoded_source = base64.b64encode(source_code.encode()).decode()
        encoded_stdin = base64.b64encode(stdin.encode()).decode()

        payload = {
            "language_id": language_id,
            "source_code": encoded_source,
            "stdin": encoded_stdin,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/submissions?base64_encoded=true&fields=*",
                json=payload,
                headers=self._headers(),
                timeout=20.0,
            )

        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail=f"Judge0 submit error: {resp.status_code}",
            )

        data = resp.json()
        token = data.get("token")
        if not token:
            raise HTTPException(status_code=502, detail="No token returned by Judge0")

        return token

    async def _get_submission(self, token: str) -> Dict[str, Any]:
        """
        Equivalent to the curl you posted:
          curl --request GET \
               --url 'https://judge0-ce.p.rapidapi.com/submissions/{token}?base64_encoded=true&fields=*'
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/submissions/{token}?base64_encoded=true&fields=*",
                headers=self._headers(),
                timeout=20.0,
            )

        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail=f"Judge0 get error: {resp.status_code}",
            )

        return resp.json()

    async def _call_judge0(
        self,
        language_id: int,
        source_code: str,
        stdin: str = "",
        max_attempts: int = 10,
        poll_interval: float = 0.5,
    ) -> Dict[str, Any]:
        """
        High-level wrapper:
          1) POST submission (get token)
          2) Poll GET /submissions/{token} until finished or max_attempts
        """
        token = await self._submit_to_judge0(language_id, source_code, stdin)

        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            data = await self._get_submission(token)
            status = data.get("status", {})
            status_id = status.get("id")
            status_desc = status.get("description")

            # Judge0 status IDs: 1 = In Queue, 2 = Processing, >=3 = finished
            if status_id is not None and status_id >= 3:
                return data

            # Still running, wait and poll again
            await asyncio.sleep(poll_interval)

        # If still not finished after max_attempts, return whatever we have
        return data

    @staticmethod
    def _decode_output(value: Optional[str]) -> str:
        if not value:
            return ""
        try:
            return base64.b64decode(value).decode()
        except Exception:
            return value

    async def run_code(
        self,
        language_id: int,
        source_code: str,
        stdin: str = "",
    ) -> Dict[str, Any]:
        """
        Single execution, no scoring.
        """
        result = await self._call_judge0(
            language_id=language_id,
            source_code=source_code,
            stdin=stdin,
        )

        stdout = self._decode_output(result.get("stdout"))
        stderr = self._decode_output(result.get("stderr"))

        return {
            "status": result["status"]["description"],
            "stdout": stdout,
            "stderr": stderr,
            "time": result.get("time"),
            "memory": result.get("memory"),
        }

    async def evaluate_code(
        self,
        language_id: int,
        source_code: str,
        test_cases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate against multiple test cases with weights.
        test_cases: [{ id, input, expectedOutput, weight }]
        """
        if not test_cases:
            raise HTTPException(status_code=400, detail="No test cases provided")

        total_weight = sum(float(tc.get("weight", 1.0)) for tc in test_cases)
        passed_weight = 0.0
        total_time = 0.0
        detailed_results: List[Dict[str, Any]] = []

        for tc in test_cases:
            tc_id = tc.get("id", "")
            tc_input = tc.get("input", "")
            expected_output = tc.get("expectedOutput", "")
            weight = float(tc.get("weight", 1.0))

            result = await self._call_judge0(
                language_id=language_id,
                source_code=source_code,
                stdin=tc_input,
            )

            status_desc = result["status"]["description"]
            stdout = self._decode_output(result.get("stdout"))
            stderr = self._decode_output(result.get("stderr"))
            time_used = float(result.get("time") or 0.0)
            memory_used = result.get("memory")

            total_time += time_used

            passed = (
                status_desc == "Accepted"
                and stdout.strip() == expected_output.strip()
            )
            if passed:
                passed_weight += weight

            detailed_results.append(
                {
                    "testCaseId": tc_id,
                    "status": status_desc,
                    "passed": passed,
                    "stdout": stdout,
                    "stderr": stderr,
                    "time": time_used,
                    "memory": memory_used,
                }
            )

        score = passed_weight / total_weight if total_weight > 0 else 0.0

        return {
            "score": score,
            "passedWeight": passed_weight,
            "totalWeight": total_weight,
            "totalExecutionTime": total_time,
            "results": detailed_results,
        }
