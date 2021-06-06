const kafka = require('../bin/kafka')

const OUT_TOPIC = "dota_request";
const IN_TOPIC = "dota_response";

const producer = kafka.producer();
const consumer = kafka.consumer({
    groupId: "node-api"
});

/**
 * Sends a message to Spark throught Kafka with the desired prediction
 * @param {Prediction} prediction Prediction requested by the user
 */
async function produce(prediction) {
    await producer.connect()
    await producer.send({
        topic: OUT_TOPIC,
        messages: [
            { value: JSON.stringify({ radiant_lineup: prediction.radiantLineup, dire_lineup: prediction.direLineup }) }
        ],
    })
    await producer.disconnect()
}

/**
 * Keeps listening from new messages from kafka.
 * Once they arrive, it creates the appropriate Prediction and stores it in the caches.
 * @returns {Promise<void>}
 */
async function consume() {
    await consumer.connect();
    await consumer.subscribe({
        topic: IN_TOPIC,
        fromBeginning: true
    })
    return consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            const value = message.value.toString();
            const newPredictionJson = JSON.parse(value);
            const newPrediction = Prediction.createFromJson(newPredictionJson);
        }
    })
}

const predictions = new Map();

class Prediction {
    id;
    r0;
    r1;
    r2;
    r3;
    r4;
    d0;
    d1;
    d2;
    d3;
    d4;
    match_seq_num;
    radiant_win_prediction;
    probability;

    /**
     * Prediction
     * @param {object} obj object with (r|d)[0-4] properties
     */
    constructor(obj) {
        for (const kv of Object.entries(obj)) {
            if (kv[0].match(/(r|d)\d/)) {
                kv[1] = parseInt(kv[1]);
            }
            this[kv[0]] = kv[1];
        }
        this.id = Prediction.getId(obj);
    }

    /**
      * Creates a new prediction based on the user request and, if not present yet, asks kafka to provide the prediction
      * @param {object} response object with (r|d)[0-4] properties
      * @returns {Prediction} newly created prediction
      */
    static create(response) {
        const newPrediction = new Prediction(response);
        if (newPrediction.isValid)
            produce(newPrediction).catch(err => console.error(err));
        return newPrediction;
    }

    /**
     * Creates a new prediction based on the kafka message and adds it to the cache
     * @param {object} response object with *radiant_lineup* and *dire_lineup* properties
     * @returns {Prediction} newly created prediction
     */
    static createFromJson(response) {
        const newPrediction = new Prediction(response);
        newPrediction.radiantLineup = response.radiant_lineup;
        newPrediction.direLineup = response.dire_lineup;
        predictions.set(newPrediction.id, newPrediction);
        return newPrediction;
    }

    /**
     * Checks if the prediction with the specified id is present and returns it
     * @param {number} id 
     * @returns {Prediction} a prediction stored in the cache, if present
     */
    static findOne(id) {
        return predictions.has(id) ? predictions.get(id) : null;
    }

    /**
     * Extrapolate the id from the (r|d)[0-4] properties of the object
     * @param {object} obj object with (r|d)[0-4] properties
     * @returns {string} string id used to identify the prediction
     */
    static getId(obj) {
        let id = "";
        for (const kv of Object.entries(obj)) {
            if (kv[0].match(/(r|d)\d/))
                id += kv[1] + ",";
        }
        return id.substr(0, id.length - 1);
    }

    /** List of the radiant lineup */
    get radiantLineup() {
        return [this.r0, this.r1, this.r2, this.r3, this.r4];
    }

    /** Sets all the r[0-4] properties and updates the id */
    set radiantLineup(lineup) {
        for (let i = 0; i < 5; i++)
            this["r" + i] = lineup[i];
        this.id = Prediction.getId(this);
    }

    /** List of the dire lineup */
    get direLineup() {
        return [this.d0, this.d1, this.d2, this.d3, this.d4];
    }

    /** Sets all the d[0-4] properties and updates the id */
    set direLineup(lineup) {
        for (let i = 0; i < 5; i++)
            this["d" + i] = lineup[i];
        this.id = Prediction.getId(this);
    }

    /** Whether the prediction is valid */
    get isValid() {
        const heroes = this.direLineup.concat(this.radiantLineup);
        return heroes.filter(e => e !== null && e != undefined);
    }
}

consume().catch(err => { console.error(err); setTimeout(consume, 10000); });

module.exports = Prediction;