import numpy as np
from sklearn.cluster import DBSCAN
from typing import List, Dict, Any

class AnalysisService:
    
    @staticmethod
    def calculate_score(
        traffic: float,
        competition_density: float,
        demand: float,
        access: float,
        synergy: float
    ) -> float:
        """
        Calculates the suitability score for a location.
        Formula: Score = (Traffic * 0.3) + (LowComp * 0.25) + (Demand * 0.2) + (Access * 0.15) + (Synergy * 0.1)
        
        Note: 'LowComp' implies that lower competition density is better. 
        We will invert the competition density (normalized) to get 'LowComp'.
        For this prototype, we assume inputs are already normalized 0-10 or 0-1.
        Let's assume inputs are 0-10.
        """
        
        # Invert competition to get "Low Competition" score (Higher is better)
        # Assuming max density score is 10.
        low_comp = max(0, 10 - competition_density)
        
        score = (
            (traffic * 0.3) +
            (low_comp * 0.25) +
            (demand * 0.2) +
            (access * 0.15) +
            (synergy * 0.1)
        )
        
        return round(score, 2)

    @staticmethod
    def cluster_competitors(locations: List[List[float]], eps_km: float = 0.5, min_samples: int = 3) -> Dict[str, Any]:
        """
        Performs DBSCAN clustering on competitor locations.
        
        Args:
            locations: List of [lat, lon] coordinates.
            eps_km: The maximum distance between two samples for one to be considered as in the neighborhood of the other.
            min_samples: The number of samples (or total weight) in a neighborhood for a point to be considered as a core point.
            
        Returns:
            Dict containing cluster labels and centroids.
        """
        if not locations:
            return {"clusters": [], "noise": []}
            
        # Convert km to radians for use with haversine metric
        # Earth radius approx 6371 km
        kms_per_radian = 6371.0088
        eps_rad = eps_km / kms_per_radian
        
        # DBSCAN with haversine metric (expects radians)
        # Scikit-learn expects [lat, lon] in radians for haversine
        coords_rad = np.radians(locations)
        
        db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric='haversine', algorithm='ball_tree').fit(coords_rad)
        
        labels = db.labels_
        
        # Process results
        clusters = {}
        noise = []
        
        for idx, label in enumerate(labels):
            point = locations[idx] # [lat, lon]
            if label == -1:
                noise.append(point)
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(point)
                
        # Calculate centroids for clusters
        cluster_summaries = []
        for label, points in clusters.items():
            points_np = np.array(points)
            centroid = np.mean(points_np, axis=0).tolist()
            cluster_summaries.append({
                "cluster_id": int(label),
                "centroid": centroid,
                "count": len(points),
                "points": points
            })
            
        return {
            "clusters": cluster_summaries,
            "noise": noise
        }
