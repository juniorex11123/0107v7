from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
import os
import uuid
import qrcode
import io
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database setup
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(title="Multi-Tenant Time Tracking System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Owner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OwnerLogin(BaseModel):
    username: str
    password: str

class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CompanyCreate(BaseModel):
    name: str
    admin_username: str
    admin_email: str
    admin_password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    role: str  # "admin" or "user"
    company_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class CompanyRegistration(BaseModel):
    company_name: str
    admin_username: str
    admin_email: str
    admin_password: str

class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    surname: str
    position: str
    number: str
    qr_code: str
    company_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmployeeCreate(BaseModel):
    name: str
    surname: str
    position: str
    number: str

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    position: Optional[str] = None
    number: Optional[str] = None

class TimeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    date: str  # YYYY-MM-DD format
    status: str  # "working" or "completed"
    last_scan_time: Optional[datetime] = None

class TimeEntryEdit(BaseModel):
    check_in: Optional[str] = None  # HH:MM format
    check_out: Optional[str] = None  # HH:MM format
    date: Optional[str] = None  # YYYY-MM-DD format

class TimeEntryCreate(BaseModel):
    employee_id: str
    check_in: str  # HH:MM format
    check_out: Optional[str] = None  # HH:MM format
    date: str  # YYYY-MM-DD format

class QRScanRequest(BaseModel):
    qr_data: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_type: str = payload.get("type", "user")  # "user" or "owner"
        
        if username is None:
            raise credentials_exception
            
        if user_type == "owner":
            # Owner authentication
            owner = await db.owners.find_one({"username": username})
            if owner is None:
                raise credentials_exception
            return {"type": "owner", "data": Owner(**owner)}
        else:
            # Regular user authentication
            company_id: str = payload.get("company_id")
            if company_id is None:
                raise credentials_exception
            user = await db.users.find_one({"username": username, "company_id": company_id})
            if user is None:
                raise credentials_exception
            return {"type": "user", "data": User(**user)}
    except jwt.PyJWTError:
        raise credentials_exception

async def get_current_owner(current_auth = Depends(get_current_user)):
    if current_auth["type"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )
    return current_auth["data"]

async def get_current_regular_user(current_auth = Depends(get_current_user)):
    if current_auth["type"] != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Regular user access required"
        )
    return current_auth["data"]

