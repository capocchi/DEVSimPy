FROM python:3.8-slim-buster

LABEL maintainer="Capocchi Laurent"
LABEL website="http://capocchi-l.universita.corsica/"

WORKDIR /app

RUN apt-get update
RUN apt-get install -y build-essential libgtk-3-dev
RUN pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-10 wxPython

#COPY requirements-nogui.txt requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "devsimpy.py"]

#CMD ["python3", "devsimpy-nogui.py", "examples/model0.yaml", "10"]
