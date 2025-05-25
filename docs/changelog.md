# Changelog and Technical Documentation

## Recent Changes in Current Chat Session

### Bug Fixes
- **Fixed White Screen Issue**: Resolved a critical issue that caused the application to display a white screen by removing the problematic `TimetableView` import from `Home.jsx` and updating the redirection logic to prevent navigation to non-existent routes.

### UI Improvements
- **Enhanced ViewSliitTimetable Component**: Improved the user interface by adding tooltips with descriptive information to metric displays and incorporating InfoCircle icons for better user feedback.
- **API Endpoint Update**: Updated the SLIIT timetable API endpoint from `/timetable/sliit/timetables` to `/timetable/sliit/timetable_sliit` to ensure proper backend communication.

## Technical Explanation of Timetable Optimization Algorithms

### Chromosome Representation
Our timetable scheduling system uses a sophisticated chromosome representation tailored for educational scheduling:

- **Chromosome Structure**: Each chromosome represents a complete timetable solution, encoded as a multi-dimensional array where each element represents:
  - Time slot (day and period)
  - Room assignment
  - Teacher assignment
  - Subject/course
  - Student group

- **Gene Encoding**: 
  ```
  Gene = [Day, Period, Room, Teacher, Subject, StudentGroup]
  ```
  This encoding ensures that all constraints can be evaluated directly from the chromosome.

### Algorithm Implementation

1. **NSGA-II (Non-dominated Sorting Genetic Algorithm II)**: A multi-objective genetic algorithm that optimizes multiple conflicting objectives simultaneously:
   - **Initialization**: Creates an initial population of random timetables.
   - **Evaluation**: Evaluates each solution against multiple objectives:
     - Room utilization (maximize)
     - Teacher satisfaction (minimize preference violations)
     - Student satisfaction (minimize gaps and overloads)
     - Time efficiency (distribute classes appropriately)
   - **Selection**: Uses tournament selection with non-dominated sorting.
   - **Crossover**: Implements specialized timetable crossover that preserves feasibility.
   - **Mutation**: Employs targeted mutation operators such as room reassignment, time slot shifting, and teacher reassignment.
   - **Optimizations**: Includes local search, constraint repair, and adaptive mutation rate adjustments.

2. **SPEA2 (Strength Pareto Evolutionary Algorithm)**: A sophisticated multi-objective algorithm with improved selection mechanisms:
   - **Fitness Assignment**: Based on both dominance and density information.
   - **Environmental Selection**: Maintains a diverse Pareto front using nearest neighbor density estimation.
   - **Archive Management**: Maintains elite solutions across generations.
   - **Optimizations**: Incorporates clustering, adaptive grid adjustments, and variable neighborhood search.

3. **MOEAD (Multi-objective Evolutionary Algorithm Based on Decomposition)**: Decomposes the multi-objective problem into multiple single-objective subproblems:
   - **Decomposition Methods**: Uses the Tchebycheff approach to create scalar optimization subproblems.
   - **Neighborhood Structure**: Defines neighborhoods for each subproblem.
   - **Collaborative Evolution**: Solutions evolve by collaborating with neighboring subproblems.
   - **Optimizations**: Includes adaptive weight vectors, constrained decomposition, and resource allocation.

### Performance Optimization Techniques
- **Constraint Handling**: Implements hard and soft constraints with repair mechanisms.
- **Parallel Computation**: Utilizes multi-threading for performance improvements.
- **Caching Mechanisms**: Caches solutions and objective values to avoid redundant calculations.
- **Custom Operators**: Employs knowledge-based crossover, directed mutation, and elitism.

### Calculation Methods
- **Fitness Calculation**: Includes metrics for room utilization, teacher satisfaction, student satisfaction, and time efficiency.
- **Constraint Violation Calculation**: Differentiates between hard and soft constraint violations.
- **Pareto Optimality**: Ranks solutions based on dominance relationships to form the Pareto front.

This integrated approach allows our system to generate high-quality timetables that balance multiple competing objectives while satisfying complex educational constraints specific to the SLIIT dataset.

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