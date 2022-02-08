# Dockerfile
# https://semaphoreci.com/community/tutorials/dockerizing-a-python-django-web-application

# FROM python:3.7-buster
FROM python:3.8-alpine

# install nginx
# RUN apt-get update && apt-get install nginx vim -y --no-install-recommends
# COPY nginx.default /etc/nginx/sites-available/default
# RUN ln -sf /dev/stdout /var/log/nginx/access.log \
#     && ln -sf /dev/stderr /var/log/nginx/error.log
# copy source and install dependencies
# COPY .pip_cache /opt/app/pip_cache/
#COPY . /opt/app/fabrikApi/
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /opt/app/fabrikApi
WORKDIR /opt/app
# COPY requirements.txt start-server-gunicorn.sh ./
COPY . .

# OnlY NEEDED FOR ALPINE
# TODO: we do not have to install the full mysql client, right?
RUN set -e; \
  apk add --no-cache --virtual .build-deps \
  bash \
  gcc \
  libc-dev \
  linux-headers \
  mariadb-dev \
  libffi-dev \
  python3-dev; \
  set -x; \
  adduser -D -H -u 1000 -s /bin/bash www-data -G www-data;
  # addgroup -g 982 -S www-data ; 
  # adduser -u 982 -D -S -G www-data www-data && exit 0 ; exit 1 ;

# only for DEMO (test3)
RUN pip install scipy

RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache; \
  rm -Rf /opt/app/pip_cache; \
  rm -Rf /opt/app/.pytest_cache; \
  rm -Rf /opt/app/.vscode; \
  rm -Rf /opt/app/.coveragerc; \
  chown -R www-data:www-data /opt/app

# start server
EXPOSE 8020
STOPSIGNAL SIGTERM
CMD ["/opt/app/start-server-gunicorn.sh"]