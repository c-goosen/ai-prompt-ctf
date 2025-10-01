"""
Test suite for CTF agent password query evaluations
Tests that agents properly call the rag_tool_func when asked "what is the password"
"""

from google.adk.evaluation.agent_evaluator import AgentEvaluator
import pytest
import os

# Get the current directory for relative paths
current_dir = os.path.dirname(__file__)
agents_dir = os.path.dirname(current_dir)


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_0_password_query():
    """Test Level 0 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_0_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_1_password_query():
    """Test Level 1 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_1_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_2_password_query():
    """Test Level 2 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_2_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_3_password_query():
    """Test Level 3 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_3_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_4_password_query():
    """Test Level 4 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_4_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_5_password_query():
    """Test Level 5 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_5_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_6_password_query():
    """Test Level 6 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_6_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_7_password_query():
    """Test Level 7 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_7_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_8_password_query():
    """Test Level 8 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_8_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_9_password_query():
    """Test Level 9 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_9_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_level_10_password_query():
    """Test Level 10 agent's response to password query."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "level_10_password_test.test.json"
        ),
    )


@pytest.mark.asyncio
@pytest.mark.adk_api
async def test_all_levels_password_queries():
    """Test all levels using the comprehensive eval set."""
    await AgentEvaluator.evaluate(
        agent_module=agents_dir,
        eval_dataset_file_path_or_dir=os.path.join(
            current_dir, "ctf_password_tests.evalset.json"
        ),
    )
