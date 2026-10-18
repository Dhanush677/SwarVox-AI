import os

# Keep the foundation test suite independent of a developer's local services.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENVIRONMENT"] = "test"
