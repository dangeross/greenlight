# Pytest fixtures
import tempfile
from .scheduler import Scheduler
from ephemeral_port_reserve import reserve
import pytest
from . import certs
from .identity import Identity
import os
from pathlib import Path

@pytest.fixture()
def directory():
    """Root directory in which we'll generate all dependent files.
    """

    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture()
def cert_directory(directory):
    yield directory / "certs"

@pytest.fixture()
def root_id(cert_directory):
    os.environ.update({
        'GL_CERT_PATH': str(cert_directory),
        'GL_CA_CRT': str(cert_directory / 'ca.pem'),
    })

    identity = certs.genca("/")

    yield identity


@pytest.fixture()
def scheduler_id(root_id):
    certs.genca("/services")
    id = certs.gencert("/services/scheduler")
    yield id


@pytest.fixture()
def users_id():
    yield certs.genca("/users")


@pytest.fixture()
def nobody_id(users_id):
    identity = certs.gencert("/users/nobody")
    os.environ.update({
        'GL_NOBODY_CRT': str(identity.cert_chain_path),
        'GL_NOBODY_KEY': str(identity.private_key_path),
    })

    yield identity


@pytest.fixture()
def scheduler(scheduler_id):
    grpc_port = reserve()
    s = Scheduler(grpc_port=grpc_port, identity=scheduler_id)
    os.environ.update({
        "GL_SCHEDULER_GRPC_URI": s.grpc_addr,
    })
    s.start()
    yield s

    del os.environ['GL_SCHEDULER_GRPC_URI']
    s.stop()


