from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import bcrypt
import jwt
import uuid
import secrets
import string
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, timedelta, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get("JWT_SECRET", "earnhub-dev-secret-change-in-prod")
JWT_ALG = "HS256"
ACCESS_TTL = timedelta(days=7)
FIXED_OTP = "123456"

app = FastAPI(title="EarnHub API")
api = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_pw(pw: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), h.encode())
    except Exception:
        return False


def create_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role, "exp": now_utc() + ACCESS_TTL}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def gen_referral_code(name: str) -> str:
    base = "".join(c for c in name.upper() if c.isalpha())[:4] or "USER"
    return base + "".join(secrets.choice(string.digits) for _ in range(4))


async def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# ---------- MODELS ----------
class SignupReq(BaseModel):
    full_name: str
    mobile: str
    email: EmailStr
    password: str = Field(min_length=6)
    city: str
    state: str
    referral_code: Optional[str] = None


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class OTPReq(BaseModel):
    email: EmailStr
    otp: str


class ForgotReq(BaseModel):
    email: EmailStr


class ResetReq(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=6)


class TaskCreate(BaseModel):
    title: str
    description: str
    category: str
    requirements: Optional[str] = ""
    budget: float
    deadline: Optional[str] = None
    workers_needed: int = 1
    location: str
    image_base64: Optional[str] = None


class ProofSubmit(BaseModel):
    note: Optional[str] = ""
    attachments: List[str] = []  # base64 strings


class WithdrawReq(BaseModel):
    amount: float
    method: Literal["upi", "bank", "paytm"]
    details: dict


class DocUpload(BaseModel):
    doc_type: Literal["aadhaar", "pan", "passbook", "address"]
    file_base64: str


class TicketReq(BaseModel):
    category: str
    description: str
    screenshot_base64: Optional[str] = None


class AdminAction(BaseModel):
    action: Literal["approve", "reject"]
    note: Optional[str] = ""


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    avatar_base64: Optional[str] = None


# ---------- AUTH ----------
@api.post("/auth/signup")
async def signup(req: SignupReq):
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(400, "Email already registered")
    user_id = str(uuid.uuid4())
    ref_code = gen_referral_code(req.full_name)
    doc = {
        "id": user_id,
        "full_name": req.full_name,
        "mobile": req.mobile,
        "email": req.email,
        "password": hash_pw(req.password),
        "city": req.city,
        "state": req.state,
        "role": "user",
        "referral_code": ref_code,
        "referred_by": req.referral_code,
        "avatar_base64": None,
        "rating": 5.0,
        "tasks_completed": 0,
        "streak": 0,
        "level": "Bronze",
        "created_at": now_utc().isoformat(),
    }
    await db.users.insert_one(doc)
    await db.wallets.insert_one({
        "user_id": user_id, "balance": 0.0, "total_earned": 0.0, "total_withdrawn": 0.0, "pending": 0.0
    })
    # Referral reward
    if req.referral_code:
        ref_user = await db.users.find_one({"referral_code": req.referral_code})
        if ref_user:
            await db.wallets.update_one(
                {"user_id": ref_user["id"]},
                {"$inc": {"balance": 50.0, "total_earned": 50.0}}
            )
            await db.transactions.insert_one({
                "id": str(uuid.uuid4()), "user_id": ref_user["id"],
                "type": "referral", "amount": 50.0, "status": "completed",
                "note": f"Referral bonus for {req.full_name}",
                "created_at": now_utc().isoformat()
            })
            await db.referrals.insert_one({
                "id": str(uuid.uuid4()),
                "referrer_id": ref_user["id"], "referred_id": user_id,
                "reward": 50.0, "created_at": now_utc().isoformat()
            })
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()), "user_id": ref_user["id"],
                "title": "Referral Reward!", "body": f"You earned ₹50 - {req.full_name} joined using your code",
                "type": "referral", "read": False, "created_at": now_utc().isoformat()
            })
    return {"ok": True, "user_id": user_id, "message": "OTP sent (use 123456)"}


