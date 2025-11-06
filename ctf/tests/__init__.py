import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from ctf.prepare_flags import prepare_flags

# Prepare flags with in-memory database for tests
_ = prepare_flags(lancedb_persistent=False)
