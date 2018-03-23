# oBMP

All of the python executables use the Kafka libraries.

probe.py connects to one of the known openBMP Kafka servers to discover what topics are served there.  
probe.py is not aware of openBMP message structures

parse.py connects to a Kafka/openBMP source and listens to a topic and attempts to parse the messages published
parse.py IS aware of openBMP message structures, including the the CAIDA forked version of openBMP and its veriosn 1.7 message formats  
parse.py attempts to prase and display message content  
parse.py does not process content at BMP protocol level  

forward.py extends parse.py  
  Forward.py is a connector between openBMP Kafka messaging context and basic BMP.  
  It unpacks the BMP payload from the Kafka envelope and forwards the BMP message on a TCP connection  
  A vanilla BMP collector can use this directly, however it suffers the limitation that unlie a true BMP session ther eis no initial FIB dump, or exchange of other BMP messages on session establishment.

