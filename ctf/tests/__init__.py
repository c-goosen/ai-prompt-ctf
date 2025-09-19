import os
import sys
import chromadb
from chromadb import Settings

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from ctf.prepare_flags import prepare_flags

chroma_client = chromadb.Client(settings=Settings(anonymized_telemetry=False))
chroma_client.create_collection("ctf_levels")
_ = prepare_flags(chroma_client_persistent=False)
