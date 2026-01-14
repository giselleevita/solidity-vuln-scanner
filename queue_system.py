"""
Queue System for Async Processing
Celery + Redis for background job processing
"""

from celery import Celery
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()

# Celery configuration
celery_app = None
REDIS_URL = config.redis_url

try:
    celery_app = Celery(
        "scanner",
        broker=REDIS_URL,
        backend=REDIS_URL
    )
    
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutes
        task_soft_time_limit=240,  # 4 minutes
    )
    
    logger.info("Celery queue system initialized")
except Exception as e:
    logger.warning(f"Celery not available: {e}. Queue system disabled.")


@celery_app.task(name="analyze_contract_async")
def analyze_contract_task(contract_code: str, contract_name: str, use_llm: bool = False):
    """
    Celery task for async contract analysis
    
    Args:
        contract_code: Solidity contract code
        contract_name: Contract name
        use_llm: Whether to use LLM audit
        
    Returns:
        Analysis result dictionary
    """
    from static_analyzer import StaticAnalyzer
    from llm_auditor import LLMAuditor
    from app_config import get_config
    
    config = get_config()
    
    # Run static analysis
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(contract_code, contract_name)
    result_dict = result.to_dict()
    
    # Run LLM audit if requested
    if use_llm and config.use_llm and config.llm_api_key:
        try:
            auditor = LLMAuditor(
                api_key=config.llm_api_key,
                model=config.llm_model,
                provider=config.llm_provider
            )
            llm_result = auditor.audit(contract_code, contract_name)
            result_dict["llm_audit"] = llm_result.to_dict()
        except Exception as e:
            logger.error(f"LLM audit failed in task: {e}")
    
    return result_dict


def submit_analysis_job(contract_code: str, contract_name: str, use_llm: bool = False) -> str:
    """
    Submit analysis job to queue
    
    Returns:
        Task ID
    """
    if celery_app is None:
        raise RuntimeError("Celery queue system not available")
    
    task = analyze_contract_task.delay(contract_code, contract_name, use_llm)
    logger.info(f"Analysis job submitted: {task.id}")
    return task.id


def get_job_status(task_id: str) -> dict:
    """
    Get status of a job
    
    Returns:
        Job status dictionary
    """
    if celery_app is None:
        return {"status": "unavailable", "error": "Queue system not available"}
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return {"status": "pending", "task_id": task_id}
    elif task.state == 'PROGRESS':
        return {
            "status": "processing",
            "task_id": task_id,
            "progress": task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        return {
            "status": "completed",
            "task_id": task_id,
            "result": task.result
        }
    else:
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(task.info)
        }
