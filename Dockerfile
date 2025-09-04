FROM python:3.10-slim-bookworm
RUN apt update
RUN apt-get install -qq -y jq sqlite3
RUN mkdir /app
WORKDIR /app
ADD requirements.lock /app
RUN pip install --upgrade -r requirements.lock
ADD entrypoint.sh /app
RUN chmod +x entrypoint.sh
# Next line will break docker layer caching, if any file is changed in the pwd.
ADD . /app
CMD ["./entrypoint.sh"]
