# 🔓 Activate Your User Account

## The Issue
Your account is in "pending" status because email verification isn't set up on the free tier. The login requires "active" status.

## Quick Solutions

### Solution 1: Direct Database Update (Fastest)

If you have access to Render's PostgreSQL database:

```sql
UPDATE users 
SET status = 'active', 
    email_verified = true,
    email_verified_at = NOW()
WHERE email = 'nilukush@gmail.com';
```

### Solution 2: Create a Temporary Activation Endpoint

Add this to your backend locally and deploy:

```python
# In backend/src/api/v1/auth.py, add this endpoint:

@router.post("/activate-temp/{email}")
async def activate_user_temp(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Temporary endpoint to activate users - REMOVE IN PRODUCTION"""
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = UserStatus.active
    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    
    await db.commit()
    return {"message": f"User {email} activated successfully"}
```

Then call:
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/auth/activate-temp/nilukush@gmail.com
```

### Solution 3: Use Render Shell (If Available)

1. Go to Render Dashboard
2. Click on your backend service
3. Go to "Shell" tab
4. Run:

```python
from backend.src.core.database import get_db
from backend.src.models.user import User, UserStatus
from sqlalchemy import select
import asyncio

async def activate():
    async with get_db() as db:
        result = await db.execute(
            select(User).where(User.email == 'nilukush@gmail.com')
        )
        user = result.scalar_one()
        user.status = UserStatus.active
        user.email_verified = True
        await db.commit()
        print("User activated!")

asyncio.run(activate())
```

### Solution 4: Skip Email Verification (Development)

Update your backend environment variables in Render:
```
SKIP_EMAIL_VERIFICATION=true
```

Then modify the login check to skip verification in development.

## Immediate Workaround

Since modifying the deployed backend takes time, try:

1. **Register a new account** and **login immediately** (sometimes there's a grace period)
2. **Check browser console** for the exact error:
   ```javascript
   // Run this in console at https://prism-frontend-kappa.vercel.app
   fetch('/api/auth/session').then(r => r.json()).then(console.log)
   ```

## The Real Issue

The backend is correctly checking email verification status. Since email sending failed (no SMTP configured), your account is stuck in "pending" status.

For production, you should:
1. Set up SMTP (SendGrid, AWS SES, etc.)
2. Or temporarily disable email verification
3. Or add an admin endpoint to manually activate users