from diagrams import Diagram, Cluster
from diagrams.programming.language import Python
from diagrams.onprem.client import Users
from diagrams.gcp.compute import Run
from diagrams.aws.storage import S3
from diagrams.custom import Custom

# Set diagram formatting
graph_attr = {
    "fontsize": "24",
    "bgcolor": "white",
    "splines": "ortho",
}

# Base path for images (Updated to your absolute path)
base_path = r"input_icons"

# Create the diagram
with Diagram("llm_based_pdf", show=False, graph_attr=graph_attr, direction="TB"):
   
    # User/Client
    user = Users("End User")

     # Select a PDF
    with Cluster("PDF Cloud Storage"):
        pdf_upload = Custom("Select existing PDF \n Upload new PDF", f"{base_path}/s3_image.png")
   
    # Frontend Cluster
    with Cluster("Frontend (User Interface)"):
        streamlit = Custom("Streamlit UI", f"{base_path}/streamlit.png")
   
    # Cloud Infrastructure Cluster
    with Cluster("GCP VM Instance"):
        # GCP Cloud Run hosting the FastAPI backend
        cloud_run = Custom("GCP VM Instance", f"{base_path}/gcp.png")

        with Cluster("Backend"):
            fastapi = Custom("FastAPI", f"{base_path}/FastAPI.png")

        with Cluster("Processing Services"):
            redis = Custom("Redis", f"{base_path}/redis.png")

            with Cluster("Redis Workers"):

                with Cluster("Worker 1 (Summary)"):
                    stream11 = Custom("Summary \n Request Stream", f"{base_path}/worker.png")
                    stream12 = Custom("Summary \n Response Stream", f"{base_path}/worker.png")
                
                with Cluster("Worker 2 (Q & A)"):
                    stream21 = Custom("Q & A \n Request Stream", f"{base_path}/worker.png")
                    stream22 = Custom("Q & A \n Response Stream", f"{base_path}/worker.png")

            with Cluster("LLM Integration"):
                llm = Custom("LLM Integration", f"{base_path}/llm.png")
                zephyr = Custom("Zephyr \n (HuggingFace)", f"{base_path}/huggingface.png")
                gemini = Custom("Gemini \n (Google)", f"{base_path}/gemini.png")

    user >> streamlit
    streamlit >> user
    streamlit >> pdf_upload 
    streamlit >> cloud_run >> fastapi >> redis

    pdf_upload >> streamlit
    cloud_run >> streamlit

    fastapi >> cloud_run
    redis >> fastapi

    with Cluster("Processing Flows"):     
        redis >> stream11
        stream11 >> llm

        redis >> stream21
        stream21 >> llm 

        llm >> stream12
        stream12 >> redis

        llm >> stream22
        stream22 >> redis

        llm >> [zephyr, gemini]
        [zephyr, gemini] >> llm

