from fastapi import APIRouter, HTTPException, Depends, status
from app.models.user_model import User, UserCreate, LoginModel
from app.utils.database import db
from passlib.context import CryptContext
from typing import List
from app.utils.jwt_util import create_access_token, verify_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")

SECRET_KEY = "TimeTableWhiz" 
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        print(f"Validating token: {token[:15]}...")
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            print("No user_id in token payload")
            raise HTTPException(status_code=401, detail="Invalid token - no user ID")
            
        print(f"Looking up user with ID: {user_id}")
        user = db["Users"].find_one({"id": user_id})
        
        if not user:
            print(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")
            
        print(f"Authenticated user: {user['username']}, role: {user['role']}")
        return user
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    try:
        print(f"Registration attempt with data: {user.dict(exclude={'password'})}")
        
        # Check for existing users with the same ID, username, or email
        existing_user = db["Users"].find_one({
            "$or": [
                {"username": user.username}, 
                {"id": user.id}, 
                {"email": user.email}
            ]
        })
        
        if existing_user:
            print(f"Registration failed: User already exists with ID {user.id} or username {user.username}")
            raise HTTPException(status_code=400, detail="User with this ID, username, or email already exists")
        
        # Role-specific validation
        if user.role == "student":
            # Validate year if provided
            if user.year:
                year = db["Years"].find_one({"name": user.year})
                if not year:
                    print(f"Registration failed: Year {user.year} not found")
                    raise HTTPException(status_code=404, detail="Year not found")
                
                if user.semester and user.semester not in ["semester_1", "semester_2"]:
                    print(f"Registration failed: Invalid semester {user.semester}")
                    raise HTTPException(status_code=400, detail="Invalid semester specified")
        
        # Prepare user data for insertion
        user_dict = user.dict()
        user_dict["hashed_password"] = hash_password(user_dict.pop("password"))
        
        # Ensure admin fields are properly set
        if user.role == "admin":
            print(f"Setting admin-specific fields for user {user.id}")
            user_dict["year"] = None
            user_dict["subgroup"] = None
            user_dict["faculty"] = None
            
            # Ensure position is set for admin
            if not user_dict.get("position"):
                user_dict["position"] = "Administrator"
                print(f"Set default position 'Administrator' for admin user {user.id}")
        
        # Insert user
        print(f"Inserting new user with ID: {user.id}, role: {user.role}")
        result = db["Users"].insert_one(user_dict)
        
        # Retrieve the created user
        created_user = db["Users"].find_one({"_id": result.inserted_id})
        if not created_user:
            print("Failed to create user: User not found after insertion")
            raise HTTPException(status_code=500, detail="Failed to create user.")
        
        print(f"User created successfully: {user.username}, role: {user.role}")
        
        # Generate token for newly registered user
        token = create_access_token({"sub": user.id})
        
        # Return user data with token
        user_response = User(**created_user)
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@router.post("/login", response_model=dict)
async def login_user(credentials: LoginModel):
    try:
        identifier = credentials.username  # This could be either username or ID
        print(f"Login attempt with identifier: {identifier}")
        
        # Try to find by username first
        user = db["Users"].find_one({"username": identifier})
        
        # If not found, try to find by ID
        if not user:
            print(f"User not found by username, trying ID: {identifier}")
            user = db["Users"].find_one({"id": identifier})
            
        if not user:
            print(f"Login failed: User not found by username or ID: {identifier}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # For debugging
        print(f"Found user: {user['username']} with ID: {user['id']}")
        
        if not verify_password(credentials.password, user["hashed_password"]):
            print(f"Login failed: Invalid password for user: {user['username']}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create JWT token
        token = create_access_token({"sub": user["id"]})
        
        print(f"Login successful for: {user['username']}, role: {user['role']}")
        return {
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user.get("email", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    This endpoint is specifically for Swagger UI authentication.
    """
    try:
        print(f"OAuth2 token request for username: {form_data.username}")
        # Try to find by username first
        user = db["Users"].find_one({"username": form_data.username})
        
        # If not found, try to find by ID
        if not user:
            print(f"User not found by username, trying ID: {form_data.username}")
            user = db["Users"].find_one({"id": form_data.username})
            
        if not user:
            print(f"OAuth2 login failed: User not found by username or ID: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not verify_password(form_data.password, user["hashed_password"]):
            print(f"OAuth2 login failed: Invalid password for user: {user['username']}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token with user ID in the sub claim
        access_token = create_access_token({"sub": user["id"]})
        
        print(f"OAuth2 login successful for: {user['username']}, role: {user['role']}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user["role"],
            "user_id": user["id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"OAuth2 login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/all", response_model=List[User])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    users = list(db["Users"].find())
    return users

@router.get("/faculty", response_model=List[User])
async def get_all_faculty(current_user: dict = Depends(get_current_user)):
    # This endpoint is protected by get_current_user, which ensures only authenticated users can access the faculty list
    faculty_members = list(db["Users"].find({"role": "faculty"}))
    return faculty_members

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, updated_user: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    hashed_password = hash_password(updated_user.password)
    updated_data = updated_user.dict()
    updated_data["hashed_password"] = hashed_password
    updated_data.pop("password", None)

    if "year" in updated_user:
        year = db["Years"].find_one({"name": updated_user["year"]})
        if not year:
            raise HTTPException(status_code=404, detail="Year not found")
    
    if "semester" in updated_user:
        if updated_user["semester"] not in ["semester_1", "semester_2"]:
            raise HTTPException(status_code=400, detail="Invalid semester specified")
        
    result = db["Users"].update_one({"id": user_id}, {"$set": updated_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return db["Users"].find_one({"id": user_id})

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    result = db["Users"].delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.get("/", response_model=List[User])
async def list_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    users = list(db["Users"].find())
    return users

#---------------------------------------------------------------------------------------------------------------

@router.post("/{user_id}/subjects")
async def add_subjects(user_id: str, subjects: List[str], current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "faculty":
        raise HTTPException(status_code=400, detail="Only faculty members can have subjects")

    updated_subjects = set(user.get("subjects", [])) | set(subjects)
    db["Users"].update_one({"id": user_id}, {"$set": {"subjects": list(updated_subjects)}})
    return {"message": "Subjects added successfully", "subjects": list(updated_subjects)}

@router.delete("/{user_id}/subjects/{subject_code}")
async def remove_subject(user_id: str, subject_code: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "faculty":
        raise HTTPException(status_code=400, detail="Only faculty members can have subjects")

    updated_subjects = [subj for subj in user.get("subjects", []) if subj != subject_code]
    db["Users"].update_one({"id": user_id}, {"$set": {"subjects": updated_subjects}})
    return {"message": f"Subject {subject_code} removed successfully", "subjects": updated_subjects}

@router.put("/{user_id}/target_hours")
async def update_target_hours(user_id: str, target_hours: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "faculty":
        raise HTTPException(status_code=400, detail="Only faculty members can have target hours")

    db["Users"].update_one({"id": user_id}, {"$set": {"target_hours": target_hours}})
    return {"message": f"Target hours updated successfully to {target_hours}"}

#---------------------------------------------------------------------------------------------------------

@router.put("/users/{user_id}/year")
async def assign_year_to_student(user_id: str, year: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "student":
        raise HTTPException(status_code=400, detail="Year can only be assigned to students")
    valid_year = db["Years"].find_one({"name": year})
    if not valid_year:
        raise HTTPException(status_code=400, detail="Invalid year")
    db["Users"].update_one({"id": user_id}, {"$set": {"year": year}})
    return {"message": f"Year {year} assigned to user {user_id}"}

@router.delete("/users/{user_id}/year")
async def remove_year_from_student(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "student":
        raise HTTPException(status_code=400, detail="Year can only be removed from students")
    db["Users"].update_one({"id": user_id}, {"$unset": {"year": ""}})
    return {"message": f"Year removed from user {user_id}"}

@router.get("/check-id-exists/{user_id}")
async def check_id_exists(user_id: str):
    """
    Check if a user ID already exists in the database.
    """
    existing_user = db["Users"].find_one({"id": user_id})
    return {"exists": existing_user is not None}
