import re
from typing import Dict, List, Tuple
from config import logger


class FillerDetectionService:
    """Detects filler words in transcripts with timestamps"""
    
    # Common filler words and phrases
    FILLER_PATTERNS = {
        "um": r"\bum+\b",
        "uh": r"\buh+\b",
        "er": r"\ber+\b",
        "ah": r"\bah+\b",
        "like": r"\blike\b",
        "you know": r"\byou know\b",
        "sort of": r"\bsort of\b",
        "kind of": r"\bkind of\b",
        "basically": r"\bbasically\b",
        "actually": r"\bactually\b",
        "literally": r"\bliterally\b",
        "I mean": r"\bI mean\b",
        "right": r"\bright\b(?=\s|$)",  # Only standalone "right"
        "well": r"^well\b|\bwell,",  # "well" at start or before comma
        "so": r"^so\b|\bso,",  # "so" at start or before comma
    }
    
    def __init__(self):
        pass
    
    def detect_from_words(self, words: List[Dict]) -> Dict:
        """
        Detect fillers from word-level transcript
        
        Args:
            words: List of word dictionaries with 'word', 'start', 'end', 'probability'
        
        Returns:
            Dictionary with filler analysis
        """
        filler_results = {}
        total_fillers = 0
        
        for filler_type, pattern in self.FILLER_PATTERNS.items():
            filler_results[filler_type] = {
                "count": 0,
                "timestamps": []
            }
        
        # Check each word against filler patterns
        for word_data in words:
            word_text = word_data.get("word", "").strip().lower()
            start_time = word_data.get("start", 0.0)
            end_time = word_data.get("end", 0.0)
            
            # Check against each filler pattern
            for filler_type, pattern in self.FILLER_PATTERNS.items():
                if re.search(pattern, word_text, re.IGNORECASE):
                    filler_results[filler_type]["count"] += 1
                    filler_results[filler_type]["timestamps"].append({
                        "start": start_time,
                        "end": end_time,
                        "text": word_text
                    })
                    total_fillers += 1
        
        # Remove fillers with zero count for cleaner output
        filler_results = {k: v for k, v in filler_results.items() if v["count"] > 0}
        
        return {
            "filler_words": filler_results,
            "total_fillers": total_fillers
        }
    
    def detect_from_text(self, text: str, segments: List[Dict]) -> Dict:
        """
        Detect fillers from full transcript text with segments
        Fallback method if word-level timestamps not available
        
        Args:
            text: Full transcript text
            segments: Segment-level data with timestamps
        
        Returns:
            Dictionary with filler analysis
        """
        filler_results = {}
        total_fillers = 0
        
        for filler_type, pattern in self.FILLER_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            count = sum(1 for _ in re.finditer(pattern, text, re.IGNORECASE))
            
            if count > 0:
                filler_results[filler_type] = {
                    "count": count,
                    "timestamps": []  # Would need segment mapping for timestamps
                }
                total_fillers += count
        
        return {
            "filler_words": filler_results,
            "total_fillers": total_fillers
        }
    
    def calculate_filler_rate(self, total_fillers: int, duration_seconds: float) -> float:
        """
        Calculate fillers per minute
        
        Args:
            total_fillers: Total number of filler words
            duration_seconds: Audio duration in seconds
        
        Returns:
            Fillers per minute
        """
        if duration_seconds <= 0:
            return 0.0
        
        duration_minutes = duration_seconds / 60.0
        return round(total_fillers / duration_minutes, 2)
    
    def get_filler_summary(self, filler_results: Dict, duration_seconds: float) -> Dict:
        """
        Get summary statistics of filler usage
        
        Returns:
            Summary dictionary
        """
        total_fillers = filler_results.get("total_fillers", 0)
        filler_rate = self.calculate_filler_rate(total_fillers, duration_seconds)
        
        # Sort fillers by count
        filler_words = filler_results.get("filler_words", {})
        sorted_fillers = sorted(
            filler_words.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        return {
            "total_fillers": total_fillers,
            "filler_rate_per_minute": filler_rate,
            "most_common_fillers": [
                {"type": k, "count": v["count"]} 
                for k, v in sorted_fillers[:5]
            ],
            "filler_percentage": 0.0  # Will calculate with word count
        }