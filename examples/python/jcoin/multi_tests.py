import time
import threading


def loop_1():
    while True:
        print('loop 1')
        time.sleep(1)
    

def loop_2():
    while True:
        print('loop 2')
        time.sleep(1)
        
        
thread1 = threading.Thread(target=loop_1)
thread1.start()

thread2 = threading.Thread(target=loop_2)
thread2.start()

