apt install default-jdk wget python-pip
wget http://www.mirrorservice.org/sites/ftp.apache.org/kafka/1.0.0/kafka_2.11-1.0.0.tgz
tar zxf kafka_2.11-1.0.0.tgz 
cd kafka_2.11-1.0.0
bin/zookeeper-server-start.sh config/zookeeper.properties
pip install kafka-python python-snappy
