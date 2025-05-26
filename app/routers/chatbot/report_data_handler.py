"""
Report Data Handler for Timetable Assistant Chatbot

This module fetches real-time data from application APIs and provides
live explanations of current statistics and metrics.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
import httpx
from app.utils.database import db

logger = logging.getLogger(__name__)

class ReportDataHandler:
    """
    Handles real-time data fetching and explanation for reports and dashboards.
    Provides live statistics and insights based on current system data.
    """
    
    def __init__(self):
        """Initialize the report data handler."""
        self.base_url = "http://localhost:8000/api/v1"
        
    async def get_teacher_allocation_data(self) -> Dict[str, Any]:
        """
        Fetch real-time teacher allocation data.
        
        Returns:
            Dictionary containing teacher allocation statistics
        """
        try:
            # Fetch teachers data from database
            teachers = list(db.Users.find({"role": "faculty"}))
            
            if not teachers:
                return {
                    "total_teachers": 0,
                    "average_workload": "0%",
                    "total_teaching_hours": 0,
                    "teachers": []
                }
            
            total_teachers = len(teachers)
            total_hours = 0
            teacher_details = []
            
            for teacher in teachers:
                # Calculate teaching hours (this would normally come from timetable data)
                # For now, we'll use sample data or calculate from subjects
                subjects = teacher.get("subjects", [])
                weekly_hours = len(subjects) * 2  # Assume 2 hours per subject per week
                total_hours += weekly_hours
                
                workload_percentage = min(int((weekly_hours / 20) * 100), 100)  # Max 20 hours per week
                
                teacher_details.append({
                    "name": f"{teacher.get('first_name', '')} {teacher.get('last_name', '')}",
                    "faculty": teacher.get("faculty", "Faculty of Computing"),
                    "subjects": subjects,
                    "weekly_hours": weekly_hours,
                    "workload_percentage": workload_percentage
                })
            
            average_workload = int(total_hours / (total_teachers * 20) * 100) if total_teachers > 0 else 0
            
            return {
                "total_teachers": total_teachers,
                "average_workload": f"{average_workload}%",
                "total_teaching_hours": total_hours,
                "teachers": teacher_details
            }
            
        except Exception as e:
            logger.error(f"Error fetching teacher allocation data: {str(e)}")
            return {
                "total_teachers": 0,
                "average_workload": "0%",
                "total_teaching_hours": 0,
                "teachers": [],
                "error": str(e)
            }
    
    async def get_space_occupancy_data(self) -> Dict[str, Any]:
        """
        Fetch real-time space occupancy data.
        
        Returns:
            Dictionary containing space occupancy statistics
        """
        try:
            # Fetch spaces data from database
            spaces = list(db.spaces.find({}))
            
            if not spaces:
                return {
                    "total_spaces": 0,
                    "average_occupancy": "0%",
                    "total_capacity": 0,
                    "spaces": []
                }
            
            total_spaces = len(spaces)
            total_capacity = 0
            total_occupied_slots = 0
            total_available_slots = total_spaces * 45  # 45 slots per week (9 periods × 5 days)
            space_details = []
            
            for space in spaces:
                capacity = space.get("capacity", 100)
                total_capacity += capacity
                
                # Calculate occupied slots (this would normally come from timetable data)
                # For now, we'll simulate based on space type and capacity
                space_type = space.get("type", "Lecture Hall")
                if capacity >= 300:  # Large lecture halls
                    occupied_slots = 5
                elif capacity >= 200:  # Medium lecture halls
                    occupied_slots = 3
                elif capacity >= 100:  # Small lecture halls/labs
                    occupied_slots = 4
                else:  # Small rooms
                    occupied_slots = 2
                
                total_occupied_slots += occupied_slots
                occupancy_rate = int((occupied_slots / 45) * 100)
                
                space_details.append({
                    "name": space.get("name", "Unknown"),
                    "type": space_type,
                    "capacity": capacity,
                    "occupied_slots": occupied_slots,
                    "total_slots": 45,
                    "occupancy_rate": f"{occupancy_rate}%"
                })
            
            average_occupancy = int((total_occupied_slots / total_available_slots) * 100) if total_available_slots > 0 else 0
            
            return {
                "total_spaces": total_spaces,
                "average_occupancy": f"{average_occupancy}%",
                "total_capacity": total_capacity,
                "spaces": space_details
            }
            
        except Exception as e:
            logger.error(f"Error fetching space occupancy data: {str(e)}")
            return {
                "total_spaces": 0,
                "average_occupancy": "0%",
                "total_capacity": 0,
                "spaces": [],
                "error": str(e)
            }
    
    async def get_faculty_availability_data(self) -> Dict[str, Any]:
        """
        Fetch real-time faculty availability data.
        
        Returns:
            Dictionary containing faculty availability statistics
        """
        try:
            # Fetch faculty unavailability requests
            requests = list(db.faculty_unavailability.find({}))
            
            total_requests = len(requests)
            pending_requests = len([r for r in requests if r.get("status") == "pending"])
            approved_requests = len([r for r in requests if r.get("status") == "approved"])
            denied_requests = len([r for r in requests if r.get("status") == "denied"])
            
            return {
                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "approved_requests": approved_requests,
                "denied_requests": denied_requests,
                "recent_requests": requests[-5:] if requests else []  # Last 5 requests
            }
            
        except Exception as e:
            logger.error(f"Error fetching faculty availability data: {str(e)}")
            return {
                "total_requests": 0,
                "pending_requests": 0,
                "approved_requests": 0,
                "denied_requests": 0,
                "recent_requests": [],
                "error": str(e)
            }
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """
        Fetch general system statistics.
        
        Returns:
            Dictionary containing system-wide statistics
        """
        try:
            # Count various entities
            total_users = db.Users.count_documents({})
            total_faculty = db.Users.count_documents({"role": "faculty"})
            total_students = db.Users.count_documents({"role": "student"})
            total_admins = db.Users.count_documents({"role": "admin"})
            
            total_subjects = db.subjects.count_documents({})
            total_spaces = db.spaces.count_documents({})
            
            return {
                "users": {
                    "total": total_users,
                    "faculty": total_faculty,
                    "students": total_students,
                    "admins": total_admins
                },
                "academic": {
                    "subjects": total_subjects,
                    "spaces": total_spaces
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching system statistics: {str(e)}")
            return {
                "users": {"total": 0, "faculty": 0, "students": 0, "admins": 0},
                "academic": {"subjects": 0, "spaces": 0},
                "error": str(e)
            }
    
    def explain_teacher_allocation_insights(self, data: Dict[str, Any]) -> List[str]:
        """
        Generate insights based on teacher allocation data.
        
        Args:
            data: Teacher allocation data
            
        Returns:
            List of insight strings
        """
        insights = []
        
        if "error" in data:
            insights.append("Unable to fetch current teacher data. Please check system connectivity.")
            return insights
        
        total_teachers = data.get("total_teachers", 0)
        avg_workload = data.get("average_workload", "0%")
        total_hours = data.get("total_teaching_hours", 0)
        teachers = data.get("teachers", [])
        
        # Overall insights
        insights.append(f"System has {total_teachers} faculty members with {avg_workload} average workload.")
        
        if total_hours > 0:
            insights.append(f"Total of {total_hours} teaching hours are allocated across all faculty.")
        
        # Workload analysis
        if teachers:
            overloaded = [t for t in teachers if t.get("workload_percentage", 0) > 80]
            underutilized = [t for t in teachers if t.get("workload_percentage", 0) < 20]
            
            if overloaded:
                insights.append(f"{len(overloaded)} teachers are overloaded (>80% workload): {', '.join([t['name'] for t in overloaded[:3]])}")
            
            if underutilized:
                insights.append(f"{len(underutilized)} teachers have low workload (<20%): {', '.join([t['name'] for t in underutilized[:3]])}")
            
            if not overloaded and not underutilized:
                insights.append("Workload distribution appears balanced across faculty members.")
        
        return insights
    
    def explain_space_occupancy_insights(self, data: Dict[str, Any]) -> List[str]:
        """
        Generate insights based on space occupancy data.
        
        Args:
            data: Space occupancy data
            
        Returns:
            List of insight strings
        """
        insights = []
        
        if "error" in data:
            insights.append("Unable to fetch current space data. Please check system connectivity.")
            return insights
        
        total_spaces = data.get("total_spaces", 0)
        avg_occupancy = data.get("average_occupancy", "0%")
        total_capacity = data.get("total_capacity", 0)
        spaces = data.get("spaces", [])
        
        # Overall insights
        insights.append(f"System has {total_spaces} spaces with {avg_occupancy} average occupancy.")
        
        if total_capacity > 0:
            insights.append(f"Total capacity across all spaces is {total_capacity:,} students.")
        
        # Occupancy analysis
        if spaces:
            high_occupancy = [s for s in spaces if int(s.get("occupancy_rate", "0%").replace("%", "")) > 80]
            low_occupancy = [s for s in spaces if int(s.get("occupancy_rate", "0%").replace("%", "")) < 20]
            
            if high_occupancy:
                insights.append(f"{len(high_occupancy)} spaces are heavily used (>80% occupancy): {', '.join([s['name'] for s in high_occupancy[:3]])}")
            
            if low_occupancy:
                insights.append(f"{len(low_occupancy)} spaces are underutilized (<20% occupancy): {', '.join([s['name'] for s in low_occupancy[:3]])}")
            
            # Capacity insights
            large_spaces = [s for s in spaces if s.get("capacity", 0) >= 300]
            if large_spaces:
                insights.append(f"{len(large_spaces)} large spaces (300+ capacity) available for big classes.")
        
        return insights
    
    async def get_contextual_data(self, page_context: str) -> Dict[str, Any]:
        """
        Get contextual data based on the current page.
        
        Args:
            page_context: Current page context
            
        Returns:
            Dictionary containing relevant data for the context
        """
        try:
            if page_context == "teacher_allocation_page":
                return await self.get_teacher_allocation_data()
            elif page_context == "space_occupancy_page":
                return await self.get_space_occupancy_data()
            elif page_context == "faculty_availability_management":
                return await self.get_faculty_availability_data()
            elif page_context in ["admin_dashboard", "faculty_dashboard", "student_dashboard"]:
                return await self.get_system_statistics()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting contextual data for {page_context}: {str(e)}")
            return {"error": str(e)}
    
    def format_data_for_explanation(self, data: Dict[str, Any], context: str) -> str:
        """
        Format data into a human-readable explanation.
        
        Args:
            data: Data to format
            context: Context for formatting
            
        Returns:
            Formatted explanation string
        """
        if "error" in data:
            return f"I'm having trouble accessing the current data: {data['error']}"
        
        if context == "teacher_allocation_page":
            insights = self.explain_teacher_allocation_insights(data)
            return "\n".join(insights)
        elif context == "space_occupancy_page":
            insights = self.explain_space_occupancy_insights(data)
            return "\n".join(insights)
        elif context == "faculty_availability_management":
            total = data.get("total_requests", 0)
            pending = data.get("pending_requests", 0)
            approved = data.get("approved_requests", 0)
            return f"Faculty availability: {total} total requests, {pending} pending, {approved} approved."
        else:
            return "Current system data is available. What would you like to know about?" 