import time
import threading
import tkinter as tk


import matplotlib.pyplot as plt
import matplotlib.animation as animation
import proccom

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

lock = threading.Lock()
new_x = []
new_y = []
t0 = time.time()

xs = []
ys = []


def feedback_handler(msg):
    global new_x, new_y, lock
    data = msg['data']
    output = data['output']
    raw = data['raw']
    orientation = output['orientation']
    acc = output['acc']
    gyro = output['gyro']
    with lock:
        new_x.append(round(time.time() - t0, 5))
        new_y.append(gyro)


def get_data():
    global new_x, new_y, lock, xs, ys
    with lock:
        new_x_copy = new_x.copy()
        new_y_copy = new_y.copy()
        new_x = []
        new_y = []
    xs = xs + new_x_copy
    ys = ys + new_y_copy
    xs = xs[-200:]
    ys = ys[-200:]
    return xs.copy(), ys.copy()


def animate(i):
    global ax
    x, y = get_data()
    ax.clear()
    ax.plot(x, y)
    plt.xticks(rotation=45, ha='right')
    plt.legend(['ax', 'ay', 'az'])


def main():
    subscriber = proccom.Subscriber({'feedback': feedback_handler}, 'logger')
    subscriber.connect()
    ani = animation.FuncAnimation(fig, animate, interval=20)
    plt.show()


if __name__ == '__main__':
    main()
