import proccom
import dsp


class SensorFeedback:

    def __init__(self, host, port):
        self.subscriber = proccom.Subscriber({'imu': self.imu_callback, 'steps': self.step_callback}, 'sensor_feedback',
                                             host=host, port=port)
        self.publisher = proccom.Publisher('reg_in', 'sensor_feedback_pub', self.format_output)
        self.acc_filter = dsp.core.MultiChannelFilter(3, [1])
        self.gyro_filter = dsp.core.MultiChannelFilter(3, [1])
        self.mag_filter = dsp.core.MultiChannelFilter(3, [1])

    def format_output(self, a, b, c):
        return {'a': a, 'b': b, 'c': c}

    def imu_callback(self, msg):
        pass

    def step_callback(self, msg):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
