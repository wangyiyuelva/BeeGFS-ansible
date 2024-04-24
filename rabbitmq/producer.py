import pika
import os


def get_file_size(file_path):
  """Gets the size of a file in bytes."""
  try:
    return os.path.getsize(file_path)
  except (FileNotFoundError, PermissionError) as e:
    # Handle potential errors like file not found or permission issues
    print(f"Error accessing file '{file_path}': {e}")
    return 0

def list_mp4_files(directory):
  """
  This function lists all mp4 files within a directory.
  """

  mp4_files = []
  target_size_bytes = 2 * 1024 * 1024

  for filename in os.listdir(directory):
    if filename.endswith(".mp4"):
      filepath = os.path.join(directory, filename)
      file_size = get_file_size(filepath)
      if file_size <= target_size_bytes:
        mp4_files.append(filepath)
  
  return mp4_files


# list all mp4 files
directory = "/beegfs/data/input/" # input directory
mp4_data = list_mp4_files(directory)

if mp4_data:
  print("start publishing...")
else:
  print("No mp4 files found in the specified directory.")

# RabbitMQ producer setup
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', '5673', heartbeat=1200))
channel = connection.channel()

# Declare the queue to send messages to
channel.queue_declare(queue='input_file_que')
    
# Loop the list and publish each file as a message to the queue
for target_mp4 in mp4_data:
  channel.basic_publish(exchange='',
                        routing_key='input_file_que',
                        body=target_mp4)
  print(f" [x] Sent {target_mp4}")

channel.close()