async def get_admin_user(current_user: User = Depends(get_current_regular_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_company_context(current_user: User = Depends(get_current_regular_user)):
    """Get company context for filtering data"""
    return current_user.company_id

# Owner Authentication and Management
@app.post("/api/owner/login", response_model=Token)
async def owner_login(login_data: OwnerLogin):
    owner = await db.owners.find_one({"username": login_data.username})
    if not owner or not verify_password(login_data.password, owner["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": owner["username"],
            "type": "owner"
        }, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": owner["id"],
            "username": owner["username"],
            "email": owner["email"],
            "type": "owner"
        }
    }

@app.get("/api/owner/companies")
async def get_all_companies(current_owner: Owner = Depends(get_current_owner)):
    """Get all companies (owner only)"""
    companies = await db.companies.find().to_list(1000)
    result = []
    
    for company in companies:
        # Get company admin count
        admin_count = await db.users.count_documents({
            "company_id": company["id"],
            "role": "admin"
        })
        
        # Get total user count
        user_count = await db.users.count_documents({
            "company_id": company["id"]
        })
        
        # Get employee count
        employee_count = await db.employees.count_documents({
            "company_id": company["id"]
        })
        
        company_data = Company(**company).dict()
        company_data.update({
            "admin_count": admin_count,
            "user_count": user_count,
            "employee_count": employee_count
        })
        result.append(company_data)
    
    return result

@app.post("/api/owner/companies")
async def create_company(
    company_data: CompanyCreate,
    current_owner: Owner = Depends(get_current_owner)
):
    """Create a new company with admin user (owner only)"""
    # Check if company name already exists
    existing_company = await db.companies.find_one({"name": company_data.name})
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firma o tej nazwie już istnieje"
        )
    
    # Check if admin username already exists
    existing_user = await db.users.find_one({"username": company_data.admin_username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nazwa użytkownika już istnieje"
        )
    
    # Create company
    company = Company(
        name=company_data.name,
        owner_id=current_owner.id
    )
    await db.companies.insert_one(company.dict())
    
    # Create admin user
    admin_user = User(
        username=company_data.admin_username,
        email=company_data.admin_email,
        password_hash=get_password_hash(company_data.admin_password),
        role="admin",
        company_id=company.id
    )
    await db.users.insert_one(admin_user.dict())
    
    return {
        "message": "Company created successfully",
        "company": company.dict(),
        "admin_user": {
            "id": admin_user.id,
            "username": admin_user.username,
            "email": admin_user.email,
            "role": admin_user.role
        }
    }

@app.delete("/api/owner/companies/{company_id}")
async def delete_company(
    company_id: str,
    current_owner: Owner = Depends(get_current_owner)
):
    """Delete a company and all its data (owner only)"""
    # Check if company exists
    company = await db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Delete all company data
    await db.users.delete_many({"company_id": company_id})
    await db.employees.delete_many({"company_id": company_id})
    await db.time_entries.delete_many({"employee_id": {"$in": []}})  # Will be updated with proper employee IDs
    
    # Get all employee IDs first, then delete time entries
    employees = await db.employees.find({"company_id": company_id}).to_list(1000)
    employee_ids = [emp["id"] for emp in employees]
    if employee_ids:
        await db.time_entries.delete_many({"employee_id": {"$in": employee_ids}})
    
    # Delete employees
    await db.employees.delete_many({"company_id": company_id})
    
    # Delete company
    await db.companies.delete_one({"id": company_id})
    
    return {"message": "Company and all its data deleted successfully"}

# Company Self-Registration
@app.post("/api/auth/register-company", response_model=Token)
async def register_company(company_data: CompanyRegistration):
    """Allow companies to self-register with admin user"""
    # Check if company name already exists
    existing_company = await db.companies.find_one({"name": company_data.company_name})
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firma o tej nazwie już istnieje"
        )
    
    # Check if admin username already exists
    existing_user = await db.users.find_one({"username": company_data.admin_username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nazwa użytkownika już istnieje"
        )
    
    # Create company
    company = Company(
        name=company_data.company_name,
        owner_id="system"  # For self-registered companies
    )
    await db.companies.insert_one(company.dict())
    
    # Create admin user
    admin_user = User(
        username=company_data.admin_username,
        email=company_data.admin_email,
        password_hash=get_password_hash(company_data.admin_password),
        role="admin",
        company_id=company.id
    )
    await db.users.insert_one(admin_user.dict())
    
    # Generate access token for the new admin
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": admin_user.username,
            "company_id": admin_user.company_id,
            "role": admin_user.role,
            "type": "user"
        }, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": admin_user.id,
            "username": admin_user.username,
            "email": admin_user.email,
            "role": admin_user.role,
            "company_id": admin_user.company_id,
            "type": "user"
        }
    }

# Universal Authentication - handles both owners and regular users
@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # First check if user is an owner
    owner = await db.owners.find_one({"username": user_data.username})
    if owner and verify_password(user_data.password, owner["password_hash"]):
        # Owner login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": owner["username"],
                "type": "owner"
            }, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": owner["id"],
                "username": owner["username"],
                "email": owner["email"],
                "type": "owner"
            }
        }
    
    # If not owner, check regular users
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "company_id": user["company_id"],
            "role": user["role"],
            "type": "user"
        }, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "company_id": user["company_id"],
            "type": "user"
        }
    }

@app.get("/api/auth/me")
async def get_me(current_auth = Depends(get_current_user)):
    if current_auth["type"] == "owner":
        owner = current_auth["data"]
        return {
            "id": owner.id,
            "username": owner.username,
            "email": owner.email,
            "type": "owner"
        }
    else:
        user = current_auth["data"]
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "company_id": user.company_id,
            "type": "user"
        }