@api.post("/auth/login")
async def login(req: LoginReq):
    user = await db.users.find_one({"email": req.email})
    if not user or not verify_pw(req.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    return {"requires_otp": True, "email": req.email, "message": "OTP sent (use 123456)"}


@api.post("/auth/verify-otp")
async def verify_otp(req: OTPReq):
    if req.otp != FIXED_OTP:
        raise HTTPException(401, "Invalid OTP")
    user = await db.users.find_one({"email": req.email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    token = create_token(user["id"], user["role"])
    return {"access_token": token, "user": user}


@api.post("/auth/forgot-password")
async def forgot(req: ForgotReq):
    user = await db.users.find_one({"email": req.email})
    if not user:
        # don't reveal
        return {"message": "If account exists, OTP sent. Use 123456 for demo."}
    return {"message": "OTP sent. Use 123456 for demo."}


@api.post("/auth/reset-password")
async def reset(req: ResetReq):
    if req.otp != FIXED_OTP:
        raise HTTPException(401, "Invalid OTP")
    user = await db.users.find_one({"email": req.email})
    if not user:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password": hash_pw(req.new_password)}})
    return {"ok": True}


@api.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return user


@api.put("/auth/me")
async def update_me(req: ProfileUpdate, user=Depends(get_current_user)):
    update = {k: v for k, v in req.dict().items() if v is not None}
    if update:
        await db.users.update_one({"id": user["id"]}, {"$set": update})
    return await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})


# ---------- TASKS ----------
@api.get("/tasks")
async def list_tasks(category: Optional[str] = None, search: Optional[str] = None,
                     sort: Optional[str] = "latest", user=Depends(get_current_user)):
    q = {"status": "open"}
    if category and category != "All":
        q["category"] = category
    if search:
        q["title"] = {"$regex": search, "$options": "i"}
    cursor = db.tasks.find(q, {"_id": 0})
    if sort == "high_paying":
        cursor = cursor.sort("budget", -1)
    else:
        cursor = cursor.sort("created_at", -1)
    return await cursor.to_list(200)


@api.post("/tasks")
async def create_task(req: TaskCreate, user=Depends(get_current_user)):
    task = {
        "id": str(uuid.uuid4()),
        "posted_by": user["id"],
        "posted_by_name": user["full_name"],
        "title": req.title,
        "description": req.description,
        "category": req.category,
        "requirements": req.requirements,
        "budget": req.budget,
        "deadline": req.deadline,
        "workers_needed": req.workers_needed,
        "location": req.location,
        "image_base64": req.image_base64,
        "status": "open",  # open -> in_progress -> under_review -> completed
        "created_at": now_utc().isoformat(),
        "distance_km": 2.5,
    }
    await db.tasks.insert_one(task)
    task.pop("_id", None)
    return task


@api.get("/tasks/mine")
async def my_tasks(user=Depends(get_current_user)):
    accepts = await db.task_acceptances.find({"user_id": user["id"]}, {"_id": 0}).to_list(500)
    result = []
    for a in accepts:
        task = await db.tasks.find_one({"id": a["task_id"]}, {"_id": 0})
        if task:
            result.append({**task, "acceptance_status": a["status"], "acceptance_id": a["id"]})
    return result


@api.post("/tasks/{task_id}/accept")
async def accept_task(task_id: str, user=Depends(get_current_user)):
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "open":
        raise HTTPException(400, "Task not available")
    existing = await db.task_acceptances.find_one({"task_id": task_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(400, "Already accepted")
    acc = {
        "id": str(uuid.uuid4()),
        "task_id": task_id,
        "user_id": user["id"],
        "status": "in_progress",
        "accepted_at": now_utc().isoformat(),
    }
    await db.task_acceptances.insert_one(acc)
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": user["id"],
        "title": "Task Accepted", "body": f"You accepted: {task['title']}",
        "type": "task", "read": False, "created_at": now_utc().isoformat()
    })
    return {"ok": True}


@api.post("/tasks/{task_id}/submit-proof")
async def submit_proof(task_id: str, req: ProofSubmit, user=Depends(get_current_user)):
    acc = await db.task_acceptances.find_one({"task_id": task_id, "user_id": user["id"]})
    if not acc:
        raise HTTPException(404, "Task not accepted")
    sub = {
        "id": str(uuid.uuid4()),
        "task_id": task_id,
        "user_id": user["id"],
        "note": req.note,
        "attachments": req.attachments,
        "status": "under_review",
        "created_at": now_utc().isoformat(),
    }
    await db.task_submissions.insert_one(sub)
    await db.task_acceptances.update_one({"id": acc["id"]}, {"$set": {"status": "under_review"}})
    # also lock pending amount
    task = await db.tasks.find_one({"id": task_id})
    if task:
        await db.wallets.update_one({"user_id": user["id"]}, {"$inc": {"pending": task["budget"]}})
    return {"ok": True}


# ---------- WALLET ----------
@api.get("/wallet")
async def get_wallet(user=Depends(get_current_user)):
    w = await db.wallets.find_one({"user_id": user["id"]}, {"_id": 0})
    if not w:
        w = {"user_id": user["id"], "balance": 0.0, "total_earned": 0.0, "total_withdrawn": 0.0, "pending": 0.0}
        await db.wallets.insert_one(w.copy())
    return w


@api.get("/transactions")
async def transactions(user=Depends(get_current_user)):
    return await db.transactions.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(500)


@api.post("/wallet/withdraw")
async def withdraw(req: WithdrawReq, user=Depends(get_current_user)):
    if req.amount < 100:
        raise HTTPException(400, "Minimum withdrawal is ₹100")
    w = await db.wallets.find_one({"user_id": user["id"]})
    if not w or w["balance"] < req.amount:
        raise HTTPException(400, "Insufficient balance")
    wd_id = str(uuid.uuid4())
    await db.withdrawals.insert_one({
        "id": wd_id, "user_id": user["id"],
        "amount": req.amount, "method": req.method, "details": req.details,
        "status": "pending", "created_at": now_utc().isoformat(),
    })
    await db.wallets.update_one(
        {"user_id": user["id"]},
        {"$inc": {"balance": -req.amount, "pending": req.amount}}
    )
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()), "user_id": user["id"],
        "type": "withdrawal", "amount": -req.amount, "status": "pending",
        "note": f"Withdrawal via {req.method.upper()}",
        "created_at": now_utc().isoformat()
    })
    return {"ok": True, "withdrawal_id": wd_id}


