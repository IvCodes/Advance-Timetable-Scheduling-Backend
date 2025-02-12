import json

MODULE_CODES = {
    "SEM101": ["CS101", "CS102", "CS103", "CS104", "CS105"],
    "SEM102": ["CS111", "CS112", "CS113", "CS114", "CS115"],
    "SEM201": ["CS201", "CS202", "CS203", "CS204", "CS205"],
    "SEM202": ["CS211", "CS212", "CS213", "CS214", "CS215"],
    "SEM301": ["CS301", "CS302", "CS303", "CS304", "CS305"],
    "SEM302": ["CS311", "CS312", "CS313", "CS314", "CS315"],
    "SEM401": ["CS401", "CS402", "CS403", "CS404", "CS405"],
    "SEM402": ["CS411", "CS412", "CS413", "CS414", "CS415"]
}

def generate_student_id(index):
    return f"ST{index:07d}"

def generate_username(first_name, last_name):
    return f"{first_name.lower()}{last_name.lower()[0]}123"

def generate_email(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}@example.com"

def assign_semester(index):
    semesters = list(MODULE_CODES.keys())
    return semesters[index % len(semesters)]

def get_year_from_semester(semester):
    return int(semester[3])

def transform_students(input_file, output_file):
    with open(input_file, 'r') as f:
        students = json.load(f)

    transformed_students = []

    for index, student in enumerate(students):
        semester = assign_semester(index)
        year = get_year_from_semester(semester)

        transformed_student = {
            "id": generate_student_id(index + 1),
            "first_name": student["first_name"],
            "last_name": student["last_name"],
            "username": generate_username(student["first_name"], student["last_name"]),
            "email": generate_email(student["first_name"], student["last_name"]),
            "telephone": "+94771234567",
            "position": "Undergraduate",
            "role": "student",
            "hashed_password": "test123",
            "subjects": MODULE_CODES[semester],
            "year": year,
            "subgroup": semester
        }

        transformed_students.append(transformed_student)

    with open(output_file, 'w') as f:
        json.dump(transformed_students, f, indent=4)

input_file = "./students.json"
output_file = "./transformed_students.json"

transform_students(input_file, output_file)
