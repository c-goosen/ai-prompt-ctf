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

# These call a real model, so they are deselected by default (see pyproject).
# Run them with: uv run pytest ctf/tests/eval/ -m llm_eval -s
pytestmark = pytest.mark.llm_eval

EVAL_DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "agents" / "eval"


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file."""
    dotenv.load_dotenv()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "evalset",
    sorted(EVAL_DATA_DIR.glob("*.evalset.json")),
    ids=lambda path: path.name.removesuffix(".evalset.json"),
)
async def test_sub_agents(evalset):
    """Run an evaluation set in ctf/agents/eval/ against the sub_agents app.

    Evaluates agent behavior including tool usage, response quality, and
    security protections. Each file is passed explicitly because, given a
    directory, AgentEvaluator only looks for *.test.json files.
    """
    await AgentEvaluator.evaluate(
        "ctf.agents.sub_agents.agent",
        str(evalset),
        num_runs=5,
    )
