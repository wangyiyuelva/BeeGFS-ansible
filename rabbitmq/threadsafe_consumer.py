import functools
import logging
import pika
import threading
import shutil
import wilelife_dlc
import socket
from datetime import datetime

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

def ack_message(channel, delivery_tag):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        channel.basic_ack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass

def do_work(connection, channel, delivery_tag, body):
    thread_id = threading.get_ident()
    fmt1 = 'Thread id: {} Delivery tag: {} Message body: {}'
    LOGGER.info(fmt1.format(thread_id, delivery_tag, body))
    
    input = body.decode()

    hostname=socket.gethostname()
    IPAddr=socket.gethostbyname(hostname)
    fname = f'/beegfs/pipeline/LogFiles/Log-{IPAddr}.log'
    with open(fname, 'a+') as f:
        # get current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        f.write(repr(current_datetime) + ": " + repr(input) + ' start running...\n')

    wild_result = wilelife_dlc.run_wildlife(input)
    wilelife_dlc.run_deeplabcut(wild_result)
    source_file = input
    filename = source_file.split("/")[-1]
    dst_file = "/beegfs/data/input_done/" + filename
    try:
        shutil.move(source_file, dst_file)
        print(f"Successfully moved {source_file} to {dst_file}")
    except Exception as e:
        print(f"Error moving file: {e}")

    with open(fname, 'a') as f:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        f.write(repr(current_datetime) + ": " + repr(input) + ' is Done.\n')

    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
    t.start()
    threads.append(t)

credentials = pika.PlainCredentials('admin', 'abc123')
# Note: sending a short heartbeat to prove that heartbeats are still
# sent even though the worker simulates long-running work
parameters =  pika.ConnectionParameters('10.0.0.108', '5673', '/', credentials=credentials, heartbeat=60)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()
# channel.exchange_declare(exchange="test_exchange", exchange_type="direct", passive=False, durable=True, auto_delete=False)
channel.queue_declare(queue="input_file_que", auto_delete=False)
# channel.queue_bind(queue="input_file_que", exchange="test_exchange", routing_key="standard_key")
# Note: prefetch is set to 1 here as an example only and to keep the number of threads created
# to a reasonable amount. In production you will want to test with different prefetch values
# to find which one provides the best performance and usability for your solution
channel.basic_qos(prefetch_count=1)

threads = []
callback = functools.partial(on_message, args=(connection, threads))
channel.basic_consume(queue='input_file_que', on_message_callback = callback)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()

# Wait for all to complete
for thread in threads:
    thread.join()

connection.close()
