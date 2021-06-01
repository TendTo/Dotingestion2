from json import loads
from pyspark.sql import SparkSession
from pyspark.sql.dataframe import StructType, StructField, DataFrame
from pyspark.sql.types import ArrayType, IntegerType, LongType, BooleanType
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.sql.functions import udf, col

sc = SparkSession.builder.appName("dotingestion").getOrCreate()

schema = StructType([StructField("dire_lineup", ArrayType(IntegerType(), False), False),
                    StructField("radiant_lineup", ArrayType(IntegerType(), False), False),
                    StructField("radiant_win", BooleanType(), False),
                    StructField("match_id", LongType(), False)])

path = "data.json"
df = sc.read.json(path, schema=schema).na.drop("all").distinct()

with open("heroes.json", 'r', encoding="utf-8") as f:
    heroes_dict = {hero['id']: i for i, hero in enumerate(loads(f.read()))}

def convert_heroes_to_lineup(df: DataFrame) -> DataFrame:

    def onehot(heroes: ArrayType):
        lineup = tuple(heroes_dict[hero] for hero in heroes)
        return Vectors.dense([1 if hero_slot in lineup else 0 for hero_slot in range(len(heroes_dict))])

    heros_to_lineup_udf = udf(onehot, VectorUDT())
    return df.withColumn("dire_lineup_vec", heros_to_lineup_udf(df.dire_lineup))\
             .withColumn("radiant_lineup_vec", heros_to_lineup_udf(df.radiant_lineup))

df = convert_heroes_to_lineup(df)

def convert_types(df: DataFrame) -> DataFrame:
    return df.withColumn("radiant_win_int", df.radiant_win.cast(IntegerType()))

df = convert_types(df)

from pyspark.ml.pipeline import Pipeline
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import VectorAssembler, VectorSizeHint

size_hint_dire = VectorSizeHint(inputCol="dire_lineup_vec", size=len(heroes_dict), handleInvalid="skip")
size_hint_radiant = VectorSizeHint(inputCol="radiant_lineup_vec", size=len(heroes_dict), handleInvalid="skip")
vec_assembler = VectorAssembler(inputCols=['dire_lineup_vec', 'radiant_lineup_vec'], outputCol="features")
regression = LogisticRegression(featuresCol="features", labelCol="radiant_win_int")
pipeline = Pipeline(stages=[size_hint_dire, size_hint_radiant, vec_assembler, regression])

traint_df, test_df = df.randomSplit([0.8, 0.2])
model = pipeline.fit(df)

result_df = model.transform(test_df)

test_accuracy = result_df.filter(col("radiant_win").eqNullSafe(col("prediction"))).count()/result_df.count()

model.save("model")