@api.get("/withdrawals")
async def list_withdrawals(user=Depends(get_current_user)):
    return await db.withdrawals.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)


# ---------- DOCUMENTS ----------
@api.post("/documents")
async def upload_doc(req: DocUpload, user=Depends(get_current_user)):
    existing = await db.documents.find_one({"user_id": user["id"], "doc_type": req.doc_type})
    payload = {
        "id": existing["id"] if existing else str(uuid.uuid4()),
        "user_id": user["id"],
        "doc_type": req.doc_type,
        "file_base64": req.file_base64,
        "status": "pending",
        "uploaded_at": now_utc().isoformat(),
    }
    if existing:
        await db.documents.update_one({"id": existing["id"]}, {"$set": payload})
    else:
        await db.documents.insert_one(payload)
    return {"ok": True}


@api.get("/documents")
async def my_docs(user=Depends(get_current_user)):
    docs = await db.documents.find({"user_id": user["id"]}, {"_id": 0, "file_base64": 0}).to_list(50)
    return docs


# ---------- NOTIFICATIONS ----------
@api.get("/notifications")
async def list_notifs(user=Depends(get_current_user)):
    return await db.notifications.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)


@api.post("/notifications/{notif_id}/read")
async def mark_read(notif_id: str, user=Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notif_id, "user_id": user["id"]}, {"$set": {"read": True}}
    )
    return {"ok": True}


# ---------- LEADERBOARD ----------
@api.get("/leaderboard")
async def leaderboard():
    wallets = await db.wallets.find({}, {"_id": 0}).sort("total_earned", -1).to_list(50)
    result = []
    for i, w in enumerate(wallets):
        u = await db.users.find_one({"id": w["user_id"]}, {"_id": 0, "password": 0})
        if u and u.get("role") != "admin":
            result.append({
                "rank": len(result) + 1,
                "user_id": u["id"],
                "name": u["full_name"],
                "city": u["city"],
                "avatar": u.get("avatar_base64"),
                "total_earned": w["total_earned"],
                "tasks_completed": u.get("tasks_completed", 0),
                "level": u.get("level", "Bronze"),
            })
    return result[:30]


# ---------- REFERRAL ----------
@api.get("/referral")
async def my_referral(user=Depends(get_current_user)):
    refs = await db.referrals.find({"referrer_id": user["id"]}, {"_id": 0}).to_list(200)
    total = sum(r["reward"] for r in refs)
    return {
        "code": user.get("referral_code"),
        "count": len(refs),
        "total_earned": total,
        "referrals": refs,
    }


