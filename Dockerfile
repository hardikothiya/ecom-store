FROM python:3.10

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Required to install mysqlclient with Pip
RUN apt-get update \
  && apt-get install python3-dev default-libmysqlclient-dev gcc -y

# Install pipenv
RUN pip install --upgrade pip 

# Install application dependencies
ADD ./requirements.txt /app/

RUN pip install --upgrade virtualenv
RUN virtualenv -p python enve
RUN . /app/enve/bin/activate
RUN pip install -r requirements.txt
RUN #pip install -U setuptools/
# We use the --system flag so packages are installed into the system python
# and not into a virtualenv. Docker containers don't need virtual environments. 

# Copy the application files into the image
COPY . /app/

# Expose port 8000 on the container
EXPOSE 8000