#### Local
import eventlet, sys, time
from eventlet import event
from eventlet.green import zmq
from eventlet.hubs import use_hub, get_hub

use_hub('zeromq')
ctx = get_hub().get_context()

rx_event = event.Event()

def receive(socket, message_count, message_size, evt):
    start = time.clock()
    for i in range (1, message_count):
        msg = socket.recv()
        assert len(msg) == message_size
    end = time.clock()
    evt.send((start, end))

def send(socket, message_count, message_size):
    msg = ' ' * message_size
    for i in range(0, message_count):
        socket.send(msg)


def main ():
    use_poll = '-p' in sys.argv
    use_copy = '-c' in sys.argv
    if use_copy:
        sys.argv.remove('-c')
    if use_poll:
        sys.argv.remove('-p')

    if len (sys.argv) != 4:
        print 'usage: local_thr [-c use-copy] [-p use-poll] <bind-to> <message-size> <message-count>'
        sys.exit(1)

    try:
        address = sys.argv[1]
        message_size = int(sys.argv[2])
        message_count = int(sys.argv[3])
    except (ValueError, OverflowError), e:
        print 'message-size and message-count must be integers'
        sys.exit(1)

    sub = ctx.socket(zmq.SUB)

    #  Add your socket options here.
    #  For example ZMQ_RATE, ZMQ_RECOVERY_IVL and ZMQ_MCAST_LOOP for PGM.
    sub.setsockopt(zmq.SUBSCRIBE , "")
    sub.bind(address)

    pub = ctx.socket(zmq.PUB)
    pub.connect(address)

    eventlet.sleep(0.1)
    eventlet.spawn(receive, sub, message_count, message_size, rx_event)
    eventlet.spawn(send, pub, message_count, message_size)

    start, end = rx_event.wait()
    elapsed = (end - start) * 1000000 # use with time.clock
    if elapsed == 0:
    	elapsed = 1
    throughput = (1000000.0 * float(message_count)) / float(elapsed)
    megabits = float(throughput * message_size * 8) / 1000000

    print "message size: %.0f [B]" % (message_size, )
    print "message count: %.0f" % (message_count, )
    print "mean throughput: %.0f [msg/s]" % (throughput, )
    print "mean throughput: %.3f [Mb/s]" % (megabits, )

    # Let the context finish messaging before ending.
    # You may need to increase this time for longer or many messages.
    eventlet.sleep(0.5)

if __name__ == "__main__":
    main ()
