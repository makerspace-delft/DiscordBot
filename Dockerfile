FROM python:3.10
WORKDIR /bot
COPY . /bot
RUN pip install -r requirements.txt
CMD python main.py