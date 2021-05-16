FROM confluentinc/cp-kafka-connect-base:6.1.1

ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"

RUN confluent-hub install --no-prompt confluentinc/kafka-connect-elasticsearch:5.4.0

COPY conf/* /etc/kafka
COPY ./elastic-init.sh /etc

ENTRYPOINT ["/etc/elastic-init.sh"]