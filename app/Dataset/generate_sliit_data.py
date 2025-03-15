from datetime import datetime, time
import json
from typing import List, Dict
import random

def generate_faculty_data() -> List[Dict]:
    return [{
        "name": "Computing",
        "code": "FCSC",
        "departments": [
            "Computer Science and Software Engineering",
            "Information Technology",
            "Cyber Security",
            "Interactive Media",
            "Information Systems Engineering",
            "Data Science"
        ]
    }]

def generate_modules() -> List[Dict]:
    return [
        # Year 1 Semester 1 Modules
        {
            "code": "IT1010",  # First 1: Year 1, Second 0: Semester 1
            "name": "Introduction to Computing",
            "long_name": "Introduction to Computing",
            "description": "Basic computing concepts"
        },
        {
            "code": "IT1020",
            "name": "IP",
            "long_name": "Introduction to Programming",
            "description": "Programming fundamentals"
        },
        {
            "code": "IT1030",
            "name": "MC",
            "long_name": "Mathematics for Computing",
            "description": "Mathematical concepts"
        },
        {
            "code": "IT1040",
            "name": "DBMS",
            "long_name": "Database Management Systems",
            "description": "Database fundamentals"
        },

        # Year 1 Semester 2 Modules
        {
            "code": "IT1550",  # First 1: Year 1, Second 5: Semester 2
            "name": "OOP",
            "long_name": "Object Oriented Programming",
            "description": "OOP concepts"
        },
        {
            "code": "IT1560",
            "name": "Web Development",
            "long_name": "Web Development",
            "description": "Web development basics"
        },
        {
            "code": "IT1570",
            "name": "Statistics",
            "long_name": "Statistics for IT",
            "description": "Statistical methods"
        },
        {
            "code": "IT1580",
            "name": "DSA",
            "long_name": "Data Structures and Algorithms",
            "description": "Data structures basics"
        },

        # Year 2 Semester 1 Modules
        {
            "code": "IT2010",  # First 2: Year 2, Second 0: Semester 1
            "name": "Advanced Programming",
            "long_name": "Advanced Programming",
            "description": "Advanced programming concepts"
        },
        {
            "code": "IT2020",
            "name": "DBMS II",
            "long_name": "Advanced Database Systems",
            "description": "Advanced database concepts"
        },
        {
            "code": "IT2030",
            "name": "Software Engineering",
            "long_name": "Software Engineering",
            "description": "Software engineering principles"
        },
        {
            "code": "IT2040",
            "name": "Networking",
            "long_name": "Computer Networks II",
            "description": "Advanced networking concepts"
        },

        # Year 2 Semester 2 Modules
        {
            "code": "IT2550",  # First 2: Year 2, Second 5: Semester 2
            "name": "Mobile Development",
            "long_name": "Mobile Application Development",
            "description": "Mobile app development"
        },
        {
            "code": "IT2560",
            "name": "Web Programming",
            "long_name": "Advanced Web Programming",
            "description": "Advanced web development"
        },
        {
            "code": "IT2570",
            "name": "OS",
            "long_name": "Operating Systems",
            "description": "Operating systems concepts"
        },
        {
            "code": "IT2580",
            "name": "Security",
            "long_name": "Information Security",
            "description": "Information security basics"
        },

        # Year 3 Semester 1 Modules
        {
            "code": "IT3010",  # First 3: Year 3, Second 0: Semester 1
            "name": "Project Management",
            "long_name": "Software Project Management",
            "description": "Project management principles"
        },
        {
            "code": "IT3020",
            "name": "DS",
            "long_name": "Data Science",
            "description": "Introduction to data science"
        },
        {
            "code": "IT3030",
            "name": "AI",
            "long_name": "Artificial Intelligence",
            "description": "AI fundamentals"
        },
        {
            "code": "IT3040",
            "name": "Cloud Computing",
            "long_name": "Cloud Computing",
            "description": "Cloud computing concepts"
        },

        # Year 3 Semester 2 Modules
        {
            "code": "IT3550",  # First 3: Year 3, Second 5: Semester 2
            "name": "ML",
            "long_name": "Machine Learning",
            "description": "Machine learning fundamentals"
        },
        {
            "code": "IT3560",
            "name": "Research Methods",
            "long_name": "Research Methods",
            "description": "Research methodology"
        },
        {
            "code": "IT3570",
            "name": "DevOps",
            "long_name": "DevOps Practices",
            "description": "DevOps principles"
        },
        {
            "code": "IT3580",
            "name": "QA",
            "long_name": "Quality Assurance",
            "description": "Software quality assurance"
        },

        # Year 4 Semester 1 Modules
        {
            "code": "IT4010",  # First 4: Year 4, Second 0: Semester 1
            "name": "Research Project",
            "long_name": "Research Project I",
            "description": "Final year research project"
        },
        {
            "code": "IT4020",
            "name": "Enterprise Architecture",
            "long_name": "Enterprise Architecture",
            "description": "Enterprise systems design"
        },
        {
            "code": "IT4030",
            "name": "Business Analytics",
            "long_name": "Business Analytics",
            "description": "Business analytics and intelligence"
        },

        # Year 4 Semester 2 Modules
        {
            "code": "IT4550",  # First 4: Year 4, Second 5: Semester 2
            "name": "Research Project II",
            "long_name": "Research Project II",
            "description": "Final year research project continuation"
        },
        {
            "code": "IT4560",
            "name": "Emerging Technologies",
            "long_name": "Emerging Technologies",
            "description": "Latest technology trends"
        },
        {
            "code": "IT4570",
            "name": "Professional Practice",
            "long_name": "Professional Practice",
            "description": "Professional development"
        }
    ]

