import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from difflib import SequenceMatcher

from app.models.incident import Incident, IncidentStatus
from app.db.base import BaseRepository

logger = logging.getLogger(__name__)

class IncidentDeduplicator:
    def __init__(self, similarity_threshold: float = 0.8, time_window_hours: int = 24):
        self.similarity_threshold = similarity_threshold
        self.time_window = timedelta(hours=time_window_hours)
    
    async def find_similar_incidents(
        self, 
        new_incident: Incident, 
        incident_repo: BaseRepository
    ) -> Optional[str]:
        """Find existing similar incidents within time window"""
        
        # Get recent open incidents
        cutoff_time = datetime.utcnow() - self.time_window
        recent_incidents = await self._get_recent_incidents(incident_repo, cutoff_time)
        
        best_match = None
        best_score = 0
        
        for incident in recent_incidents:
            score = self._calculate_similarity(new_incident, incident)
            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = incident.id
                
        if best_match:
            logger.info(f"🔗 Found similar incident {best_match} (similarity: {best_score:.2f})")
            
        return best_match
    
    def _calculate_similarity(self, incident1: Incident, incident2: Incident) -> float:
        """Calculate similarity score between two incidents"""
        
        # Title similarity (weighted 40%)
        title_sim = SequenceMatcher(None, incident1.title.lower(), incident2.title.lower()).ratio()
        
        # Summary similarity (weighted 30%)
        summary_sim = SequenceMatcher(None, incident1.summary.lower(), incident2.summary.lower()).ratio()
        
        # Tag overlap (weighted 20%)
        tags1 = set(incident1.tags or [])
        tags2 = set(incident2.tags or [])
        tag_sim = len(tags1.intersection(tags2)) / max(len(tags1.union(tags2)), 1)
        
        # Severity match (weighted 10%)
        severity_sim = 1.0 if incident1.severity == incident2.severity else 0.5
        
        total_score = (title_sim * 0.4) + (summary_sim * 0.3) + (tag_sim * 0.2) + (severity_sim * 0.1)
        
        return total_score
    
    async def _get_recent_incidents(self, incident_repo: BaseRepository, cutoff_time: datetime) -> List[Incident]:
        """Get recent open incidents for comparison"""
        try:
            # This would need to be implemented in the repository
            # For now, return empty list - implement based on your DB query capabilities
            return []
        except Exception as e:
            logger.error(f"Error fetching recent incidents: {e}")
            return []

# Global instance
deduplicator = IncidentDeduplicator()