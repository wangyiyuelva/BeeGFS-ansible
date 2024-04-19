import pika

input = "../data_input/test.mp4"
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', '5673'))
channel = connection.channel()

channel.queue_declare(queue='input_file_que')
		
		
channel.basic_publish(exchange='',
                          routing_key='input_file_que',
                          body=input)
print(" [x] Sent {input}")
channel.close()