# ---------- TICKETS ----------
@api.post("/tickets")
async def create_ticket(req: TicketReq, user=Depends(get_current_user)):
    t = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_name": user["full_name"],
        "category": req.category,
        "description": req.description,
        "screenshot_base64": req.screenshot_base64,
        "status": "open",
        "created_at": now_utc().isoformat(),
    }
    await db.tickets.insert_one(t)
    t.pop("_id", None)
    t.pop("screenshot_base64", None)
    return t


@api.get("/tickets")
async def my_tickets(user=Depends(get_current_user)):
    return await db.tickets.find({"user_id": user["id"]}, {"_id": 0, "screenshot_base64": 0}).sort("created_at", -1).to_list(100)


# ---------- ADMIN ----------
@api.get("/admin/stats")
async def admin_stats(admin=Depends(get_current_admin)):
    users_count = await db.users.count_documents({"role": "user"})
    tasks_count = await db.tasks.count_documents({})
    pending_wd = await db.withdrawals.count_documents({"status": "pending"})
    pending_docs = await db.documents.count_documents({"status": "pending"})
    pending_tasks = await db.task_submissions.count_documents({"status": "under_review"})
    tickets_count = await db.tickets.count_documents({"status": "open"})
    return {
        "users": users_count, "tasks": tasks_count,
        "pending_withdrawals": pending_wd, "pending_documents": pending_docs,
        "pending_tasks": pending_tasks, "open_tickets": tickets_count,
    }


@api.get("/admin/withdrawals")
async def admin_withdrawals(admin=Depends(get_current_admin)):
    items = await db.withdrawals.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    for it in items:
        u = await db.users.find_one({"id": it["user_id"]}, {"_id": 0, "password": 0})
        it["user_name"] = u["full_name"] if u else "?"
        it["user_email"] = u["email"] if u else "?"
    return items


@api.post("/admin/withdrawals/{wd_id}")
async def act_withdrawal(wd_id: str, req: AdminAction, admin=Depends(get_current_admin)):
    wd = await db.withdrawals.find_one({"id": wd_id})
    if not wd:
        raise HTTPException(404, "Not found")
    if wd["status"] != "pending":
        raise HTTPException(400, "Already processed")
    new_status = "approved" if req.action == "approve" else "rejected"
    await db.withdrawals.update_one({"id": wd_id}, {"$set": {"status": new_status}})
    if req.action == "approve":
        await db.wallets.update_one(
            {"user_id": wd["user_id"]},
            {"$inc": {"pending": -wd["amount"], "total_withdrawn": wd["amount"]}}
        )
        await db.transactions.update_one(
            {"user_id": wd["user_id"], "type": "withdrawal", "status": "pending", "amount": -wd["amount"]},
            {"$set": {"status": "completed"}}
        )
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "user_id": wd["user_id"],
            "title": "Withdrawal Approved", "body": f"₹{wd['amount']:.0f} sent via {wd['method'].upper()}",
            "type": "withdrawal", "read": False, "created_at": now_utc().isoformat()
        })
    else:
        # refund
        await db.wallets.update_one(
            {"user_id": wd["user_id"]},
            {"$inc": {"pending": -wd["amount"], "balance": wd["amount"]}}
        )
        await db.transactions.update_one(
            {"user_id": wd["user_id"], "type": "withdrawal", "status": "pending", "amount": -wd["amount"]},
            {"$set": {"status": "rejected"}}
        )
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "user_id": wd["user_id"],
            "title": "Withdrawal Rejected", "body": req.note or "Contact support.",
            "type": "withdrawal", "read": False, "created_at": now_utc().isoformat()
        })
    return {"ok": True}


@api.get("/admin/documents")
async def admin_documents(admin=Depends(get_current_admin)):
    items = await db.documents.find({}, {"_id": 0}).sort("uploaded_at", -1).to_list(200)
    for it in items:
        u = await db.users.find_one({"id": it["user_id"]}, {"_id": 0, "password": 0})
        it["user_name"] = u["full_name"] if u else "?"
    return items


