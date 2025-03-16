# app/etl/impact_analyzer.py
from typing import List, Dict, Any, Optional
from app.models.activity_model import Activity
from app.models.module_model import Module
from app.models.space_model import Space
from app.models.year_model import Year, SubGroup

class ImpactAnalyzer:
    """
    Analyzes the impact of new data on existing timetables
    """
    
    @staticmethod
    async def analyze_activities_impact(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the impact of new activities on existing timetables
        
        Args:
            activities: List of activity dictionaries to analyze
            
        Returns:
            Dictionary with impact analysis results
        """
        impact_results = {
            'affected_timetables': [],
            'affected_teachers': set(),
            'affected_subgroups': set(),
            'potential_conflicts': [],
            'impact_level': 'low'  # Can be 'low', 'medium', 'high'
        }
        
        # Get existing timetables that might be affected
        # This would depend on your database structure and how timetables are stored
        
        # For each activity, check if it affects existing timetables
        for activity in activities:
            # Check teacher conflicts
            if activity.get('teacher_ids'):
                teacher_ids = activity['teacher_ids']
                if isinstance(teacher_ids, str):
                    teacher_ids = [tid.strip() for tid in teacher_ids.split(',')]
                impact_results['affected_teachers'].update(teacher_ids)
            
            # Check subgroup conflicts
            if activity.get('subgroup_ids'):
                subgroup_ids = activity['subgroup_ids']
                if isinstance(subgroup_ids, str):
                    subgroup_ids = [sgid.strip() for sgid in subgroup_ids.split(',')]
                impact_results['affected_subgroups'].update(subgroup_ids)
            
            # Check for potential time conflicts
            # This would require checking against existing scheduled activities
        
        # Convert sets to lists for JSON serialization
        impact_results['affected_teachers'] = list(impact_results['affected_teachers'])
        impact_results['affected_subgroups'] = list(impact_results['affected_subgroups'])
        
        # Determine impact level based on number of affected entities
        if len(impact_results['affected_timetables']) > 5 or len(impact_results['potential_conflicts']) > 10:
            impact_results['impact_level'] = 'high'
        elif len(impact_results['affected_timetables']) > 2 or len(impact_results['potential_conflicts']) > 5:
            impact_results['impact_level'] = 'medium'
        
        return impact_results
    
    @staticmethod
    async def analyze_modules_impact(modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the impact of new modules on existing timetables
        
        Args:
            modules: List of module dictionaries to analyze
            
        Returns:
            Dictionary with impact analysis results
        """
        impact_results = {
            'affected_activities': [],
            'impact_level': 'low'  # Can be 'low', 'medium', 'high'
        }
        
        # Find activities that reference these modules
        # This would depend on your database structure
        
        # Determine impact level based on number of affected activities
        if len(impact_results['affected_activities']) > 20:
            impact_results['impact_level'] = 'high'
        elif len(impact_results['affected_activities']) > 10:
            impact_results['impact_level'] = 'medium'
        
        return impact_results
    
    @staticmethod
    async def analyze_spaces_impact(spaces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the impact of new spaces on existing timetables
        
        Args:
            spaces: List of space dictionaries to analyze
            
        Returns:
            Dictionary with impact analysis results
        """
        impact_results = {
            'affected_timetables': [],
            'capacity_changes': [],
            'impact_level': 'low'  # Can be 'low', 'medium', 'high'
        }
        
        # For each space, check if it's updating an existing space
        for space in spaces:
            space_code = space.get('code')
            if not space_code:
                continue
                
            # Check if this space already exists
            # If it does, check for capacity changes
            # This would depend on your database structure
            
            # For demonstration, we'll assume some capacity changes
            if space.get('capacity'):
                impact_results['capacity_changes'].append({
                    'space_code': space_code,
                    'old_capacity': 0,  # Would be fetched from database
                    'new_capacity': space['capacity'],
                    'difference': space['capacity'] - 0  # Would calculate actual difference
                })
        
        # Determine impact level based on capacity changes
        if any(change['difference'] < 0 for change in impact_results['capacity_changes']):
            # Negative capacity changes have higher impact
            if any(abs(change['difference']) > 20 for change in impact_results['capacity_changes']):
                impact_results['impact_level'] = 'high'
            elif any(abs(change['difference']) > 10 for change in impact_results['capacity_changes']):
                impact_results['impact_level'] = 'medium'
        
        return impact_results
    
    @staticmethod
    async def analyze_years_impact(years: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the impact of new years and subgroups on existing timetables
        
        Args:
            years: List of year dictionaries to analyze
            
        Returns:
            Dictionary with impact analysis results
        """
        impact_results = {
            'affected_activities': [],
            'subgroup_changes': [],
            'capacity_changes': [],
            'impact_level': 'low'  # Can be 'low', 'medium', 'high'
        }
        
        # For each year, check if it's updating an existing year
        for year in years:
            year_name = year.get('name')
            if not year_name:
                continue
                
            # Check if this year already exists
            # If it does, check for capacity changes and subgroup changes
            # This would depend on your database structure
            
            # For demonstration, we'll assume some capacity changes
            if year.get('total_capacity'):
                impact_results['capacity_changes'].append({
                    'year_name': year_name,
                    'old_capacity': 0,  # Would be fetched from database
                    'new_capacity': year['total_capacity'],
                    'difference': year['total_capacity'] - 0  # Would calculate actual difference
                })
            
            # Check subgroup changes
            for subgroup in year.get('subgroups', []):
                subgroup_code = subgroup.get('code')
                if not subgroup_code:
                    continue
                    
                # Check if this subgroup already exists
                # If it does, check for capacity changes
                # This would depend on your database structure
                
                # For demonstration, we'll assume some capacity changes
                if subgroup.get('capacity'):
                    impact_results['subgroup_changes'].append({
                        'subgroup_code': subgroup_code,
                        'old_capacity': 0,  # Would be fetched from database
                        'new_capacity': subgroup['capacity'],
                        'difference': subgroup['capacity'] - 0  # Would calculate actual difference
                    })
        
        # Determine impact level based on capacity changes
        if any(change['difference'] < 0 for change in impact_results['capacity_changes'] + impact_results['subgroup_changes']):
            # Negative capacity changes have higher impact
            if any(abs(change['difference']) > 20 for change in impact_results['capacity_changes'] + impact_results['subgroup_changes']):
                impact_results['impact_level'] = 'high'
            elif any(abs(change['difference']) > 10 for change in impact_results['capacity_changes'] + impact_results['subgroup_changes']):
                impact_results['impact_level'] = 'medium'
        
        return impact_results
    
    @staticmethod
    async def get_analyzer(entity_type: str):
        """Get the appropriate analyzer function based on entity type"""
        analyzers = {
            'activities': ImpactAnalyzer.analyze_activities_impact,
            'modules': ImpactAnalyzer.analyze_modules_impact,
            'spaces': ImpactAnalyzer.analyze_spaces_impact,
            'years': ImpactAnalyzer.analyze_years_impact
        }
        
        return analyzers.get(entity_type)