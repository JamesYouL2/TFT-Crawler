FROM continuumio/anaconda3

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

#Install libraries
EXPOSE 5000
#RUN apt-get install libpq-dev python3-dev -y
RUN pip install psycopg2-binary
RUN conda install -c conda-forge hdbscan
RUN pip install tabulate
RUN pip install pantheon
RUN pip install nest_asyncio

#Copy working directory
COPY . /

WORKDIR /app

#Run scripts
CMD [ "python", "./main.py" ]