"""Stats tracking for RAG system evaluation - unified stats system."""

import json
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class QueryStats:
    """Stats for a single query."""
    session_id: str
    query: str
    timestamp: str
    inference_time: float
    token_in: int
    token_out: int
    char_truncated: int
    total_context_truncated: int
    rag_time: float
    internet_search_used: bool
    top_k: int
    top_score: float
    num_sources: int
    use_query_expansion: bool
    use_rag: bool


class Stats:
    """Global unified stats tracker - single source of truth."""
    
    def __init__(self, storage_path: str = "data/stats"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Global stats file
        self.global_stats_file = self.storage_path / "global.json"
        # Queries log
        self.queries_file = self.storage_path / "queries.jsonl"
        # Sessions file
        self.sessions_file = self.storage_path / "sessions.json"
        
        self._load_global()
    
    def _load_global(self):
        """Load global stats from file."""
        if self.global_stats_file.exists():
            try:
                with open(self.global_stats_file, "r") as f:
                    data = json.load(f)
                    self.total_queries = data.get("total_queries", 0)
                    self.total_inference_time = data.get("total_inference_time", 0)
                    self.total_token_in = data.get("total_token_in", 0)
                    self.total_token_out = data.get("total_token_out", 0)
                    self.total_char_truncated = data.get("total_char_truncated", 0)
                    self.total_context_truncated = data.get("total_context_truncated", 0)
                    self.total_rag_time = data.get("total_rag_time", 0)
                    self.internet_search_count = data.get("internet_search_count", 0)
                    self.avg_top_score = data.get("avg_top_score", 0)
                    self.sessions = data.get("sessions", {})
            except Exception:
                self._init_global()
        else:
            self._init_global()
    
    def _init_global(self):
        """Initialize global stats."""
        self.total_queries = 0
        self.total_inference_time = 0
        self.total_token_in = 0
        self.total_token_out = 0
        self.total_char_truncated = 0
        self.total_context_truncated = 0
        self.total_rag_time = 0
        self.internet_search_count = 0
        self.avg_top_score = 0
        self.sessions = {}
    
    def _save_global(self):
        """Save global stats to file."""
        with open(self.global_stats_file, "w") as f:
            json.dump({
                "total_queries": self.total_queries,
                "total_inference_time": round(self.total_inference_time, 2),
                "total_token_in": self.total_token_in,
                "total_token_out": self.total_token_out,
                "total_char_truncated": self.total_char_truncated,
                "total_context_truncated": self.total_context_truncated,
                "total_rag_time": round(self.total_rag_time, 2),
                "internet_search_count": self.internet_search_count,
                "avg_top_score": round(self.avg_top_score, 4),
                "sessions": self.sessions,
            }, f, indent=2)
    
    def add_query(self, stats: QueryStats):
        """Add a query to stats - updates both global and session."""
        # Update global
        self.total_queries += 1
        self.total_inference_time += stats.inference_time
        self.total_token_in += stats.token_in
        self.total_token_out += stats.token_out
        self.total_char_truncated += stats.char_truncated
        self.total_context_truncated += stats.total_context_truncated
        self.total_rag_time += stats.rag_time
        
        if stats.internet_search_used:
            self.internet_search_count += 1
        
        # Update avg top score
        self.avg_top_score = (
            (self.avg_top_score * (self.total_queries - 1) + stats.top_score) 
            / self.total_queries
        )
        
        # Update session stats
        if stats.session_id not in self.sessions:
            self.sessions[stats.session_id] = {
                "created_at": stats.timestamp,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "query_count": 0,
                "total_top_score": 0,
            }
        
        session = self.sessions[stats.session_id]
        session["total_input_tokens"] += stats.token_in
        session["total_output_tokens"] += stats.token_out
        session["query_count"] += 1
        session["total_top_score"] += stats.top_score
        session["last_query"] = stats.timestamp
        
        self._save_global()
        
        # Save query to file
        with open(self.queries_file, "a") as f:
            f.write(json.dumps(asdict(stats)) + "\n")
    
    def get_global(self) -> Dict:
        """Get global stats."""
        return {
            "total_queries": self.total_queries,
            "total_inference_time": round(self.total_inference_time, 2),
            "avg_inference_time": round(self.total_inference_time / max(self.total_queries, 1), 2),
            "total_token_in": self.total_token_in,
            "total_token_out": self.total_token_out,
            "total_tokens": self.total_token_in + self.total_token_out,
            "avg_token_in": round(self.total_token_in / max(self.total_queries, 1)),
            "avg_token_out": round(self.total_token_out / max(self.total_queries, 1)),
            "total_char_truncated": self.total_char_truncated,
            "total_context_truncated": self.total_context_truncated,
            "total_rag_time": round(self.total_rag_time, 2),
            "avg_rag_time": round(self.total_rag_time / max(self.total_queries, 1), 2),
            "internet_search_count": self.internet_search_count,
            "internet_search_rate": round(self.internet_search_count / max(self.total_queries, 1) * 100, 1),
            "avg_top_score": round(self.avg_top_score, 4),
            "total_sessions": len(self.sessions),
        }
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get stats for a specific session."""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "created_at": session.get("created_at", ""),
            "total_queries": session.get("query_count", 0),
            "total_input_tokens": session.get("total_input_tokens", 0),
            "total_output_tokens": session.get("total_output_tokens", 0),
            "total_tokens": session.get("total_input_tokens", 0) + session.get("total_output_tokens", 0),
            "avg_top_score": round(
                session.get("total_top_score", 0) / max(session.get("query_count", 1), 1
            ), 4),
            "last_query": session.get("last_query", ""),
        }
    
    def get_all_sessions(self) -> List[Dict]:
        """Get summary of all sessions."""
        return [
            self.get_session_stats(sid)
            for sid in self.sessions.keys()
        ]
    
    def get_recent_queries(self, n: int = 10) -> List[Dict]:
        """Get N most recent queries."""
        queries = []
        if self.queries_file.exists():
            with open(self.queries_file, "r") as f:
                for line in f:
                    queries.append(json.loads(line))
        
        return queries[-n:][::-1]
    
    def get_metrics_for_dashboard(self) -> Dict:
        """Get all metrics for dashboard display."""
        global_stats = self.get_global()
        
        # Get recent trends
        recent = self.get_recent_queries(20)
        if recent:
            recent_inference = [q["inference_time"] for q in recent]
            recent_tokens = [q["token_in"] + q["token_out"] for q in recent]
            recent_scores = [q["top_score"] for q in recent]
        else:
            recent_inference = []
            recent_tokens = []
            recent_scores = []
        
        return {
            "global": global_stats,
            "trends": {
                "avg_inference_time_last_20": round(np.mean(recent_inference), 2) if recent_inference else 0,
                "avg_tokens_last_20": round(np.mean(recent_tokens)) if recent_tokens else 0,
                "avg_score_last_20": round(np.mean(recent_scores), 4) if recent_scores else 0,
            },
            "recent_queries": recent[:5],
        }
    def __str__(self) -> str:
        return "Stats()"

