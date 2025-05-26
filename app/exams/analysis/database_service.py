import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from .models import AlgorithmRunResult, AlgorithmComparison, ExamMetrics
import logging

logger = logging.getLogger(__name__)

class ExamEvaluationDatabaseService:
    """Service for storing and retrieving exam algorithm evaluation results"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection_name = "exam_algorithm_runs"
        self.comparison_collection_name = "exam_algorithm_comparisons"
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            # Use the same MongoDB URI as the main app
            mongodb_uri = "mongodb+srv://ivCodes:doNF7RbKedWTtB5S@timetablewiz-cluster.6pnyt.mongodb.net/?retryWrites=true&w=majority&appName=TimeTableWiz-Cluster"
            database_name = "time_table_whiz"
            
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.database = self.client[database_name]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {database_name}")
            
            # Create indexes for better performance
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Index on algorithm_name and run_timestamp for efficient queries
            await self.database[self.collection_name].create_index([
                ("algorithm_name", 1),
                ("run_timestamp", -1)
            ])
            
            # Index on metrics for ranking queries
            await self.database[self.collection_name].create_index([
                ("metrics.proximity_penalty", 1),
                ("metrics.efficiency_score", -1)
            ])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def store_algorithm_run(self, result: AlgorithmRunResult) -> str:
        """Store an algorithm run result and return the document ID"""
        try:
            # Convert to dict for MongoDB storage
            result_dict = result.dict(by_alias=True, exclude_unset=True)
            
            # Insert into database
            insert_result = await self.database[self.collection_name].insert_one(result_dict)
            
            logger.info(f"Stored algorithm run result for {result.algorithm_name} with ID: {insert_result.inserted_id}")
            return str(insert_result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store algorithm run result: {e}")
            raise
    
    async def get_algorithm_runs(self, 
                               algorithm_name: Optional[str] = None,
                               limit: int = 50,
                               sort_by: str = "run_timestamp",
                               sort_order: int = -1) -> List[Dict[str, Any]]:
        """Retrieve algorithm runs with optional filtering"""
        try:
            # Build query filter
            query_filter = {}
            if algorithm_name:
                query_filter["algorithm_name"] = algorithm_name
            
            # Execute query
            cursor = self.database[self.collection_name].find(query_filter)
            cursor = cursor.sort(sort_by, sort_order).limit(limit)
            
            results = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                result["_id"] = str(result["_id"])
            
            logger.info(f"Retrieved {len(results)} algorithm runs")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve algorithm runs: {e}")
            raise
    
    async def get_algorithm_comparison(self, run_ids: List[str]) -> Dict[str, Any]:
        """Get or create a comparison between multiple algorithm runs"""
        try:
            # First, retrieve the runs
            runs = []
            for run_id in run_ids:
                run = await self.database[self.collection_name].find_one({"_id": run_id})
                if run:
                    run["_id"] = str(run["_id"])
                    runs.append(run)
            
            if not runs:
                raise ValueError("No valid runs found for comparison")
            
            # Create comparison analysis
            comparison_data = self._analyze_runs_comparison(runs)
            
            # Store comparison result
            comparison = AlgorithmComparison(
                run_ids=run_ids,
                **comparison_data
            )
            
            comparison_dict = comparison.dict(by_alias=True, exclude_unset=True)
            await self.database[self.comparison_collection_name].insert_one(comparison_dict)
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"Failed to create algorithm comparison: {e}")
            raise
    
    def _analyze_runs_comparison(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze and compare multiple algorithm runs"""
        if not runs:
            return {}
        
        # Sort by different metrics
        proximity_ranking = sorted(runs, key=lambda x: x["metrics"]["proximity_penalty"])
        efficiency_ranking = sorted(runs, key=lambda x: x["metrics"]["efficiency_score"], reverse=True)
        
        # Calculate overall ranking (weighted combination)
        for run in runs:
            metrics = run["metrics"]
            # Simple weighted score (lower is better for proximity, higher is better for efficiency)
            overall_score = (
                -metrics["proximity_penalty"] * 0.4 +  # Negative because lower is better
                metrics["efficiency_score"] * 0.3 +
                -metrics["student_load_variance"] * 0.2 +  # Negative because lower is better
                metrics["slot_utilization"] * 0.1
            )
            run["overall_score"] = overall_score
        
        overall_ranking = sorted(runs, key=lambda x: x["overall_score"], reverse=True)
        
        # Prepare ranking data
        def format_ranking(ranked_runs):
            return [
                {
                    "algorithm_name": run["algorithm_name"],
                    "run_id": run["_id"],
                    "score": run["metrics"]["proximity_penalty"] if "proximity_penalty" in run["metrics"] else 0,
                    "rank": idx + 1
                }
                for idx, run in enumerate(ranked_runs)
            ]
        
        best_run = overall_ranking[0]
        worst_run = overall_ranking[-1]
        
        return {
            "proximity_ranking": format_ranking(proximity_ranking),
            "efficiency_ranking": format_ranking(efficiency_ranking),
            "overall_ranking": [
                {
                    "algorithm_name": run["algorithm_name"],
                    "run_id": run["_id"],
                    "overall_score": run["overall_score"],
                    "rank": idx + 1
                }
                for idx, run in enumerate(overall_ranking)
            ],
            "best_algorithm": best_run["algorithm_name"],
            "worst_algorithm": worst_run["algorithm_name"],
            "performance_gap": best_run["overall_score"] - worst_run["overall_score"]
        }
    
    async def get_algorithm_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about algorithm performance"""
        try:
            # Aggregate statistics
            pipeline = [
                {
                    "$group": {
                        "_id": "$algorithm_name",
                        "total_runs": {"$sum": 1},
                        "avg_proximity_penalty": {"$avg": "$metrics.proximity_penalty"},
                        "avg_efficiency_score": {"$avg": "$metrics.efficiency_score"},
                        "best_proximity_penalty": {"$min": "$metrics.proximity_penalty"},
                        "best_efficiency_score": {"$max": "$metrics.efficiency_score"},
                        "avg_execution_time": {"$avg": "$execution_time_seconds"}
                    }
                },
                {
                    "$sort": {"avg_proximity_penalty": 1}  # Sort by best average proximity penalty
                }
            ]
            
            cursor = self.database[self.collection_name].aggregate(pipeline)
            stats = await cursor.to_list(length=None)
            
            # Get total runs across all algorithms
            total_runs = await self.database[self.collection_name].count_documents({})
            
            return {
                "total_runs": total_runs,
                "algorithm_stats": stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get algorithm statistics: {e}")
            raise
    
    async def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instance
exam_db_service = ExamEvaluationDatabaseService() 