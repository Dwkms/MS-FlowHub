from dataclasses import dataclass


@dataclass(frozen=True)
class ActorContext:
    """Authenticated employee identity used by application services.

    The current query-parameter bridge remains temporary until Supabase Auth is connected.
    """

    employee_id: str
    role: str
    auth_user_id: str | None = None
