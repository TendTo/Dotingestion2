const { Kafka } = require('kafkajs')

const KAFKA_BOOTSTRAP_SERVER = "kafkaserver:9092"

const kafka = new Kafka({
    clientId: 'npm-api',
    brokers: [KAFKA_BOOTSTRAP_SERVER],
})

module.exports = kafka