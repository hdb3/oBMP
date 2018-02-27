#!/usr/bin/python

from kafka import KafkaConsumer

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer(bootstrap_servers=['bmp.bgpstream.caida.org:9092'],client_id='lancaster_university_UK',group_id='beta-bmp-stream')
for topic in consumer.topics():
    print(topic)
consumer = KafkaConsumer(bootstrap_servers=['r720:9092'])
for topic in consumer.topics():
    print(topic)
#consumer = KafkaConsumer('test', bootstrap_servers=['localhost:9092'])
#consumer = KafkaConsumer('my-topic', group_id='my-group', bootstrap_servers=['localhost:9092'])
exit()
for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition, message.offset, message.key, message.value))

