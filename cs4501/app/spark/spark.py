
'''
from pyspark import SparkContext

sc = SparkContext("spark://spark-master:7077", "PopularItems")

data = sc.textFile("/tmp/data/accessLog.txt", 2)     # each worker loads a piece of the data file

pairs = data.map(lambda line: line.split("\t"))   # tell each worker to split each line of it's partition
pages = pairs.map(lambda pair: (pair[1], 1))      # re-layout the data to ignore the user id
count = pages.reduceByKey(lambda x,y: int(x)+int(y))        # shuffle the data so that each key is only on one worker
                                                  # and then reduce all the values by adding them together

output = count.collect()                          # bring the data back to the master node so we can print it out
for page_id, count in output:
    print ("page_id %s count %d" % (page_id, count))
print ("Popular items done")

sc.stop()
'''

from pyspark import SparkContext
from itertools import combinations
import MySQLdb

sc = SparkContext("spark://spark-master:7077", "CoViews")

data = sc.textFile("/tmp/data/accessLog.txt", 2)     # each worker loads a piece of the data file

db = MySQLdb.connect('db', 'www', '$3cureUS', 'cs4501')
cursor = db.cursor()
print("Clearing Recommendations Table")
cursor.execute("TRUNCATE TABLE entity_recommendations;")

pairs = data.map(lambda line: line.split("\t"))  # tell each worker to split each line of it's partition
#groups = pairs.map(lambda pair: (str(pair[0]),str(pair[1]) ))
grouped = pairs.groupByKey().map(lambda x : (x[0], list(x[1])))

transform1 = grouped.flatMap(lambda x: [(x[0], k) for k in list(combinations(x[1], 2))]) 
transform2 = transform1.map(lambda x: (x[1], x[0]))


transform3 = transform2.groupByKey().map(lambda x: (x[0], set(x[1])))
transform3 = transform3.map(lambda x: (x[0], len(x[1]))) 
filtered = transform3.filter(lambda x: x[1] > 0).collect()

#output = transform1.collect()

'''
for user_id, count in output:
    print ("Products %s count %s" % (user_id, count))
print ("Popular items done")

'''
for product_id, count in filtered:
    product0 = str(product_id[0])
    product1 = str(product_id[1])
    cursor.execute(
        "INSERT INTO entity_recommendations (item_id, recommended_items) VALUES (%s, %s) ON DUPLICATE KEY UPDATE recommended_items=CONCAT(recommended_items, ',', VALUES(recommended_items));",
        (product0, product1))
    cursor.execute(
        "INSERT INTO entity_recommendations (item_id, recommended_items) VALUES (%s, %s) ON DUPLICATE KEY UPDATE recommended_items=CONCAT(recommended_items, ',', VALUES(recommended_items));",
        (product1, product0))
    db.commit()

    print ("Products %s count %d" % (product_id, count))
print ("Popular items done")

sc.stop()

db.close()