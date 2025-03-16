
# app/etl/training_data.py
"""
Training data for the chatbot to answer ETL-related questions
"""

ETL_TRAINING_DATA = [
    {
        "question": "How do I upload data in bulk?",
        "answer": "You can upload data in bulk by going to the Data Management section and selecting 'Bulk Data Import'. From there, you can download a template for the type of data you want to upload (activities, modules, spaces, or years), fill it out, and then upload it back to the system."
    },
    {
        "question": "What file formats are supported for bulk uploads?",
        "answer": "The system supports both CSV and Excel (XLSX) file formats for bulk data uploads. You can download a template in Excel format and either use it directly or convert it to CSV if preferred."
    },
    {
        "question": "How do I download a template for data upload?",
        "answer": "Go to the Data Management section, select 'Bulk Data Import', and then click on the 'Download Template' button next to the entity type you want to upload (activities, modules, spaces, or years)."
    },
    {
        "question": "What happens if my uploaded data has errors?",
        "answer": "If your uploaded data contains errors, the system will validate the data and show you a detailed error report. The report will include the row number, field name, and a description of each error. No invalid data will be imported until you fix the errors and re-upload the file."
    },
    {
        "question": "Can I see how my new data will impact existing timetables?",
        "answer": "Yes, after uploading your data, the system will perform an impact analysis to show you how the new data might affect existing timetables. This includes information about affected teachers, subgroups, and potential conflicts. The impact is rated as low, medium, or high to help you understand the potential consequences."
    },
    {
        "question": "What information is required for activities?",
        "answer": "Required fields for activities include: code (format: AC-XXX), name, subject code, activity type, duration, teacher IDs, and subgroup IDs. Optional fields include required equipment and special requirements."
    },
    {
        "question": "What information is required for modules?",
        "answer": "Required fields for modules include: code, name, and long name. The description field is optional."
    },
    {
        "question": "What information is required for spaces?",
        "answer": "Required fields for spaces include: name, long name, code (3-10 uppercase letters or numbers), and capacity. The attributes field is optional and can be provided as a JSON string or comma-separated key:value pairs."
    },
    {
        "question": "What information is required for years and subgroups?",
        "answer": "Required fields for years include: year name, year long name, and total capacity. Each year must have at least one subgroup, and each subgroup requires a name, code (3-10 uppercase letters or numbers), and capacity. The total capacity of all subgroups should not exceed the year's total capacity."
    },
    {
        "question": "How do I specify multiple teachers or subgroups for an activity?",
        "answer": "For multiple teachers or subgroups, use a comma-separated list in the respective fields. For example, in the teacher_ids field, you can enter 'T001,T002,T003' to assign three teachers to an activity."
    },
    {
        "question": "What happens if I upload duplicate data?",
        "answer": "The system checks for duplicates based on unique codes (like activity code, module code, etc.). If duplicates are found, the system will flag them as errors during validation. You'll need to resolve these duplicates before the data can be imported."
    },
    {
        "question": "Can I update existing data through bulk upload?",
        "answer": "Yes, if you include the code of an existing entity in your upload file, the system will update that entity with the new information provided. This allows you to make bulk updates to existing data."
    },
    {
        "question": "How do I specify attributes for spaces?",
        "answer": "You can specify attributes for spaces either as a JSON string (e.g., '{\"projector\": \"Yes\", \"whiteboard\": \"Yes\"}') or as comma-separated key:value pairs (e.g., 'projector:Yes,whiteboard:Yes'). These attributes help describe the facilities available in each space."
    },
    {
        "question": "What is the format for the year template?",
        "answer": "The year template has rows representing subgroups within years. If a year has multiple subgroups, you'll have multiple rows with the same year information (year_name, year_long_name, total_capacity) but different subgroup information (subgroup_name, subgroup_code, subgroup_capacity)."
    },
    {
        "question": "How can I get help with data import errors?",
        "answer": "If you encounter errors during data import, the system provides detailed error messages for each issue. You can also refer to the documentation sheets in the template files for field requirements and examples. If you need further assistance, please contact the system administrator."
    }
]

def get_etl_training_data():
    """Return the ETL training data for the chatbot"""
    return ETL_TRAINING_DATA