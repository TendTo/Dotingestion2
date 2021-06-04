FROM cassandra

COPY cassandra-init.sh /cassandra-init.sh
RUN chmod +x /cassandra-init.sh

ENTRYPOINT ["/cassandra-init.sh"]
CMD ["cassandra", "-f"]