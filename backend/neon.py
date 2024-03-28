from pathlib import Path

import modal

neon_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "psycopg2-binary~=2.9.9",
        "requests~=2.31.0",
    )
    .apt_install("wget", "lsb-release")
    .run_commands(
        [
            "sh -c 'echo \"deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main\" > /etc/apt/sources.list.d/postgres.list'",
            "wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -",
        ]
    )
    .apt_install("postgresql-client-14")
    .run_commands(
        [
            "wget --quiet -O - https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash",
        ]
    )
    .env({"NVM_DIR": "/root/.nvm"})
    .run_commands(
        [
            ". $NVM_DIR/nvm.sh && nvm install 20",
            ". $NVM_DIR/nvm.sh && nvm use 20 && node -v && npm -v",
            ". $NVM_DIR/nvm.sh && npm i -g neonctl && neonctl completion >> /root/.bashrc",
        ]
    )
)


stub = modal.Stub(
    "coffeeshop-neon-client",
    secrets=[modal.Secret.from_name("my-neon-secret")],
    image=neon_image,
)

with neon_image.imports():
    import os

    import psycopg2
    import requests


@stub.cls()
class ApiClient:
    @modal.enter()
    def setup(self):
        self.project_id = os.environ["NEON_PROJECT_ID"]
        self.api_key = os.environ["NEON_API_KEY"]

    @property
    def base_url(self):
        return f"https://console.neon.tech/api/v2/projects/{self.project_id}/branches"

    @property
    def headers(self):
        return {"accept": "application/json", "authorization": f"Bearer {self.api_key}"}

    @modal.method()
    def get_branches(self):
        response = requests.get(self.base_url, headers=self.headers)
        branches = [
            (branch["id"], branch["name"]) for branch in response.json()["branches"]
        ]
        return branches

    @modal.method()
    def get_host(self, branch_id):
        """Find the host name associated with a given branch."""
        url = f"{self.base_url}/{branch_id}/endpoints"
        response = requests.get(url, headers=self.headers)
        host = response.json()["endpoints"][0]["host"]
        return host

    @modal.method()
    def create_branch_and_get_host(self, branch_name):
        payload = {
            "branch": {"name": branch_name},
            "endpoints": [{"type": "read_write"}],
        }
        response = requests.post(self.base_url, json=payload, headers=self.headers)
        if response.status_code == 201:
            branch_info = response.json()
            host = branch_info["endpoints"][0]["host"]
            return host
        else:
            raise Exception(f"Failed to create branch {branch_name}")


@stub.cls()
class DbClient:
    def __init__(self, host):
        self.host = host

    @modal.enter()
    def setup(self):
        self.project_id = os.environ["NEON_PROJECT_ID"]
        self.api_key = os.environ["NEON_API_KEY"]
        self.db_user = os.environ["PGUSER"]
        self.db_password = os.environ["PGPASSWORD"]

    @modal.enter()
    def connect(self):
        """Connect to the Neon pgsql database.

        The `modal.enter` decorator ensures we only do this once per instance."""

        conn = psycopg2.connect(
            user=self.db_user,
            password=self.db_password,
            host=self.host,
            database="neondb",
            sslmode="require",
        )
        self.conn = conn

    @modal.method()
    def test_connection(self):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10"
            )
            cur.arraysize = 10
            result = cur.fetchmany()
            return result

    @modal.method()
    def execute(self, query, **kwargs):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, **kwargs)
                self.conn.commit()

                if cur.description:
                    for row in cur:
                        yield row
        except Exception as e:
            self.conn.rollback()
            raise e

    @property
    def connection_string(self):
        return f"postgresql://{self.db_user}:{self.db_password}@{self.host}/neondb?sslmode=require"

    @modal.method()
    def from_seed(self, seed_query):
        import subprocess

        subprocess.run(
            [
                "psql",
                self.connection_string,
                "-c",
                seed_query,
            ]
        )

    @modal.exit()
    def close(self):
        self.conn.close()


@stub.local_entrypoint()
def main(query_file: str = None):
    print("connecting to Neon db")
    api_client = ApiClient()
    branches = api_client.get_branches.remote()
    assert branches, "failed to fetch branches from the api"
    branch_id, branch_name = branches[0]
    print(f"connecting to Neon db for branch {branch_name}")
    host = api_client.get_host.remote(branch_id)
    print(f"found host: {host}")
    client = DbClient(host)
    print(f"connected. listing all tables in branch {branch_name}:")
    print("", *[row[0] for row in client.test_connection.remote()], sep="\t")
    if query_file is not None:
        print(f"applying query from file {query_file}")
        client.from_seed.remote(host, Path(query_file).read_text())
