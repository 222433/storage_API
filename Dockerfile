# Dockerfile
FROM python:3.10

WORKDIR /storage_api

COPY storage_api/ .
RUN pip install debugpy
RUN pip install -r requirements.txt

# RUN chmod -R 777 /app

CMD ["python3", "run.py"]
# CMD ["curl", "http://0.0.0.0:8080/webservice/pluginfile.php/25/assignsubmission_file/submission_files/6/test.py?token=3e20c74833b770afee53ec851f063212"]