def generate_spaces() -> List[Dict]:
    spaces = [
        # Main Building Lecture Halls
        {
            "name": "A401",
            "long_name": "Main Lecture Hall A401",
            "code": "LH401",
            "capacity": 200,
            "attributes": {
                "projector": "Yes",
                "computers": "No",
                "air_conditioned": "Yes"
            }
        },
        {
            "name": "A501",
            "long_name": "Main Lecture Hall A501",
            "code": "LH501",
            "capacity": 200,
            "attributes": {
                "projector": "Yes",
                "computers": "No",
                "air_conditioned": "Yes"
            }
        },
        # Labs
        {
            "name": "B501",
            "long_name": "Computer Lab B501",
            "code": "LAB501",
            "capacity": 60,
            "attributes": {
                "projector": "Yes",
                "computers": "Yes",
                "air_conditioned": "Yes"
            }
        },
        {
            "name": "B502",
            "long_name": "Computer Lab B502",
            "code": "LAB502",
            "capacity": 60,
            "attributes": {
                "projector": "Yes",
                "computers": "Yes",
                "air_conditioned": "Yes"
            }
        }
    ]
    return spaces

def generate_years() -> List[Dict]:
    years = []
    for year in range(1, 5):  # 4 years
        for semester in range(1, 3):  # 2 semesters per year
            for group_num in range(1, 6):  # 5 groups per semester
                years.append({
                    "id": f"Y{year}S{semester}.{group_num}",
                    "year": year,
                    "semester": semester,
                    "group_num": group_num,
                    "size": 40
                })
    return years

def generate_users() -> List[Dict]:
    faculty = []
    students = []
    
    # Generate faculty members (lecturers)
    lecturer_names = [
        ("Chandimal", "Jayawardena"),
        ("Kushani", "Perera"),
        ("Sasika", "Kumarasinghe"),
        ("Dhishan", "Dhammearatchi"),
        ("Uthpala", "Samarakoon"),
        ("Dilshan", "Silva"),
        ("Rajitha", "Dissanayake"),
        ("Thilini", "Fernando"),
        ("Samadhi", "Rathnayaka"),
        ("Kavindi", "Gunawardena")
    ]
    
    for i, (first, last) in enumerate(lecturer_names, 1):
        faculty.append({
            "id": f"FA{i:07d}",
            "first_name": first,
            "last_name": last,
            "username": f"{first.lower()}.{last.lower()}",
            "role": "lecturer",
            "department": random.choice([
                "Computer Science and Software Engineering",
                "Information Technology",
                "Cyber Security"
            ])
        })
    
    # Generate students
    years = generate_years()
    for year in years:
        students.append({
            "id": f"IT{random.randint(100000, 999999)}",
            "first_name": f"Student{random.randint(1, 300)}",
            "last_name": f"Learner{random.randint(1, 300)}",
            "username": f"it{random.randint(100000, 999999)}",
            "role": "student",
            "year_group": year["id"]
        })
    
    return faculty + students

