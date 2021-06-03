FROM jupyter/pyspark-notebook:spark-3.1.1

RUN pip3 install pyspark kafka-utils numpy

WORKDIR /app

COPY ./data .
COPY ./python .
COPY ./model ./model
COPY ./cv_model ./cv_model
COPY ./conf/log4j.properties ./conf

# Run commands
ENTRYPOINT ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1,org.elasticsearch:elasticsearch-spark-30_2.12:7.12.1", "--master", "local[*]", "app.py"]