@api.post("/admin/documents/{doc_id}")
async def act_document(doc_id: str, req: AdminAction, admin=Depends(get_current_admin)):
    d = await db.documents.find_one({"id": doc_id})
    if not d:
        raise HTTPException(404, "Not found")
    new_status = "verified" if req.action == "approve" else "rejected"
    await db.documents.update_one({"id": doc_id}, {"$set": {"status": new_status}})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": d["user_id"],
        "title": f"Document {new_status.capitalize()}",
        "body": f"{d['doc_type'].upper()} {'verified' if req.action == 'approve' else 'rejected'}",
        "type": "document", "read": False, "created_at": now_utc().isoformat()
    })
    return {"ok": True}


@api.get("/admin/task-submissions")
async def admin_task_subs(admin=Depends(get_current_admin)):
    items = await db.task_submissions.find({"status": "under_review"}, {"_id": 0}).sort("created_at", -1).to_list(200)
    for it in items:
        u = await db.users.find_one({"id": it["user_id"]}, {"_id": 0, "password": 0})
        t = await db.tasks.find_one({"id": it["task_id"]}, {"_id": 0})
        it["user_name"] = u["full_name"] if u else "?"
        it["task_title"] = t["title"] if t else "?"
        it["budget"] = t["budget"] if t else 0
    return items


@api.post("/admin/task-submissions/{sub_id}")
async def act_task_sub(sub_id: str, req: AdminAction, admin=Depends(get_current_admin)):
    s = await db.task_submissions.find_one({"id": sub_id})
    if not s:
        raise HTTPException(404, "Not found")
    task = await db.tasks.find_one({"id": s["task_id"]})
    if req.action == "approve":
        await db.task_submissions.update_one({"id": sub_id}, {"$set": {"status": "approved"}})
        await db.task_acceptances.update_one(
            {"task_id": s["task_id"], "user_id": s["user_id"]},
            {"$set": {"status": "completed"}}
        )
        if task:
            await db.wallets.update_one(
                {"user_id": s["user_id"]},
                {"$inc": {"balance": task["budget"], "total_earned": task["budget"], "pending": -task["budget"]}}
            )
            await db.users.update_one({"id": s["user_id"]}, {"$inc": {"tasks_completed": 1, "streak": 1}})
            await db.transactions.insert_one({
                "id": str(uuid.uuid4()), "user_id": s["user_id"],
                "type": "earning", "amount": task["budget"], "status": "completed",
                "note": f"Earned from: {task['title']}",
                "created_at": now_utc().isoformat()
            })
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()), "user_id": s["user_id"],
                "title": "Task Approved!", "body": f"₹{task['budget']:.0f} added to your wallet",
                "type": "task", "read": False, "created_at": now_utc().isoformat()
            })
    else:
        await db.task_submissions.update_one({"id": sub_id}, {"$set": {"status": "rejected"}})
        await db.task_acceptances.update_one(
            {"task_id": s["task_id"], "user_id": s["user_id"]},
            {"$set": {"status": "rejected"}}
        )
        if task:
            await db.wallets.update_one(
                {"user_id": s["user_id"]},
                {"$inc": {"pending": -task["budget"]}}
            )
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "user_id": s["user_id"],
            "title": "Task Rejected", "body": req.note or "Resubmit with better proof",
            "type": "task", "read": False, "created_at": now_utc().isoformat()
        })
    return {"ok": True}


@api.get("/admin/users")
async def admin_users(admin=Depends(get_current_admin)):
    return await db.users.find({"role": "user"}, {"_id": 0, "password": 0}).to_list(500)


@api.get("/admin/tickets")
async def admin_tickets(admin=Depends(get_current_admin)):
    return await db.tickets.find({}, {"_id": 0, "screenshot_base64": 0}).sort("created_at", -1).to_list(200)


@api.post("/admin/tickets/{tid}/close")
async def close_ticket(tid: str, admin=Depends(get_current_admin)):
    await db.tickets.update_one({"id": tid}, {"$set": {"status": "closed"}})
    return {"ok": True}


