from app.core.database import Base
from app.models.analysis import AnalysisJob, Email, Attachment, URL
from app.models.audit import AuditEvent
from app.models.finding import Finding
from app.models.risk import RiskResult
# which is needed by Alembic for autogenerating migrations.
