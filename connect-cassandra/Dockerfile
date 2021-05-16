FROM confluentinc/cp-kafka-connect-base:6.1.1

ARG CONNECTOR_VERSION="1.4.0"

ADD setup/kafka-connect-cassandra-sink-${CONNECTOR_VERSION}.tar.gz /tmp
COPY conf/connect-standalone.properties /etc/kafka
COPY conf/cassandra-sink.properties /etc/kafka

USER root

RUN mkdir -p /usr/share/confluent-hub-components &&\
    mv /tmp/kafka-connect-cassandra-sink-${CONNECTOR_VERSION}/*.jar  /usr/share/confluent-hub-components

CMD ["/bin/connect-standalone", "/etc/kafka/connect-standalone.properties", "/etc/kafka/cassandra-sink.properties"]