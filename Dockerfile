FROM continuumio/anaconda3

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

#Install libraries
RUN pip install pandas --upgrade
EXPOSE 5000
RUN pip install psycopg2-binary
RUN conda install -c conda-forge hdbscan
RUN pip install tabulate
RUN pip install pantheon
RUN pip install nest_asyncio
RUN pip install pygsheets

#Copy working directory
COPY . /

WORKDIR /app

#Run scripts
CMD [ "python", "./main.py" ]