# Company Management (Admin only)
@app.get("/api/company/info")
async def get_company_info(current_user: User = Depends(get_current_regular_user)):
    company = await db.companies.find_one({"id": current_user.company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return Company(**company)

@app.get("/api/company/users")
async def get_company_users(current_user: User = Depends(get_admin_user)):
    users = await db.users.find({"company_id": current_user.company_id}).to_list(1000)
    return [
        {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"]
        }
        for user in users
    ]

@app.post("/api/company/users")
async def create_company_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user)
):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nazwa użytkownika już istnieje"
        )
    
    # Create user in the same company as admin
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        company_id=current_user.company_id
    )
    await db.users.insert_one(new_user.dict())
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "company_id": new_user.company_id
    }

@app.delete("/api/company/users/{user_id}")
async def delete_company_user(
    user_id: str,
    current_user: User = Depends(get_admin_user)
):
    # Check if user exists and belongs to the same company
    user_to_delete = await db.users.find_one({"id": user_id, "company_id": current_user.company_id})
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie możesz usunąć własnego konta"
        )
    
    result = await db.users.delete_one({"id": user_id, "company_id": current_user.company_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Employee endpoints (Admin only, company-scoped)
@app.post("/api/employees", response_model=Employee)
async def create_employee(
    employee_data: EmployeeCreate,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    # Check if employee number already exists in this company
    existing_employee = await db.employees.find_one({
        "number": employee_data.number,
        "company_id": company_id
    })
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Numer pracownika już istnieje w tej firmie"
        )
    
    # Generate unique QR code data
    qr_data = f"EMP_{company_id}_{employee_data.number}_{str(uuid.uuid4())[:8]}"
    qr_code = generate_qr_code(qr_data)
    
    employee = Employee(
        name=employee_data.name,
        surname=employee_data.surname,
        position=employee_data.position,
        number=employee_data.number,
        qr_code=qr_code,
        company_id=company_id
    )
    
    await db.employees.insert_one(employee.dict())
    return employee

@app.get("/api/employees", response_model=List[Employee])
async def get_employees(
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    employees = await db.employees.find({"company_id": company_id}).to_list(1000)
    return [Employee(**emp) for emp in employees]

@app.put("/api/employees/{employee_id}", response_model=Employee)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    employee = await db.employees.find_one({"id": employee_id, "company_id": company_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = employee_data.dict(exclude_unset=True)
    if update_data:
        # Check if number is being changed and if it already exists
        if "number" in update_data:
            existing_employee = await db.employees.find_one({
                "number": update_data["number"],
                "company_id": company_id,
                "id": {"$ne": employee_id}
            })
            if existing_employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Numer pracownika już istnieje w tej firmie"
                )
        
        await db.employees.update_one(
            {"id": employee_id, "company_id": company_id},
            {"$set": update_data}
        )
    
    updated_employee = await db.employees.find_one({"id": employee_id, "company_id": company_id})
    return Employee(**updated_employee)

@app.delete("/api/employees/{employee_id}")
async def delete_employee(
    employee_id: str,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    result = await db.employees.delete_one({"id": employee_id, "company_id": company_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Also delete related time entries
    await db.time_entries.delete_many({"employee_id": employee_id})
    
    return {"message": "Employee deleted successfully"}

# Time tracking endpoints (company-scoped)
@app.post("/api/time/scan")
async def scan_qr(
    scan_data: QRScanRequest,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_current_regular_user)
):
    # Find employee by QR data
    qr_data = scan_data.qr_data
    
    # Extract company and employee info from QR data (format: EMP_COMPANYID_NUMBER_UUID)
    if not qr_data.startswith("EMP_"):
        raise HTTPException(status_code=400, detail="Invalid QR code")
    
    try:
        parts = qr_data.split("_")
        if len(parts) < 3:
            raise HTTPException(status_code=400, detail="Invalid QR code format")
        qr_company_id = parts[1]
        employee_number = parts[2]
        
        # Verify QR code belongs to user's company
        if qr_company_id != company_id:
            raise HTTPException(status_code=403, detail="QR kod nie należy do Twojej firmy")
        
        employee = await db.employees.find_one({
            "number": employee_number,
            "company_id": company_id
        })
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid QR code format")
    
    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now()
    
    # Check if there's an active time entry for today
    existing_entry = await db.time_entries.find_one({
        "employee_id": employee["id"],
        "date": today,
        "status": "working"
    })
    
    # Cooldown check - prevent scanning within 5 seconds
    COOLDOWN_SECONDS = 5
    
    if existing_entry and existing_entry.get("last_scan_time"):
        last_scan = existing_entry["last_scan_time"]
        if isinstance(last_scan, str):
            last_scan = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
        elif hasattr(last_scan, 'replace'):
            last_scan = last_scan.replace(tzinfo=None) if last_scan.tzinfo else last_scan
        
        time_diff = (current_time - last_scan).total_seconds()
        if time_diff < COOLDOWN_SECONDS:
            remaining_seconds = int(COOLDOWN_SECONDS - time_diff)
            raise HTTPException(
                status_code=429, 
                detail=f"Poczekaj {remaining_seconds} sekund przed kolejnym skanowaniem"
            )
    
    # Check for completed entries today to prevent multiple scans
    completed_entry = await db.time_entries.find_one({
        "employee_id": employee["id"],
        "date": today,
        "status": "completed"
    })
    
    if completed_entry and completed_entry.get("last_scan_time"):
        last_scan = completed_entry["last_scan_time"]
        if isinstance(last_scan, str):
            last_scan = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
        elif hasattr(last_scan, 'replace'):
            last_scan = last_scan.replace(tzinfo=None) if last_scan.tzinfo else last_scan
        
        time_diff = (current_time - last_scan).total_seconds()
        if time_diff < COOLDOWN_SECONDS:
            remaining_seconds = int(COOLDOWN_SECONDS - time_diff)
            raise HTTPException(
                status_code=429, 
                detail=f"Poczekaj {remaining_seconds} sekund przed kolejnym skanowaniem"
            )
    
    if existing_entry:
        # Check out - end work
        check_out_time = datetime.now()
        await db.time_entries.update_one(
            {"id": existing_entry["id"]},
            {
                "$set": {
                    "check_out": check_out_time,
                    "status": "completed",
                    "last_scan_time": check_out_time
                }
            }
        )
        return {
            "action": "check_out",
            "employee": f"{employee['name']} {employee['surname']}",
            "time": check_out_time.strftime("%H:%M:%S"),
            "message": "Pomyślnie zakończono pracę",
            "cooldown_seconds": COOLDOWN_SECONDS
        }
    else:
        # Check in - start work
        check_in_time = datetime.now()
        time_entry = TimeEntry(
            employee_id=employee["id"],
            check_in=check_in_time,
            date=today,
            status="working",
            last_scan_time=check_in_time
        )
        await db.time_entries.insert_one(time_entry.dict())
        
        return {
            "action": "check_in",
            "employee": f"{employee['name']} {employee['surname']}",
            "time": check_in_time.strftime("%H:%M:%S"),
            "message": "Pomyślnie rozpoczęto pracę",
            "cooldown_seconds": COOLDOWN_SECONDS
        }

@app.get("/api/time/entries/{employee_id}")
async def get_employee_time_entries(
    employee_id: str,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    # Verify employee belongs to company
    employee = await db.employees.find_one({"id": employee_id, "company_id": company_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    entries = await db.time_entries.find({"employee_id": employee_id}).to_list(1000)
    return [TimeEntry(**entry) for entry in entries]

@app.get("/api/time/entries")
async def get_all_time_entries(
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    """Get all time entries for company with employee information"""
    # Get all employees for this company
    employees = await db.employees.find({"company_id": company_id}).to_list(1000)
    employee_ids = [emp["id"] for emp in employees]
    employee_map = {emp["id"]: emp for emp in employees}
    
    # Get time entries for company employees
    entries = await db.time_entries.find({"employee_id": {"$in": employee_ids}}).sort("date", -1).to_list(1000)
    
    # Combine entries with employee data
    result = []
    for entry in entries:
        employee = employee_map.get(entry["employee_id"])
        if employee:
            entry_data = TimeEntry(**entry).dict()
            entry_data["employee_name"] = f"{employee['name']} {employee['surname']}"
            entry_data["employee_number"] = employee["number"]
            entry_data["employee_position"] = employee["position"]
            
            # Calculate hours worked if both check_in and check_out exist
            if entry_data.get("check_in") and entry_data.get("check_out"):
                check_in = entry_data["check_in"]
                check_out = entry_data["check_out"]
                if isinstance(check_in, str):
                    check_in = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
                if isinstance(check_out, str):
                    check_out = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
                
                duration = check_out - check_in
                hours_worked = duration.total_seconds() / 3600
                entry_data["hours_worked"] = round(hours_worked, 2)
            else:
                entry_data["hours_worked"] = None
            
            result.append(entry_data)
    
    return result

@app.put("/api/time/entries/{entry_id}")
async def update_time_entry(
    entry_id: str,
    entry_data: TimeEntryEdit,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    """Update a time entry (admin only, company-scoped)"""
    # Get entry and verify it belongs to company employee
    entry = await db.time_entries.find_one({"id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Verify employee belongs to company
    employee = await db.employees.find_one({"id": entry["employee_id"], "company_id": company_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    update_fields = {}
    
    # Update date if provided
    if entry_data.date:
        update_fields["date"] = entry_data.date
    
    # Update check_in if provided
    if entry_data.check_in:
        date_str = entry_data.date or entry["date"]
        check_in_datetime = datetime.strptime(f"{date_str} {entry_data.check_in}", "%Y-%m-%d %H:%M")
        update_fields["check_in"] = check_in_datetime
    
    # Update check_out if provided
    if entry_data.check_out:
        date_str = entry_data.date or entry["date"]
        check_out_datetime = datetime.strptime(f"{date_str} {entry_data.check_out}", "%Y-%m-%d %H:%M")
        update_fields["check_out"] = check_out_datetime
        
        # Set status to completed if both times exist
        if "check_in" in update_fields or entry.get("check_in"):
            update_fields["status"] = "completed"
    
    if update_fields:
        await db.time_entries.update_one(
            {"id": entry_id},
            {"$set": update_fields}
        )
    
    updated_entry = await db.time_entries.find_one({"id": entry_id})
    return TimeEntry(**updated_entry)

@app.post("/api/time/entries")
async def create_time_entry(
    entry_data: TimeEntryCreate,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    """Create a manual time entry (admin only, company-scoped)"""
    # Verify employee exists and belongs to company
    employee = await db.employees.find_one({"id": entry_data.employee_id, "company_id": company_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Parse times
    check_in_datetime = datetime.strptime(f"{entry_data.date} {entry_data.check_in}", "%Y-%m-%d %H:%M")
    check_out_datetime = None
    status = "working"
    
    if entry_data.check_out:
        check_out_datetime = datetime.strptime(f"{entry_data.date} {entry_data.check_out}", "%Y-%m-%d %H:%M")
        status = "completed"
    
    time_entry = TimeEntry(
        employee_id=entry_data.employee_id,
        check_in=check_in_datetime,
        check_out=check_out_datetime,
        date=entry_data.date,
        status=status,
        last_scan_time=datetime.now()
    )
    
    await db.time_entries.insert_one(time_entry.dict())
    return time_entry

@app.delete("/api/time/entries/{entry_id}")
async def delete_time_entry(
    entry_id: str,
    company_id: str = Depends(get_company_context),
    current_user: User = Depends(get_admin_user)
):
    """Delete a time entry (admin only, company-scoped)"""
    # Get entry and verify it belongs to company employee
    entry = await db.time_entries.find_one({"id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Verify employee belongs to company
    employee = await db.employees.find_one({"id": entry["employee_id"], "company_id": company_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    result = await db.time_entries.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    return {"message": "Time entry deleted successfully"}

@app.get("/api/")
async def root():
    return {"message": "Multi-Tenant Time Tracking System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)