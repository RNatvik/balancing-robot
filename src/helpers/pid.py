import time


class PID:

    def __init__(self, p: float, i: float, d: float, dt: float = None, ilim: list = None, olim: list = None):
        """
        A basic implementation of the PID algorithm

        :param p: Proportional gain
        :param i: Integral gain
        :param d: Derivative gain
        :param dt: expected regulator frequency.
         If dt is None calculate dt as the time between calls to calculate method, else use this value when calculate
         is called
        :param ilim: windup limit of the error sum.
        :param olim: output limit. Output values will be constrained within this limit
        """
        self.p = p
        self.i = i
        self.d = d
        self.dt = dt
        self.ilim = ilim
        self.olim = olim

        self.e0 = None
        self.t0 = None
        self.esum = 0

        self.type_error = False
        self.dt_error = False

    def initialize(self, e0: float = 0, delay: float = None):
        """
        Initializes the PID algorithm variables self.t0 and self.e0

        :param e0: initial "previous error" value
        :param delay: time to sleep after assigning initial values.
        :return:
        """
        self.t0 = time.time()
        self.t0 = e0
        if delay:
            time.sleep(delay)

    def calculate(self, measurement: float, target: float, dt: float = None, return_components: bool = False):
        """
        Run the PID algorithm once.
        This method will return None if not initialized properly OR dt is 0.
        The value of dt is prioritized in the following order "method parameter" -> "init parameter" -> "calculated dt"

        :param measurement: The measured system output value
        :param target: The target system output value
        :param dt: overrides dt parameter from init or calculated value if init dt is None.
        :param return_components: method returns only output if set to False.
        Method returns output, p-component, i-component and d-component as a tuple if set to True
        :return: PID algorithm output value. (Optional: (output, p, i d))
        """
        t = time.time()
        e = target - measurement

        # This try block handles variables that might not have been initialized.
        try:
            # Determine dt
            if dt is None:
                if self.dt:
                    dt = self.dt
                else:
                    dt = t - self.t0
            if not dt > 0:
                raise ValueError
            # Determine error
            de = e - self.e0
        except TypeError:
            self.type_error = True
            return None
        except ValueError:
            self.dt_error = True
            return None
        finally:
            self.esum += e
            self.t0 = t
            self.e0 = e

        self.type_error = False
        self.dt_error = False

        if self.ilim:
            self.esum = constrain(self.esum, self.ilim[0], self.ilim[1])

        p = self.p * e
        i = self.i * self.esum * dt
        d = self.d * de / dt

        output = p + i + d
        if self.olim:
            output = constrain(output, self.olim[0], self.olim[1])

        if return_components:
            return output, p, i, d
        else:
            return output

    def get_flags(self):
        """
        Returns error flags as tuple

        :return: (self.type_error, self.dt_error)
        """
        return self.type_error, self.dt_error


def constrain(value, min_v, max_v):
    """
    Constrains a value between a minimum and maximum value

    :param value: the value to constrain
    :param min_v: the minimum value
    :param max_v: the maximum value
    :return: constrained value
    """
    return min(max(value, min_v), max_v)
