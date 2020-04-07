FROM continuumio/anaconda3

#Install grequests and upgrade pandas
RUN pip install grequests
EXPOSE 5000
RUN pip install pandas==1.0.3
RUN conda install -c conda-forge hdbscan
RUN conda install tabulate

#Copy working directory
COPY . /

WORKDIR /app

#Run Main
CMD [ "python", "./main.py" ]