# ---------- SEED ----------
@app.on_event("startup")
async def seed_data():
    # Seed admin
    admin = await db.users.find_one({"email": "admin@earnhub.com"})
    if not admin:
        admin_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": admin_id,
            "full_name": "EarnHub Admin",
            "mobile": "9999999999",
            "email": "admin@earnhub.com",
            "password": hash_pw("Admin@123"),
            "city": "Mumbai", "state": "Maharashtra",
            "role": "admin", "referral_code": "ADMIN0000",
            "referred_by": None, "avatar_base64": None,
            "rating": 5.0, "tasks_completed": 0, "streak": 0, "level": "Diamond",
            "created_at": now_utc().isoformat(),
        })
        await db.wallets.insert_one({
            "user_id": admin_id, "balance": 0.0, "total_earned": 0.0,
            "total_withdrawn": 0.0, "pending": 0.0
        })

    # Seed demo user with balance
    demo = await db.users.find_one({"email": "demo@earnhub.com"})
    if not demo:
        demo_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": demo_id,
            "full_name": "Demo User",
            "mobile": "9876543210",
            "email": "demo@earnhub.com",
            "password": hash_pw("Demo@123"),
            "city": "Bengaluru", "state": "Karnataka",
            "role": "user", "referral_code": "DEMO1234",
            "referred_by": None, "avatar_base64": None,
            "rating": 4.8, "tasks_completed": 12, "streak": 5, "level": "Silver",
            "created_at": now_utc().isoformat(),
        })
        await db.wallets.insert_one({
            "user_id": demo_id, "balance": 850.0, "total_earned": 2450.0,
            "total_withdrawn": 1600.0, "pending": 0.0
        })
        # demo transactions
        for t in [
            {"type": "earning", "amount": 250, "note": "Earned from: Product Photoshoot"},
            {"type": "earning", "amount": 150, "note": "Earned from: Data Entry"},
            {"type": "withdrawal", "amount": -500, "note": "Withdrawal via UPI"},
            {"type": "referral", "amount": 50, "note": "Referral bonus"},
        ]:
            await db.transactions.insert_one({
                "id": str(uuid.uuid4()), "user_id": demo_id,
                "type": t["type"], "amount": t["amount"],
                "status": "completed", "note": t["note"],
                "created_at": now_utc().isoformat()
            })

    # Seed tasks
    if await db.tasks.count_documents({}) < 3:
        seed_tasks = [
            {"title": "Product Photoshoot at Bandra", "description": "Click 20 photos of clothing items at our store. DSLR or good phone camera required.", "category": "Photography", "budget": 800, "location": "Bandra, Mumbai", "distance_km": 1.2},
            {"title": "Data Entry - 500 rows", "description": "Enter product data from spreadsheets into our Shopify store. Approx 500 rows.", "category": "Data Entry", "budget": 450, "location": "Remote", "distance_km": 0},
            {"title": "Distribute Flyers in Koramangala", "description": "Hand out 200 promotional flyers near tech parks. 2-3 hours work.", "category": "Marketing", "budget": 350, "location": "Koramangala, Bangalore", "distance_km": 3.4},
            {"title": "Verify 10 Shop Addresses", "description": "Visit 10 shops, verify they exist and click a photo of the storefront.", "category": "Verification", "budget": 500, "location": "Andheri, Mumbai", "distance_km": 2.8},
            {"title": "Quick Survey Walk-in", "description": "Conduct a 5-min consumer survey at our mall booth. 20 responses needed.", "category": "Survey", "budget": 300, "location": "Phoenix Mall, Pune", "distance_km": 5.1},
            {"title": "Pickup Documents from Notary", "description": "Pickup a sealed envelope from our notary and drop at our office.", "category": "Delivery", "budget": 250, "location": "Connaught Place, Delhi", "distance_km": 1.8},
            {"title": "List 50 items on Meesho", "description": "Upload product images and descriptions to our Meesho seller account.", "category": "Product Listing", "budget": 600, "location": "Remote", "distance_km": 0},
            {"title": "Mystery Shopper - Cafe", "description": "Visit our partner cafe, order food, complete a feedback form.", "category": "Survey", "budget": 200, "location": "Indiranagar, Bangalore", "distance_km": 4.5},
        ]
        for t in seed_tasks:
            await db.tasks.insert_one({
                "id": str(uuid.uuid4()),
                "posted_by": "system",
                "posted_by_name": "EarnHub",
                "title": t["title"], "description": t["description"],
                "category": t["category"], "requirements": "",
                "budget": t["budget"], "deadline": (now_utc() + timedelta(days=7)).isoformat(),
                "workers_needed": 5, "location": t["location"],
                "image_base64": None, "status": "open",
                "created_at": now_utc().isoformat(),
                "distance_km": t["distance_km"],
            })


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
