-- Setup script to create a test organization and link it to the test user

-- First, check if the default organization exists
DO $$
DECLARE
    org_id INTEGER;
    user_id INTEGER;
BEGIN
    -- Get the test user ID
    SELECT id INTO user_id FROM users WHERE email = 'nilukush@gmail.com' LIMIT 1;
    
    IF user_id IS NULL THEN
        RAISE NOTICE 'Test user not found. Please ensure user exists first.';
        RETURN;
    END IF;

    -- Check if default organization exists
    SELECT id INTO org_id FROM organizations WHERE slug = 'personal' LIMIT 1;
    
    IF org_id IS NULL THEN
        -- Create the default organization
        INSERT INTO organizations (
            name, 
            slug, 
            email, 
            plan, 
            max_users, 
            max_projects, 
            max_storage_gb,
            owner_id,
            settings,
            created_at,
            updated_at
        ) VALUES (
            'Personal Organization',
            'personal',
            'nilukush@gmail.com',
            'free',
            5,
            10,
            50,
            user_id,
            '{}',
            NOW(),
            NOW()
        ) RETURNING id INTO org_id;
        
        RAISE NOTICE 'Created organization with ID: %', org_id;
    ELSE
        RAISE NOTICE 'Organization already exists with ID: %', org_id;
    END IF;
    
    -- Add user as member of organization if not already
    BEGIN
        INSERT INTO organization_members (user_id, organization_id, role, joined_at)
        VALUES (user_id, org_id, 'admin', NOW());
        RAISE NOTICE 'Added user as organization member';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'User is already a member of the organization';
    END;
    
    RAISE NOTICE 'User is now a member of the organization';
END $$;

-- Verify the setup
SELECT 
    o.id,
    o.name,
    o.slug,
    o.plan,
    o.owner_id,
    u.email as owner_email,
    om.role as member_role
FROM organizations o
JOIN users u ON o.owner_id = u.id
LEFT JOIN organization_members om ON o.id = om.organization_id AND om.user_id = u.id
WHERE o.slug = 'personal';