-- IMMEDIATE SQL FIX FOR USER ACTIVATION
-- Run this in Neon Dashboard SQL Editor NOW while waiting for backend deployment

-- 1. Check current status of your user
SELECT id, email, status, email_verified, is_active, is_deleted 
FROM users 
WHERE email = 'nilukush@gmail.com';

-- 2. Activate your user immediately
UPDATE users 
SET 
    status = 'active',
    email_verified = true,
    email_verified_at = NOW(),
    is_deleted = false  -- Ensure user is not soft-deleted
WHERE email = 'nilukush@gmail.com';

-- 3. Verify the update worked
SELECT id, email, status, email_verified, is_deleted,
       CASE 
           WHEN status = 'active' AND is_deleted = false THEN 'YES - User can login!'
           ELSE 'NO - Check status and is_deleted'
       END as can_login
FROM users 
WHERE email = 'nilukush@gmail.com';

-- 4. Optional: Activate ALL pending users at once
-- UPDATE users 
-- SET 
--     status = 'active',
--     email_verified = true,
--     email_verified_at = NOW()
-- WHERE status = 'pending' AND is_deleted = false;

-- 5. View all users with their login status
SELECT 
    email,
    status,
    email_verified,
    is_deleted,
    CASE 
        WHEN status = 'active' AND is_deleted = false THEN '✅ Can Login'
        WHEN status = 'pending' THEN '⏳ Needs Activation'
        WHEN is_deleted = true THEN '❌ Deleted'
        ELSE '❌ Cannot Login'
    END as login_status,
    created_at
FROM users 
ORDER BY created_at DESC 
LIMIT 20;