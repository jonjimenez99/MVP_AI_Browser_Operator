from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from app.schemas.requests import (
    TestCaseRequest,
    TestCaseFileRequest,
    TestSuiteRequest
)
from app.schemas.responses import (
    TestCaseResponse,
    TestExecutionStatus,
    TestSuiteResponse
)
from app.services.operator_runner import (
    OperatorRunnerInterface,
    create_operator_runner,
    StepExecutionResult
)
from app.api.dependencies import (
    get_current_tenant,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Update the dependency
def get_operator_runner() -> OperatorRunnerInterface:
    """Dependency for getting test runner instance."""
    return create_operator_runner()

@router.post(
    "/execute",
    response_model=TestCaseResponse,
    summary="Execute a single test case",
    description="Execute a test case with given steps, URL, and optional headless mode"
)
async def execute_operator_case(
    request: TestCaseRequest,
    background_tasks: BackgroundTasks,
    test_runner: OperatorRunnerInterface = Depends(get_operator_runner),
    tenant_id: str = Depends(get_current_tenant),
) -> TestCaseResponse:
    """
    Execute a single test case with the provided steps.

    Args:
        request: Test case details including URL, steps, and optional headless mode
        background_tasks: FastAPI background tasks handler
        test_runner: Injected test runner service
        tenant_id: Current tenant identifier
    """
    try:
        # Execute test case with headless parameter (None if not provided)
        result = await test_runner.run_operator_case(
            url=request.url,
            natural_language_steps=request.test_steps,
            headless=request.headless if request.headless is not None else False  # Default to False
        )

        # Schedule cleanup in background
        background_tasks.add_task(
            cleanup_operator_artifacts,
            result.steps_results
        )

        logger.debug(result.steps_results)

        return TestCaseResponse(
            request_id=result.metadata.get("request_id"),
            tenant_id=tenant_id,
            execution_time=datetime.now(),
            success=result.success,
            steps_results=[
                {
                    "step": step_result.natural_language_step,
                    "success": step_result.execution_result.success,
                    "screenshot_url": step_result.execution_result.screenshot_path,
                    "duration": step_result.duration,
                    "error": step_result.execution_result.error_message
                }
                for step_result in result.steps_results
            ],
            total_duration=result.total_duration,
            error_message=result.error_message
        )

    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Test execution failed: {str(e)}"
        )

@router.post(
    "/execute/file",
    response_model=TestCaseResponse,
    summary="Execute test case from file",
    description="Execute a test case from an uploaded file"
)
async def execute_operator_case_from_file(
    request: TestCaseFileRequest,
    test_runner: OperatorRunnerInterface = Depends(get_operator_runner),
    tenant_id: str = Depends(get_current_tenant)
) -> TestCaseResponse:
    """Execute test case from uploaded file."""
    try:
        # Read and parse file content
        test_steps = await parse_operator_file(request.file)

        # Use default headless=False for file-based execution
        return await execute_operator_case(
            TestCaseRequest(
                url=request.url,
                test_steps=test_steps,
                headless=False  # Default for file-based execution
            ),
            background_tasks=BackgroundTasks(),
            test_runner=test_runner,
            tenant_id=tenant_id
        )

    except Exception as e:
        logger.error(f"File execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"File execution failed: {str(e)}"
        )

@router.get(
    "/status/{execution_id}",
    response_model=TestExecutionStatus,
    summary="Get test execution status",
    description="Get the status of a test execution by ID"
)
async def get_execution_status(
    execution_id: str,
    tenant_id: str = Depends(get_current_tenant)
) -> TestExecutionStatus:
    """Get status of a test execution."""
    try:
        # Retrieve status from storage/cache
        status = await get_operator_status(execution_id, tenant_id)

        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )

        return status

    except Exception as e:
        logger.error(f"Status retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Status retrieval failed: {str(e)}"
        )

@router.post(
    "/suite/execute",
    response_model=TestSuiteResponse,
    summary="Execute test suite",
    description="Execute multiple test cases as a suite"
)
async def execute_operator_suite(
    request: TestSuiteRequest,
    background_tasks: BackgroundTasks,
    test_runner: OperatorRunnerInterface = Depends(get_operator_runner),
    tenant_id: str = Depends(get_current_tenant)
) -> TestSuiteResponse:
    """Execute multiple test cases as a suite."""
    try:
        start_time = datetime.now()
        suite_results = []

        for test_case in request.test_cases:
            result = await execute_operator_case(
                test_case,
                background_tasks,
                test_runner,
                tenant_id
            )
            suite_results.append(result)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        return TestSuiteResponse(
            suite_id=request.suite_id,
            tenant_id=tenant_id,
            execution_time=end_time,
            results=suite_results,
            total_duration=total_duration,
            total_cases=len(suite_results),
            successful_cases=sum(1 for r in suite_results if r.success),
            failed_cases=sum(1 for r in suite_results if not r.success)
        )

    except Exception as e:
        logger.error(f"Suite execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Suite execution failed: {str(e)}"
        )

# Helper functions
async def cleanup_operator_artifacts(step_results: List[StepExecutionResult]) -> None:
    """Clean up screenshots and other artifacts after test execution."""
    try:
        for result in step_results:
            if result.execution_result.screenshot_path:
                # Delete screenshot file
                pass
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)

async def parse_operator_file(file: bytes) -> str:
    """Parse test steps from uploaded file."""
    try:
        # Implement file parsing logic
        return file.decode()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format: {str(e)}"
        )

async def get_operator_status(
    execution_id: str,
    tenant_id: str
) -> Optional[TestExecutionStatus]:
    """Retrieve test execution status from storage."""
    # Implement status retrieval logic
    pass