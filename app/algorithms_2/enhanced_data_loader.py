"""
Enhanced Data Loader with Student ID Mapping for Backend
Extends the basic data loader to include key-value pairs for student IDs and exam assignments
"""
from typing import Dict, List, Tuple, Optional, Set, Any
import os
import sys
from Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots

class EnhancedDataLoader:
    """
    Enhanced data loader that includes student ID mappings and key-value pairs
    for better HTML timetable visualization
    """
    
    def __init__(self):
        """Initialize the enhanced data loader with existing data"""
        self.activities_dict = activities_dict
        self.groups_dict = groups_dict
        self.spaces_dict = spaces_dict
        self.lecturers_dict = lecturers_dict
        self.slots = slots
        
        # Enhanced mappings
        self.student_id_to_activities = {}
        self.activity_id_to_students = {}
        self.student_id_to_groups = {}
        self.group_id_to_students = {}
        
        # Generate student IDs and mappings
        self._generate_student_mappings()
    
    def _generate_student_mappings(self):
        """Generate student ID mappings and key-value pairs"""
        student_counter = 1
        
        # Generate student IDs for each group
        for group_id, group in self.groups_dict.items():
            group_students = []
            
            # Generate student IDs for this group
            for i in range(group.size):
                student_id = f"IT{20000 + student_counter:05d}"
                group_students.append(student_id)
                
                # Map student to group
                self.student_id_to_groups[student_id] = group_id
                
                # Initialize student's activity list
                self.student_id_to_activities[student_id] = []
                
                student_counter += 1
            
            # Map group to students
            self.group_id_to_students[group_id] = group_students
        
        # Map students to activities based on group enrollments
        for activity_id, activity in self.activities_dict.items():
            activity_students = []
            
            # Get all students from groups enrolled in this activity
            for group_id in activity.group_ids:
                if group_id in self.group_id_to_students:
                    group_students = self.group_id_to_students[group_id]
                    activity_students.extend(group_students)
                    
                    # Add this activity to each student's activity list
                    for student_id in group_students:
                        if student_id in self.student_id_to_activities:
                            self.student_id_to_activities[student_id].append(activity_id)
            
            # Map activity to students
            self.activity_id_to_students[activity_id] = activity_students
    
    def get_student_activities(self, student_id: str) -> List[str]:
        """Get all activities for a specific student"""
        return self.student_id_to_activities.get(student_id, [])
    
    def get_activity_students(self, activity_id: str) -> List[str]:
        """Get all students enrolled in a specific activity"""
        return self.activity_id_to_students.get(activity_id, [])
    
    def get_group_students(self, group_id: str) -> List[str]:
        """Get all students in a specific group"""
        return self.group_id_to_students.get(group_id, [])
    
    def get_student_group(self, student_id: str) -> Optional[str]:
        """Get the group ID for a specific student"""
        return self.student_id_to_groups.get(student_id)
    
    def get_slot_student_assignments(self, timetable: dict, slot: str) -> Dict[str, List[str]]:
        """
        Get student assignments for a specific time slot
        
        Args:
            timetable: The timetable dictionary
            slot: The time slot to analyze
            
        Returns:
            Dictionary mapping room IDs to lists of student IDs
        """
        slot_assignments = {}
        
        if slot in timetable:
            for room_id, activity in timetable[slot].items():
                if activity is not None and hasattr(activity, 'id'):
                    # Get students enrolled in this activity
                    students = self.get_activity_students(activity.id)
                    slot_assignments[room_id] = students
                else:
                    slot_assignments[room_id] = []
        
        return slot_assignments
    
    def get_student_schedule(self, student_id: str, timetable: dict) -> Dict[str, Dict[str, str]]:
        """
        Get the complete schedule for a specific student
        
        Args:
            student_id: The student ID
            timetable: The timetable dictionary
            
        Returns:
            Dictionary mapping slots to activity and room information
        """
        student_schedule = {}
        
        for slot in self.slots:
            if slot in timetable:
                for room_id, activity in timetable[slot].items():
                    if activity is not None and hasattr(activity, 'id'):
                        # Check if this student is enrolled in this activity
                        activity_students = self.get_activity_students(activity.id)
                        if student_id in activity_students:
                            student_schedule[slot] = {
                                'activity_id': activity.id,
                                'activity_name': activity.subject,
                                'room_id': room_id,
                                'lecturer_id': activity.teacher_id
                            }
                            break  # Student can only have one activity per slot
        
        return student_schedule
    
    def export_student_mappings(self) -> Dict[str, Any]:
        """Export all student mappings for external use"""
        return {
            'student_id_to_activities': self.student_id_to_activities,
            'activity_id_to_students': self.activity_id_to_students,
            'student_id_to_groups': self.student_id_to_groups,
            'group_id_to_students': self.group_id_to_students,
            'total_students': len(self.student_id_to_activities),
            'total_activities': len(self.activity_id_to_students),
            'total_groups': len(self.group_id_to_students)
        }
    
    def print_summary(self):
        """Print a summary of the enhanced data loader"""
        print("🎓 Enhanced Data Loader Summary")
        print("=" * 40)
        print(f"Total Students: {len(self.student_id_to_activities)}")
        print(f"Total Activities: {len(self.activity_id_to_students)}")
        print(f"Total Groups: {len(self.group_id_to_students)}")
        print(f"Total Lecturers: {len(self.lecturers_dict)}")
        print(f"Total Rooms: {len(self.spaces_dict)}")
        print(f"Total Time Slots: {len(self.slots)}")
        
        # Sample student information
        if self.student_id_to_activities:
            sample_student = list(self.student_id_to_activities.keys())[0]
            sample_activities = self.student_id_to_activities[sample_student]
            sample_group = self.student_id_to_groups[sample_student]
            
            print(f"\nSample Student: {sample_student}")
            print(f"  Group: {sample_group}")
            print(f"  Activities: {len(sample_activities)} enrolled")
            print(f"  Activity IDs: {sample_activities[:3]}{'...' if len(sample_activities) > 3 else ''}")


# Global instance for easy access
enhanced_data_loader = EnhancedDataLoader()

if __name__ == "__main__":
    # Test the enhanced data loader
    enhanced_data_loader.print_summary()
    
    # Test student mappings
    if enhanced_data_loader.student_id_to_activities:
        sample_student = list(enhanced_data_loader.student_id_to_activities.keys())[0]
        print(f"\nTesting with student {sample_student}:")
        print(f"Activities: {enhanced_data_loader.get_student_activities(sample_student)}")
        print(f"Group: {enhanced_data_loader.get_student_group(sample_student)}") 