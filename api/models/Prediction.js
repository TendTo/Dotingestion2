const kafka = require('../bin/kafka')

const OUT_TOPIC = "dota_request";
const IN_TOPIC = "dota_response";

const producer = kafka.producer();
const consumer = kafka.consumer({
    groupId: "node-api"
});

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

    constructor(obj) {
        for (const kv of Object.entries(obj)) {
            if (kv[0].match(/(r|d)\d/)) {
                kv[1] = parseInt(kv[1]);
            }
            this[kv[0]] = kv[1];
        }
        this.id = Prediction.getId(obj);
    }

    static create(response) {
        const newPrediction = new Prediction(response);
        if (newPrediction.isValid)
            produce(newPrediction).catch(err => console.error(err));
        return newPrediction;
    }

    static createFromJson(response) {
        const newPrediction = new Prediction(response);
        newPrediction.radiantLineup = response.radiant_lineup;
        newPrediction.direLineup = response.dire_lineup;
        predictions.set(newPrediction.id, newPrediction);
        return newPrediction;
    }

    static findOne(id) {
        return predictions.has(id) ? predictions.get(id) : null;
    }

    static getId(obj) {
        let id = "";
        for (const kv of Object.entries(obj)) {
            if (kv[0].match(/(r|d)\d/))
                id += kv[1] + ",";
        }
        return id.substr(0, id.length - 1);
    }

    get radiantLineup() {
        return [this.r0, this.r1, this.r2, this.r3, this.r4];
    }

    set radiantLineup(lineup) {
        for (let i = 0; i < 5; i++)
            this["r" + i] = lineup[i];
        this.id = Prediction.getId(this);
    }

    get direLineup() {
        return [this.d0, this.d1, this.d2, this.d3, this.d4];
    }

    set direLineup(lineup) {
        for (let i = 0; i < 5; i++)
            this["d" + i] = lineup[i];
        this.id = Prediction.getId(this);
    }


    get isValid() {
        const heroes = this.direLineup.concat(this.radiantLineup);
        return heroes.filter(e => e !== null && e != undefined);
    }
}

consume().catch(err => { console.error(err); setTimeout(consume, 10000); });

module.exports = Prediction;