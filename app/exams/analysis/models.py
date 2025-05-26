from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Annotated
from datetime import datetime
from bson import ObjectId

# Simple string-based ID for Pydantic v2 compatibility
PyObjectId = Annotated[str, Field(description="MongoDB ObjectId as string")]

class ExamMetrics(BaseModel):
    """Individual metrics for an exam algorithm run"""
    proximity_penalty: float = Field(..., description="Total proximity penalty score")
    conflict_violations: int = Field(..., description="Number of hard constraint violations")
    room_capacity_violations: int = Field(..., description="Number of room capacity violations")
    slot_utilization: float = Field(..., description="Percentage of time slots utilized")
    student_load_variance: float = Field(..., description="Variance in student exam load per day")
    max_exams_per_day: int = Field(..., description="Maximum exams any student has in a single day")
    avg_exams_per_day: float = Field(..., description="Average exams per student per day")
    total_students_affected: int = Field(..., description="Total students with proximity conflicts")
    
    # Additional quality metrics
    fairness_score: float = Field(..., description="How fairly exams are distributed")
    efficiency_score: float = Field(..., description="Overall efficiency of the timetable")
    
    class Config:
        json_encoders = {ObjectId: str}

class AlgorithmRunResult(BaseModel):
    """Complete result of an algorithm run"""
    id: Optional[str] = Field(default=None, alias="_id")
    algorithm_name: str = Field(..., description="Name of the algorithm used")
    run_timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_seconds: float = Field(..., description="Time taken to run the algorithm")
    
    # Algorithm parameters
    algorithm_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters used for the algorithm")
    
    # Raw results
    solution: List[int] = Field(..., description="The solution permutation/assignment")
    objective_values: Dict[str, float] = Field(default_factory=dict, description="Raw objective function values")
    
    # Detailed metrics
    metrics: ExamMetrics = Field(..., description="Detailed evaluation metrics")
    
    # Metadata
    dataset_info: Dict[str, Any] = Field(default_factory=dict, description="Information about the dataset used")
    success: bool = Field(True, description="Whether the algorithm run was successful")
    error_message: Optional[str] = Field(None, description="Error message if run failed")
    
    # Comparison data
    rank_among_runs: Optional[int] = Field(None, description="Rank of this run compared to others")
    percentile_score: Optional[float] = Field(None, description="Percentile score compared to other runs")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AlgorithmComparison(BaseModel):
    """Comparison results between multiple algorithm runs"""
    id: Optional[str] = Field(default=None, alias="_id")
    comparison_timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_ids: List[str] = Field(..., description="List of algorithm run IDs being compared")
    
    # Ranking results
    proximity_ranking: List[Dict[str, Any]] = Field(..., description="Algorithms ranked by proximity penalty")
    efficiency_ranking: List[Dict[str, Any]] = Field(..., description="Algorithms ranked by efficiency")
    overall_ranking: List[Dict[str, Any]] = Field(..., description="Overall ranking considering all metrics")
    
    # Statistical analysis
    best_algorithm: str = Field(..., description="Best performing algorithm overall")
    worst_algorithm: str = Field(..., description="Worst performing algorithm overall")
    performance_gap: float = Field(..., description="Performance gap between best and worst")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 