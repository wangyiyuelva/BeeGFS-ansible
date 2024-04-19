import pika
import os

def list_mp4_files(directory):
  """
  This function lists all mp4 files within a directory.
  """

  mp4_files = []

  for filename in os.listdir(directory):
    if filename.endswith(".mp4"):
      filepath = os.path.join(directory, filename)
      mp4_files.append(filepath)
  
  return mp4_files


# list all mp4 files
directory = "/beegfs/data/input/" # input directory
mp4_data = list_mp4_files(directory)

if mp4_data:
  print(mp4_data)
else:
  print("No mp4 files found in the specified directory.")

# rabbitMQ producer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', '5673'))
channel = connection.channel()

channel.queue_declare(queue='input_file_que')
    
for target_mp4 in mp4_data:
  channel.basic_publish(exchange='',
                        routing_key='input_file_que',
                        body=target_mp4)
  print(f" [x] Sent {target_mp4}")

channel.close()
