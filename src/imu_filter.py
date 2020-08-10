import proccom
import dsp
import regutil


class SensorFeedback:

    def __init__(self, host, port, interval):
        self.subscriber = proccom.Subscriber({'imu': self._imu_callback, 'steps': self._step_callback},
                                             'sensor_feedback', host=host, port=port)
        self.publisher = proccom.Publisher('reg_in', 'sensor_feedback_pub', self._format_output, host=host, port=port)
        self.thread = regutil.util.ScheduledTask(interval, self._task)

        self.acc_filter = dsp.core.MultiChannelFilter(3, [1])
        self.gyro_filter = dsp.core.MultiChannelFilter(3, [1])
        self.mag_filter = dsp.core.MultiChannelFilter(3, [1])

    def _format_output(self, orientation, angular_velocity, forward_velocity):
        return {
            'orientation': orientation,
            'angular_velocity': angular_velocity,
            'forward_velocity': forward_velocity
        }

    def _imu_callback(self, msg):
        data = msg['data']
        acc = data['acc']
        gyro = data['gyro']
        mag = data['mag']

        self.acc_filter.filter_values(acc)
        self.gyro_filter.filter_values(gyro)
        self.gyro_filter.filter_values(mag)

    def _step_callback(self, msg):
        pass

    def _task(self):
        acc = self.acc_filter.get_latest()
        gyro = self.gyro_filter.get_latest()
        mag = self.mag_filter.get_latest()

        # Calculate Orientation
        orientation = [1, 2, 3]
        # Calculate Angular velocity
        angular_velocity = [1, 2, 3]
        # Calculate Forward velocity
        forward_velocity = 1

        self.publisher.publish(orientation, angular_velocity, forward_velocity)


def main():
    pass


if __name__ == '__main__':
    main()
