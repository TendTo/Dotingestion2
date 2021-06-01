FROM openjdk:8-jre

ENV SPARK_HOME=/opt/spark
ENV SPARK_VERSION=3.1.1
ENV PATH $PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

RUN apt-get update &&\
    apt-get -y install python3 python3-pip &&\
    pip3 install pyspark kafka-utils numpy

ADD setup/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz /opt
RUN mv /opt/spark-${SPARK_VERSION}-bin-hadoop2.7 ${SPARK_HOME}

WORKDIR ${SPARK_HOME}

COPY ./data .
COPY ./python .
COPY ./model ./model
COPY ./cv_model ./cv_model
COPY ./conf/log4j.properties ./conf

# Run commands
ENTRYPOINT ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1,org.elasticsearch:elasticsearch-spark-30_2.12:7.12.1", "--master", "local[*]", "app.py"]