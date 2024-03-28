from pathlib import Path

import modal

image = modal.Image.debian_slim().pip_install(
    "streamlit~=1.32.2", "pandas~=2.2.1", "plotly~=5.20.0"
)

stub = modal.Stub(name="coffeshop-dashboard", image=image)


streamlit_script_local_path = Path(__file__).parent / "Home.py"
streamlit_script_remote_path = Path("/root/Home.py")
streamlit_pages_local_path = Path(__file__).parent / "pages"
streamlit_pages_remote_path = Path("/root/pages")

streamlit_script_mount = modal.Mount.from_local_file(
    streamlit_script_local_path,
    remote_path=streamlit_script_remote_path,
)

streamlit_pages_mount = modal.Mount.from_local_dir(
    streamlit_pages_local_path,
    remote_path=streamlit_pages_remote_path,
)

backend_mount = modal.Mount.from_local_python_packages("backend")


@stub.function(
    allow_concurrent_inputs=100,
    mounts=[streamlit_script_mount, streamlit_pages_mount, backend_mount],
    concurrency_limit=1,
    timeout=60 * 60,
)
@modal.web_server(8000)
def run():
    import shlex
    import subprocess

    target = shlex.quote(str(streamlit_script_remote_path))
    cmd = f"streamlit run {target} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false"
    subprocess.Popen(cmd, shell=True)
