# Changelog

## [Unreleased]
### Features Implemented
1. **ETL Process Implementation**:
   - Created a structured ETL process for bulk data uploads in the timetable scheduling system.
   - Added new routes for uploading and downloading templates for various entities (activities, modules, years, spaces).
   - Implemented processors for handling the import of activities, modules, spaces, and years.

2. **Data Management Component**:
   - Integrated a new route for "Bulk Data Import" in the Data Management section of the frontend.
   - Created a `DataImport` component to facilitate file uploads and template downloads.

3. **Impact Analyzer**:
   - Developed an `ImpactAnalyzer` class to assess how new data will affect existing timetables.
   - Implemented methods to analyze the impact of activities, modules, spaces, and years.

4. **Template Generators**:
   - Created functions to generate templates for activities, modules, spaces, and years in Excel format.
   - Included documentation sheets within the templates to guide users on required fields and formatting.

5. **Validators**:
   - Created validators for activities, modules, spaces, and years to ensure data integrity before processing.
   - Implemented error handling and reporting for invalid data.

6. **Training Data for Chatbot**:
   - Developed a training data file for the chatbot to assist users with ETL-related questions.

### Dependencies Updated
- Updated the `requirements.txt` file to include new dependencies such as:
  - `charset-normalizer`
  - `distro`
  - `et_xmlfile`
  - `greenlet`
  - `jiter`
  - `jsonpatch`
  - `jsonpointer`
  - `langchain`
  - `openai`
  - `openpyxl`
  - `orjson`
  - `pandas`
  - `python-dateutil`
  - `requests`
  - `SQLAlchemy`
  - `tzdata`
  - `urllib3`

### Code Structure Updates
- Refactored the code structure to ensure modularity and maintainability, adhering to the user's guidelines for code organization.

### Documentation Updates
- Updated documentation to reflect the new ETL features and provided clear instructions for users on how to use the bulk import functionality.