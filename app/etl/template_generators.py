# app/etl/template_generators.py
import pandas as pd
import io
from fastapi.responses import StreamingResponse

def generate_activity_template(format='xlsx'):
    """Generate a template file for Activities in Excel or CSV format"""
    data = {
        'code': ['AC-001', 'AC-002'],  # Example data
        'name': ['Introduction to Programming', 'Database Systems'],
        'subject': ['CSC101', 'CSC205'],
        'activity_type': ['lecture', 'lab'],
        'duration': [2, 3],
        'teacher_ids': ['T001,T002', 'T003'],  # Comma-separated for multiple values
        'subgroup_ids': ['GRP001', 'GRP002,GRP003'],
        'required_equipment': ['projector,whiteboard', 'computers'],
        'special_requirements': ['None', 'Requires computer lab']
    }
    
    df = pd.DataFrame(data)
    
    if format.lower() == 'csv':
        # Create CSV output
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=activities_template.csv'}
        )
    else:
        # Create an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Activities', index=False)
            worksheet = writer.sheets['Activities']
            
            # Add a documentation sheet
            documentation = pd.DataFrame({
                'Field': ['code', 'name', 'subject', 'activity_type', 'duration', 
                        'teacher_ids', 'subgroup_ids', 'required_equipment', 'special_requirements'],
                'Description': [
                    'Unique code for the activity (format: AC-XXX)',
                    'Name of the activity',
                    'Module/Subject code this activity is part of',
                    'Type of activity (lecture, lab, tutorial, etc.)',
                    'Duration in periods (integer)',
                    'Comma-separated list of teacher IDs',
                    'Comma-separated list of student subgroup IDs',
                    'Comma-separated list of required equipment',
                    'Any special requirements (optional)'
                ],
                'Required': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No'],
                'Example': ['AC-001', 'Introduction to Programming', 'CSC101', 'lecture', '2', 
                          'T001,T002', 'GRP001', 'projector,whiteboard', 'Requires computer lab']
            })
            documentation.to_excel(writer, sheet_name='Documentation', index=False)
        
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=activities_template.xlsx'}
        )

def generate_module_template(format='xlsx'):
    """Generate a template file for Modules in Excel or CSV format"""
    data = {
        'code': ['CSC101', 'CSC205'],  # Example data
        'name': ['Programming Basics', 'Database Systems'],
        'long_name': ['Introduction to Programming', 'Database Management Systems'],
        'description': ['Fundamentals of programming using Python', 'Relational databases and SQL']
    }
    
    df = pd.DataFrame(data)
    
    if format.lower() == 'csv':
        # Create CSV output
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=modules_template.csv'}
        )
    else:
        # Create an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Modules', index=False)
            
            # Add a documentation sheet
            documentation = pd.DataFrame({
                'Field': ['code', 'name', 'long_name', 'description'],
                'Description': [
                    'Unique code for the module',
                    'Short name of the module',
                    'Full name of the module',
                    'Description of the module (optional)'
                ],
                'Required': ['Yes', 'Yes', 'Yes', 'No'],
                'Example': ['CSC101', 'Programming Basics', 'Introduction to Programming', 'Fundamentals of programming using Python']
            })
            documentation.to_excel(writer, sheet_name='Documentation', index=False)
        
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=modules_template.xlsx'}
        )

def generate_space_template(format='xlsx'):
    """Generate a template file for Spaces in Excel or CSV format"""
    data = {
        'name': ['LH1', 'Lab2'],  # Example data
        'long_name': ['Lecture Hall 1', 'Computer Lab 2'],
        'code': ['LH101', 'CL102'],
        'capacity': [150, 30],
        'attributes': ['{"projector": "Yes", "whiteboard": "Yes", "air_conditioned": "No"}', 
                      '{"computers": 30, "software": "Visual Studio, Eclipse"}']
    }
    
    df = pd.DataFrame(data)
    
    if format.lower() == 'csv':
        # Create CSV output
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=spaces_template.csv'}
        )
    else:
        # Create an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Spaces', index=False)
            
            # Add a documentation sheet
            documentation = pd.DataFrame({
                'Field': ['name', 'long_name', 'code', 'capacity', 'attributes'],
                'Description': [
                    'Short name for the space',
                    'Full name of the space',
                    'Unique code for the space (format: 3-10 uppercase letters or numbers)',
                    'Maximum capacity of the space',
                    'JSON string or comma-separated key:value pairs of attributes'
                ],
                'Required': ['Yes', 'Yes', 'Yes', 'Yes', 'No'],
                'Example': ['LH1', 'Lecture Hall 1', 'LH101', '150', '{"projector": "Yes", "whiteboard": "Yes"}']
            })
            documentation.to_excel(writer, sheet_name='Documentation', index=False)
        
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=spaces_template.xlsx'}
        )

def generate_year_template(format='xlsx'):
    """Generate a template file for Years and Subgroups in Excel or CSV format"""
    data = {
        'year_name': [1, 1, 2, 2],  # Example data
        'year_long_name': ['First Year', 'First Year', 'Second Year', 'Second Year'],
        'total_capacity': [100, 100, 80, 80],
        'subgroup_name': ['Group A', 'Group B', 'Group A', 'Group B'],
        'subgroup_code': ['GRP001', 'GRP002', 'GRP003', 'GRP004'],
        'subgroup_capacity': [50, 50, 40, 40]
    }
    
    df = pd.DataFrame(data)
    
    if format.lower() == 'csv':
        # Create CSV output
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=years_template.csv'}
        )
    else:
        # Create an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Years', index=False)
            
            # Add a documentation sheet
            documentation = pd.DataFrame({
                'Field': ['year_name', 'year_long_name', 'total_capacity', 
                        'subgroup_name', 'subgroup_code', 'subgroup_capacity'],
                'Description': [
                    'Year number or identifier',
                    'Full name of the year',
                    'Total capacity for the year',
                    'Name of the subgroup',
                    'Unique code for the subgroup (format: 3-10 uppercase letters or numbers)',
                    'Capacity of the subgroup'
                ],
                'Required': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
                'Example': ['1', 'First Year', '100', 'Group A', 'GRP001', '50']
            })
            documentation.to_excel(writer, sheet_name='Documentation', index=False)
            
            # Add an explanation sheet
            explanation = pd.DataFrame({
                'Topic': ['File Format', 'Multiple Subgroups', 'Validation Rules'],
                'Explanation': [
                    'Each row represents a subgroup within a year. Multiple rows can have the same year_name to represent different subgroups in the same year.',
                    'If a year has multiple subgroups, repeat the year information (year_name, year_long_name, total_capacity) for each subgroup row.',
                    'The sum of subgroup capacities for a year should not exceed the total_capacity of that year.'
                ]
            })
            explanation.to_excel(writer, sheet_name='Explanation', index=False)
        
        output.seek(0)
        
        # Create a streaming response
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=years_template.xlsx'}
        )

def get_template_generator(entity_type: str, format: str = 'xlsx'):
    """Get the appropriate template generator function based on entity type"""
    generators = {
        'activities': generate_activity_template,
        'modules': generate_module_template,
        'spaces': generate_space_template,
        'years': generate_year_template
    }
    
    generator = generators.get(entity_type)
    if generator:
        return generator(format)
    return None