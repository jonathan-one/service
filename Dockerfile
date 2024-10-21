# python (environnement)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# folders
RUN mkdir /code/
WORKDIR /code

# install mysql dependencies
RUN apt-get update
# RUN apt-get install gcc default-libmysqlclient-dev -y

# add projet
COPY . /code/

RUN pip install -r requirements.txt


EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]