# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Evaluation tests for CTF agents."""

import pathlib

import dotenv
import pytest
from google.adk.evaluation import AgentEvaluator

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file."""
    dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_sub_agents():
    """Test the sub_agents app with evaluation data.
    
    This test runs all evaluation sets found in ctf/agents/eval/
    against the sub_agents app. It will evaluate agent behavior
    including tool usage, response quality, and security protections.
    """
    # Path to eval data directory containing .evalset.json files
    eval_data_dir = pathlib.Path(__file__).parent.parent.parent / "agents" / "eval"
    await AgentEvaluator.evaluate(
        "sub_agents",
        str(eval_data_dir),
        num_runs=5,
    )

