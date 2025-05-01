FROM python:3.12.9-slim
WORKDIR /root
COPY requirements.txt /root/
RUN pip install -r requirements.txt
COPY src/main/flask_service.py /root/
ENTRYPOINT ["python"]
CMD ["flask_service.py"]