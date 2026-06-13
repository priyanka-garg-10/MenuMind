# Importing all models here registers them with Base.metadata.
# This file must be imported before init_db() is called in main.py,
# otherwise create_all() won't know which tables to create.
from app.models.user import OTPSession, User  # noqa: F401
from app.models.preference import UserPreference  # noqa: F401
