from json import loads
from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
from pyspark.sql.functions import from_json, udf
from pyspark.sql.dataframe import StructType, StructField, DataFrame
from pyspark.sql.types import ArrayType, FloatType, IntegerType, LongType, BooleanType
from pyspark.ml import PipelineModel
from pyspark.ml.linalg import Vectors, VectorUDT

# Command to run this application:
# spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1,org.elasticsearch:elasticsearch-spark-30_2.12:7.12.1 --master local[*] app.py

elastic_host = "elasticsearch"
elastic_index = "matches"
kafkaServer = "kafkaServer:9092"
topic = "dota_lineup"

# Schema of the input data
schema = StructType([
    StructField("dire_lineup", ArrayType(IntegerType(), False), False),
    StructField("radiant_lineup", ArrayType(IntegerType(), False), False),
    StructField("radiant_win", BooleanType(), False),
    StructField("match_seq_num", LongType(), False)
])

# Spark configuration, mainly needed for the elasticsearch plugin
sparkConf = SparkConf().set("spark.app.name", "dotingestion") \
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
model = PipelineModel.load("model")


# Convert "dire_lineup" and "radiant_lineup" from array to Vector, and apply the "onehot" function
def convert_heroes_to_lineup(df: DataFrame) -> DataFrame:

    def onehot(heroes: ArrayType):
        lineup = tuple(heroes_dict[hero] for hero in heroes)
        return Vectors.dense([1 if hero_slot in lineup else 0 for hero_slot in range(len(heroes_dict))])

    heros_to_lineup_udf = udf(onehot, VectorUDT())
    return df.withColumn("dire_lineup_vec", heros_to_lineup_udf(df.dire_lineup))\
             .withColumn("radiant_lineup_vec", heros_to_lineup_udf(df.radiant_lineup))


# Use the "value" json format to retrieve the data in the provided schema, then convert "radiant_win" from bool to int
def convert_types_for_ml(df: DataFrame) -> DataFrame:
    df = df.selectExpr("CAST(value AS STRING)") \
           .select(from_json("value", schema=schema).alias("data")) \
           .select("data.*")
    return df.withColumn("radiant_win_int", df.radiant_win.cast(IntegerType()))


# Convert "prediction" from int to bool and "probability" from VectorUDT to array
def convert_types_for_es(df: DataFrame) -> DataFrame:
    to_array = udf(lambda v: v.toArray().tolist(), ArrayType(FloatType()))

    return df.withColumn("radiant_win_prediction", df.prediction.cast(BooleanType())) \
             .withColumn("probability_arr", to_array(df.probability))


# Combine all the convert functions and finally apply the ml model
def process_data(df: DataFrame, ml_model: PipelineModel = model) -> DataFrame:
    df = convert_types_for_ml(df)
    df = convert_heroes_to_lineup(df)
    df = ml_model.transform(df)
    df = convert_types_for_es(df)

    return df.select("probability_arr", "radiant_win_prediction", "match_seq_num")


# Read the stream from kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .option("startingOffsets","earliest") \
    .load()

# Process the data and enrich it with the ml prediction
df = process_data(df)

# Write the stream to elasticsearch
query = df.writeStream \
          .option("checkpointLocation", "./checkpoints") \
          .format("es") \
          .start(elastic_index)

# Keep running untill terminated
query.awaitTermination()