def generate_activities() -> List[Dict]:
    activities = []
    activity_counter = 1
    
    print("\nGenerating activities:")
    # Generate activities for each module
    modules = generate_modules()
    for module in modules:
        year = int(module['code'][2])  # Extract year from module code (IT1xxx -> year 1)
        semester = 2 if int(module['code'][3]) >= 5 else 1  # Semester 1: 0-4, Semester 2: 5-9
        print(f"\nProcessing module: {module['code']} ({module['name']})")
        print(f"Year: {year}, Semester: {semester}")
        
        # Generate subgroup IDs for this year and semester
        subgroup_ids = [f"Y{year}S{semester}.{i}" for i in range(1, 6)]
        print(f"Groups: {', '.join(subgroup_ids)}")
        
        # Lecture (2 hours)
        activities.append({
            "code": f"AC-{activity_counter:03d}",
            "name": f"{module['name']} Lecture",
            "subject": module['code'],
            "teacher_ids": [f"FA{random.randint(1, 10):07d}"],
            "subgroup_ids": subgroup_ids,  # All groups for this year/semester
            "duration": 2,
            "type": "Lecture",
            "space_requirements": ["Lecture Hall"]
        })
        print(f"Created lecture activity for groups: {', '.join(subgroup_ids)}")
        activity_counter += 1
        
        # Tutorial groups (1 hour each)
        for group_num in range(1, 6):
            subgroup_id = f"Y{year}S{semester}.{group_num}"
            activities.append({
                "code": f"AC-{activity_counter:03d}",
                "name": f"{module['name']} Tutorial - Group {group_num}",
                "subject": module['code'],
                "teacher_ids": [f"FA{random.randint(1, 10):07d}"],
                "subgroup_ids": [subgroup_id],
                "duration": 1,
                "type": "Tutorial",
                "space_requirements": ["Tutorial Room", "Lecture Hall"]
            })
            print(f"Created tutorial activity for group: {subgroup_id}")
            activity_counter += 1
        
        # Practical sessions (2 hours each) for programming/technical modules
        if any(keyword in module['name'].lower() for keyword in ['programming', 'database', 'networks', 'web']):
            for group_num in range(1, 6):
                subgroup_id = f"Y{year}S{semester}.{group_num}"
                activities.append({
                    "code": f"AC-{activity_counter:03d}",
                    "name": f"{module['name']} Practical - Group {group_num}",
                    "subject": module['code'],
                    "teacher_ids": [f"FA{random.randint(1, 10):07d}"],
                    "subgroup_ids": [subgroup_id],
                    "duration": 2,
                    "type": "Practical",
                    "space_requirements": ["Computer Lab"]
                })
                print(f"Created practical activity for group: {subgroup_id}")
                activity_counter += 1
    
    print(f"\nTotal activities generated: {activity_counter - 1}")
    return activities

def generate_constraints() -> List[Dict]:
    return [
        {
            "name": "No Teacher Overlap",
            "description": "A teacher cannot be scheduled for multiple activities at the same time",
            "type": "hard",
            "weight": 10
        },
        {
            "name": "No Student Group Overlap",
            "description": "A student group cannot be scheduled for multiple activities at the same time",
            "type": "hard",
            "weight": 10
        },
        {
            "name": "No Room Overlap",
            "description": "A room cannot be scheduled for multiple activities at the same time",
            "type": "hard",
            "weight": 10
        },
        {
            "name": "Room Type Match",
            "description": "Activities must be scheduled in rooms that match their requirements",
            "type": "hard",
            "weight": 10
        },
        {
            "name": "Room Capacity",
            "description": "Room capacity must be sufficient for the student group size",
            "type": "hard",
            "weight": 10
        }
    ]

def generate_complete_dataset():
    dataset = {
        "faculties": generate_faculty_data(),
        "modules": generate_modules(),
        "spaces": generate_spaces(),
        "years": generate_years(),
        "users": generate_users(),
        "activities": generate_activities(),
        "constraints": generate_constraints()
    }
    return dataset

def save_dataset(dataset, filename="sliit_computing_dataset.json"):
    with open(filename, 'w') as f:
        json.dump(dataset, f, indent=2)

if __name__ == "__main__":
    dataset = generate_complete_dataset()
    save_dataset(dataset)
    print("SLIIT Computing dataset generated successfully!")