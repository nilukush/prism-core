-- Emergency User Activation SQL
-- Run this in Neon Dashboard SQL Editor

-- 1. Check user status
SELECT id, email, status, email_verified, is_active, created_at 
FROM users 
WHERE email = 'nilukush@gmail.com';

-- 2. Activate the user
UPDATE users 
SET status = 'active',
    email_verified = true,
    email_verified_at = NOW(),
    is_active = true
WHERE email = 'nilukush@gmail.com';

-- 3. Verify activation
SELECT id, email, status, email_verified, is_active 
FROM users 
WHERE email = 'nilukush@gmail.com';

-- For all pending users (use with caution):
-- UPDATE users 
-- SET status = 'active',
--     email_verified = true,
--     email_verified_at = NOW(),
--     is_active = true
-- WHERE status = 'pending';