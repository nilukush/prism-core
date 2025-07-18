"""
Production patch for auto-activation.
This file shows how to modify auth.py to support auto-activation in production.
"""

# Add this to authenticate_user method in auth.py after line 324:

# PRODUCTION AUTO-ACTIVATION PATCH
# Check if auto-activation is enabled (works in any environment)
if os.getenv("AUTO_ACTIVATE_USERS", "false").lower() == "true":
    if user.status == UserStatus.pending:
        logger.info(
            "auto_activating_user",
            username=username,
            environment=settings.ENVIRONMENT,
            reason="AUTO_ACTIVATE_USERS is enabled"
        )
        user.status = UserStatus.active
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        # Note: Don't set is_active as it's computed
        await db.commit()
        await db.refresh(user)

# Also modify the status check to be more flexible:
# Replace the existing status check (around line 340) with:

# Check user status with auto-activation support
if user.status != UserStatus.active:
    # If auto-activation failed or is disabled
    logger.warning(
        "user_not_active",
        username=username,
        status=user.status.value,
        auto_activate_enabled=os.getenv("AUTO_ACTIVATE_USERS", "false")
    )
    return None