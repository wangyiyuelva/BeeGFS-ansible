import pika, sys, os
import wilelife_dlc
import shutil
import socket
from datetime import datetime

def receive():
    # Establishing connection with RabbitMQ server
    credentials = pika.PlainCredentials('admin', 'abc123')
    connection = pika.BlockingConnection(pika.ConnectionParameters('10.0.0.108', '5673', '/', credentials=credentials, heartbeat=1200))
    channel = connection.channel()

    # Declaring the queue to consume messages from
    channel.queue_declare(queue='input_file_que')

    # Getting the IP address of the current machine for logging
    hostname=socket.gethostname()
    IPAddr=socket.gethostbyname(hostname)
    print("Your Computer IP Address is:"+IPAddr)
    fname = f"/beegfs/pipeline/flask/static/{IPAddr.replace('.', '-')}.log"

    # Define the callback function and register it with basic_consume()
    def callback(ch, method, properties, body):
        print(f" [x] Received filename {body}")
        input = body.decode()

        # process filename for shutil
        source_file = input
        filename = source_file.split("/")[-1]
        dst_file = "/beegfs/data/input_done/" + filename

        # Add logging info
        with open(fname, 'a+') as f:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            f.write(repr(current_datetime) + ": " + repr(filename) + ' start running wildlife model...\n')
        print(f" [x] Processing {input}")

        # Running PytorchWildlife model
        wild_result = wilelife_dlc.run_wildlife(input)

        # Add logging info
        with open(fname, 'a+') as f:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            f.write(repr(current_datetime) + ": " + repr(filename) + ' completed wildlife model, starting deeplabcut...\n')

        # Running Deeplabcut model
        wilelife_dlc.run_deeplabcut(wild_result)

        # Moving completed input file to another directory
        try:
            shutil.move(source_file, dst_file)
            print(f"Successfully moved {source_file} to {dst_file}")
        except Exception as e:
            print(f"Error moving file: {e}")
 
        # Logging completion of processing
        with open(fname, 'a') as f:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            f.write(repr(current_datetime) + ": " + repr(filename) + ' is Done.\n')

        # Acknowledge the message
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print(f" [x] Complete {input}")

    # Setting service prefetch count, and start consuming
    channel.basic_qos(prefetch_count=1)    
    channel.basic_consume(queue='input_file_que',
                          auto_ack=False,
                          on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':

    try:
        receive()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

