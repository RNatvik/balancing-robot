import proccom
import dsp


class MultiChannelFilter:

    def __init__(self, channels: int, b: list, a: list = None, k: float = 1):
        self.channels = channels
        self.filters = []
        for i in range(self.channels):
            self.filters.append(dsp.core.Filter(b, a=a, k=k))

    def filter_values(self, values):
        """
        Filters values
        :param values: values to filter
        :return: filtered values
        """
        filtered_values = [0] * self.channels
        if len(values) == self.channels:
            for i in range(self.channels):
                filtered_values[i] = self.filters[i].filter_value(values[i])
        else:
            filtered_values = None

        filtered_values = [self.filters[i].filter_value(values[i]) for i in range(self.channels)]
        return filtered_values


class ImuFilter:

    def __init__(self, host, port):
        self.subscriber = proccom.Subscriber({'imu': self.imu_callback}, 'imu_filter', host=host, port=port)

    def imu_callback(self, msg):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
