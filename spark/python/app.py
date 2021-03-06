import os
import logging
from json import loads
from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
from pyspark.sql.functions import from_json, udf
from pyspark.sql.dataframe import StructType, StructField, DataFrame
from pyspark.sql.types import ArrayType, FloatType, IntegerType, LongType, BooleanType, StringType
from pyspark.ml import PipelineModel
from pyspark.ml.linalg import Vectors, VectorUDT

# Command to run this application:
# spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1,org.elasticsearch:elasticsearch-spark-30_2.12:7.12.1 --master local[*] app.py
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.ERROR)

elastic_host = "elasticsearch"
elastic_index = "matches"
kafkaServer = "kafkaserver:9092"
elastic_topic = "dota_lineup"
in_topic = "dota_request"
out_topic = "dota_response"

# Schema of the input data that will go to elasticsearch
schema_elastic = StructType([
    StructField("dire_lineup", ArrayType(IntegerType(), False), False),
    StructField("radiant_lineup", ArrayType(IntegerType(), False), False),
    StructField("radiant_win", BooleanType(), False),
    StructField("match_seq_num", LongType(), False)
])

# Schema of the input data that will go to the api
schema_api = StructType([
    StructField("radiant_lineup", ArrayType(IntegerType(), False), False),
    StructField("dire_lineup", ArrayType(IntegerType(), False), False),
])

# Spark configuration, mainly needed for the elasticsearch plugin
sparkConf = SparkConf().set("spark.app.name", "dotingestion2") \
                        .set("spark.scheduler.mode", "FAIR") \
                        .set("es.nodes", "elasticsearch") \
                        .set("es.port", "9200") \
                        .set("es.mapping.id", "match_seq_num") \
                        .set("es.write.operation", "upsert")

# Load the hero_id conversions
with open("heroes.json", 'r', encoding="utf-8") as f:
    heroes_dict = {hero['id']: i for i, hero in enumerate(loads(f.read()))}

# Create a spark context with the provided conficurations
sc = SparkContext.getOrCreate(conf=sparkConf)
spark = SparkSession(sc)

# Load the Machine Learning model
model_name = os.getenv("MODEL", 'model')
model = PipelineModel.load(model_name)


# Convert "dire_lineup" and "radiant_lineup" from array to Vector, and apply the "onehot" function
def convert_heroes_to_lineup(df: DataFrame) -> DataFrame:

    def onehot(heroes: ArrayType):
        lineup = tuple(heroes_dict[hero] for hero in heroes)
        return Vectors.dense([1 if hero_slot in lineup else 0 for hero_slot in range(len(heroes_dict))])

    heros_to_lineup_udf = udf(onehot, VectorUDT())
    return df.withColumn("dire_lineup_vec", heros_to_lineup_udf(df.dire_lineup))\
             .withColumn("radiant_lineup_vec", heros_to_lineup_udf(df.radiant_lineup))


# Use the "value" json format to retrieve the data in the provided schema, then convert "radiant_win" from bool to int
def convert_types_elastic_for_ml(df: DataFrame) -> DataFrame:
    df = df.selectExpr("CAST(value AS STRING)") \
           .select(from_json("value", schema=schema_elastic).alias("data")) \
           .select("data.*")
    return df.withColumn("radiant_win_int", df.radiant_win.cast(IntegerType()))


# Use the "value" json format to retrieve the data in the provided schema
def convert_types_api_for_ml(df: DataFrame) -> DataFrame:
    return df.selectExpr("CAST(value AS STRING)") \
           .select(from_json("value", schema=schema_api).alias("data")) \
           .select("data.*")


# Convert "prediction" from int to bool and "probability" from VectorUDT to array
def convert_types_for_es(df: DataFrame) -> DataFrame:
    to_array = udf(lambda v: v.toArray().tolist(), ArrayType(FloatType()))

    return df.withColumn("radiant_win_prediction", df.prediction.cast(BooleanType())) \
             .withColumn("probability_arr", to_array(df.probability))


# Convert "prediction" from int to bool and "probability" from VectorUDT to array. Put all in the value column
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
def process_data_elastic(df: DataFrame, ml_model: PipelineModel = model) -> DataFrame:
    df = convert_types_elastic_for_ml(df)
    df = convert_heroes_to_lineup(df)
    df = ml_model.transform(df)
    df = convert_types_for_es(df)

    return df.select("probability_arr", "radiant_win_prediction", "match_seq_num")


# Combine all the convert functions and finally apply the ml model
def process_data_api(df: DataFrame, ml_model: PipelineModel = model) -> DataFrame:
    df = convert_types_api_for_ml(df)
    df = convert_heroes_to_lineup(df)
    df = ml_model.transform(df)
    df = convert_types_for_kafka(df)

    return df


####################################
#
#   Kafka -> Spark -> Elasticsearch
#
####################################

# Read the stream from kafka
df_elastic = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", elastic_topic) \
    .option("startingOffsets","earliest") \
    .load()

# Process the data and enrich it with the ml prediction
df_elastic = process_data_elastic(df_elastic)

# Write the stream to elasticsearch
query_elastic = df_elastic.writeStream \
          .option("checkpointLocation", "./checkpoints") \
          .format("es") \
          .start(elastic_index + "/_doc")

####################################
#
#   Kafka -> Spark -> Kafka -> API
#
####################################

# Read the stream from kafka
df_api = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", in_topic) \
    .option("startingOffsets","earliest") \
    .load()

# Process the data and enrich it with the ml prediction
df_api = process_data_api(df_api)

# Write the stream to kafka
query_api = df_api.writeStream \
          .format("kafka") \
          .option("kafka.bootstrap.servers", kafkaServer) \
          .option("topic", out_topic) \
          .option("checkpointLocation", "./checkpoints-api") \
          .start()

# Keep running untill terminated
query_elastic.awaitTermination()
query_api.awaitTermination()
