# This file holds the global database connections
# It is separate so main.py and deps.py can both import it safely.

class DatabaseState:
    client = None
    incidents = None
    events = None
    actions = None
    users = None
    tenants = None
    invitations = None
    usage = None

db_state = DatabaseState()