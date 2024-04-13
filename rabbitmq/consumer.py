import pika, sys, os

def receive():
    credentials = pika.PlainCredentials('admin', 'abc123')
    connection = pika.BlockingConnection(pika.ConnectionParameters('10.0.4.102', '5673', '/', credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue='input_file_que')
    # Define the callback function and register it with basic_consume()
    def callback(ch, method, properties, body):
        print(f" [x] Received filename {body}")
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
