import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.analysis import AnalysisJob, JobStatus, Email
from app.models.finding import Finding
from app.schemas.analyzer import AnalysisContext
from app.services.parser import parse_email_service
from app.services.analyzers.auth_analyzer import AuthenticationAnalyzer
from app.services.analyzers.url_analyzer import UrlAnalyzer
from app.services.analyzers.attachment_analyzer import AttachmentAnalyzer
from app.services.analyzers.content_analyzer import ContentAnalyzer
from app.services.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

@celery_app.task(name="run_analysis_pipeline")
def run_analysis_pipeline(job_id: str):
    """
    Background worker orchestrating the entire static analysis pipeline.
    Connects parsing, distinct analyzers, evidence generation, and risk engine.
    Handles partial analyzer failures safely.
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"AnalysisJob {job_id} not found in database.")
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        email_record = db.query(Email).filter(Email.job_id == job_id).first()
        if not email_record:
            job.status = JobStatus.FAILED
            db.commit()
            logger.error(f"Email record missing for job {job_id}.")
            return
            
        context = AnalysisContext(job_id=job.id, workspace_path=job.workspace_path, email_record=email_record)
        context.db = db

        # 1. Parsing and Extraction
        parse_email_service(db, email_record.id)
        
        # 2. Run Modular Analyzers
        analyzers = [
            AuthenticationAnalyzer(),
            ContentAnalyzer(),
            UrlAnalyzer(),
            AttachmentAnalyzer()
        ]
        
        for analyzer in analyzers:
            try:
                # Pass context to analyzer
                result = analyzer.analyze(context)
                
                # Extract and persist findings
                if result.status in ("success", "error"):
                    for finding_schema in result.findings:
                        # Convert evidence dict to string (simulating JSON for sqlite MVP)
                        import json
                        evidence_str = json.dumps(finding_schema.evidence) if finding_schema.evidence else None
                        
                        db_finding = Finding(
                            job_id=job.id,
                            analyzer_name=result.analyzer_name,
                            source=finding_schema.source,
                            category=finding_schema.category,
                            finding_type=finding_schema.type,
                            severity=finding_schema.severity,
                            confidence=finding_schema.confidence,
                            title=finding_schema.title,
                            description=finding_schema.description,
                            evidence=evidence_str,
                            artifact_ref=finding_schema.artifact_ref
                        )
                        db.add(db_finding)
                
                # Commit after each analyzer for partial resiliency
                db.commit()
                
            except Exception as e:
                logger.error(f"Analyzer {analyzer.NAME} encountered a critical failure for job {job_id}: {e}")
                db.rollback() 
                # Continues to next analyzer gracefully to preserve partial results!
                
        # 3. Aggregate Risk via Engine
        findings = db.query(Finding).filter(Finding.job_id == job_id).all()
        risk_engine = RiskEngine()
        risk_engine.analyze(db, job.id, findings)
        
        # 4. Pipeline Complete
        job.status = JobStatus.COMPLETED
        db.commit()

    except Exception as e:
        logger.error(f"Unrecoverable pipeline failure for job {job_id}: {e}")
        db.rollback()
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            db.commit()
    finally:
        db.close()
