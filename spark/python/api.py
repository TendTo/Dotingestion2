import logging
from json import loads
from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
from pyspark.sql.functions import from_json, udf
from pyspark.sql.dataframe import StructType, StructField, DataFrame
from pyspark.sql.types import ArrayType, FloatType, IntegerType, StringType, BooleanType
from pyspark.ml import PipelineModel
from pyspark.ml.linalg import Vectors, VectorUDT

# Command to run this application:
# spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1 --master local[*] api.py
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.ERROR)

kafkaServer = "kafkaserver:9092"
in_topic = "dota_request"
out_topic = "dota_response"

# Schema of the input data
schema = StructType([
    StructField("radiant_lineup", ArrayType(IntegerType(), False), False),
    StructField("dire_lineup", ArrayType(IntegerType(), False), False),
])

# Spark configuration, mainly needed for the elasticsearch plugin
sparkConf = SparkConf().set("spark.app.name", "dotingestion2-api")

# Load the hero_id conversions
with open("heroes.json", 'r', encoding="utf-8") as f:
    heroes_dict = {hero['id']: i for i, hero in enumerate(loads(f.read()))}

# Create a spark context with the provided conficurations
sc = SparkContext.getOrCreate(conf=sparkConf)
spark = SparkSession(sc)

# Load the Machine Learning model
model = PipelineModel.load("model")


# Convert "dire_lineup" and "radiant_lineup" from array to Vector, and apply the "onehot" function
def convert_heroes_to_lineup(df: DataFrame) -> DataFrame:

    def onehot(heroes: ArrayType):
        lineup = tuple(heroes_dict[hero] for hero in heroes)
        return Vectors.dense([1 if hero_slot in lineup else 0 for hero_slot in range(len(heroes_dict))])

    heros_to_lineup_udf = udf(onehot, VectorUDT())
    return df.withColumn("dire_lineup_vec", heros_to_lineup_udf(df.dire_lineup))\
             .withColumn("radiant_lineup_vec", heros_to_lineup_udf(df.radiant_lineup))


# Use the "value" json format to retrieve the data in the provided schema
def convert_types_for_ml(df: DataFrame) -> DataFrame:
    return df.selectExpr("CAST(value AS STRING)") \
           .select(from_json("value", schema=schema).alias("data")) \
           .select("data.*")


# Convert "prediction" from int to bool and "probability" from VectorUDT to array
def convert_types_for_kafka(df: DataFrame) -> DataFrame:
    to_array = udf(lambda v: v.toArray().tolist(), ArrayType(FloatType()))
    to_value = udf(
        lambda radiant_lineup, dire_lineup, radiant_win_prediction, probability_arr:
        f'{{"radiant_lineup": {radiant_lineup}, "dire_lineup": {dire_lineup}, "radiant_win_prediction": {"true" if radiant_win_prediction else "false"}, "probability": {probability_arr}}}',
        StringType())

    df = df.withColumn("radiant_win_prediction", df.prediction.cast(BooleanType())) \
             .withColumn("probability_arr", to_array(df.probability))
    return df.withColumn("value", to_value(df.radiant_lineup, df.dire_lineup, df.radiant_win_prediction, df.probability_arr))


# Combine all the convert functions and finally apply the ml model
def process_data(df: DataFrame, ml_model: PipelineModel = model) -> DataFrame:
    df = convert_types_for_ml(df)
    df = convert_heroes_to_lineup(df)
    df = ml_model.transform(df)
    df = convert_types_for_kafka(df)

    return df


# Read the stream from kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", in_topic) \
    .option("startingOffsets","earliest") \
    .load()

# Process the data and enrich it with the ml prediction
df = process_data(df)

# Write the stream to kafka
query = df.writeStream \
          .format("kafka") \
          .option("kafka.bootstrap.servers", kafkaServer) \
          .option("topic", out_topic) \
          .option("checkpointLocation", "./checkpoints-api") \
          .start()

# Keep running untill terminated
query.awaitTermination()
