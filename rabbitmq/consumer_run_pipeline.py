import pika, sys, os
import wilelife_dlc
import shutil

def receive():
    credentials = pika.PlainCredentials('admin', 'abc123')
    connection = pika.BlockingConnection(pika.ConnectionParameters('10.0.0.108', '5673', '/', credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue='input_file_que')

    # Define the callback function and register it with basic_consume()
    def callback(ch, method, properties, body):
        print(f" [x] Received filename {body}")
        

        input = body.decode()
        print(f" [x] Processing {input}")
        
        wild_result = wilelife_dlc.run_wildlife(input)
        wilelife_dlc.run_deeplabcut(wild_result)

        # filename = wild_result.split("/")[-1]
        # source_file = wild_result[:-4] + "DLC_snapshot-700000_labeled.mp4"
        # dst_file = "/beegfs/data/output/" + filename
        # try:
        #     shutil.move(source_file, dst_file)
        #     print(f"Successfully moved {source_file} to {dst_file}")
        # except Exception as e:
        #     print(f"Error moving file: {e}")
        
        print(f" [x] Complete {input}")
        ch.basic_ack(delivery_tag = method.delivery_tag)
        
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
