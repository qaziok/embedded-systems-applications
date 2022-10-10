#!/usr/bin/python3

import RPi.GPIO as GPIO
from time import sleep

DEFAULT_REFRESH = 1

# GPIO.setup(0, GPIO.IN)
# GPIO.setup(0, GPIO.OUT)

# GPIO.output(0, GPIO.HIGH)
# GPIO.output(0, GPIO.LOW)

# pin1 = GPIO.input(0)

# print(pin1)
# print("done")

# zielone = [2,3,5,6,34,35,37,39,45,42,43,10,11,13,14,18,19,21,23,28,25,26]
# czerwone = [0,4,7,32,36,41,38,47,44,12,15,16,8,20,22,24,27]

class TrafficLightsPhase:
    def __init__(self, on_lights, arrows, lights, duration):
        """
            :param on_lights: lights indexes to be turned on
            :param arrows: lights indexes to show arrows
            :param lights: all traffic lights on an intersection
            :param duration: green light duration in refresh cycles (one refresh cycle is 1s by default)
        """
        self.on_lights = on_lights
        self.arrows = arrows
        self.lights = lights
        self.duration = duration

    def lights_function(self, function_name):
        output = []
        for i, light in enumerate(self.lights):
            if i in self.on_lights:
                points = getattr(light, function_name)()
            else:
                points = light.off(arrow=i in self.arrows and function_name == 'on')

            output.extend(points)
        return output

    def start(self):
        return self.lights_function('start')
            
    def running(self):
        sequence = self.lights_function('on')
        return (sequence for _ in range(self.duration))

    def stopping(self):
        return [
            self.lights_function('stop'),
            self.lights_function('off')
        ]
        

class TrafficLight:
    def __init__(self, lights, arrow=None):
        self.lights = lights
        self.arrow = arrow
    
    def start(self):
        return [self.lights[0], self.lights[1]]

    def on(self):
        return [self.lights[-1]]

    def stop(self):
        return [self.lights[1]]

    def off(self, arrow=False):
        if arrow:
            return [self.lights[0], self.arrow]
        else:
            return [self.lights[0]]

class PedestrianLight(TrafficLight):
    def __init__(self, lights):
        super().__init__(lights)

    def start(self):
        return [self.lights[0]]

    def stop(self):
        return [self.lights[0]]


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # buttons
    GPIO.setup(26, GPIO.IN)
    GPIO.setup(27, GPIO.IN)

    for i in [20,21,22,23,24,25]:
        GPIO.setup(i, GPIO.OUT)

def send_value(value):
    GPIO.output(21,GPIO.LOW)
    GPIO.output(20,GPIO.HIGH if value else GPIO.LOW)
    GPIO.output(21,GPIO.HIGH)

def show_lights():
    GPIO.output(22,GPIO.LOW)
    GPIO.output(22,GPIO.HIGH)
    GPIO.output(23,GPIO.LOW)
    GPIO.output(24,GPIO.LOW)
    GPIO.output(25,GPIO.LOW)
    sleep(DEFAULT_REFRESH)

def generate_pattern(lights):
    return [int(i in lights) for i in range(47,-1,-1)]

def send48bites(on_lights_list):
    print(generate_pattern(on_lights_list)[::-1])
    for v in generate_pattern(on_lights_list):
        send_value(v)
    show_lights()

def pedestrian_button_pressed():
    return GPIO.input(26) or GPIO.input(27)

def run_phase(state):
    send48bites(state.start())

    for lights in state.running():
        if pedestrian_button_pressed():
            break
        send48bites(lights)

    for lights in state.stopping():
        send48bites(lights)

traffic_lights = [
    # east
    TrafficLight([0,1,2],arrow=3), #0
    # west
    TrafficLight([8,9,10],arrow=11), #1
    # north
    TrafficLight([16,17,18],arrow=19), #2
    TrafficLight([30,29,28]), #3
    # south
    TrafficLight([32,33,34],arrow=35), #4
    TrafficLight([47,46,45]), #5
    # east pedestrian
    PedestrianLight([4,5]), #6
    PedestrianLight([7,6]), #7
    # south pedestrian
    PedestrianLight([36,37]), #8
    PedestrianLight([38,39]), #9
    PedestrianLight([41,42]), #10
    PedestrianLight([44,43]), #11
    # west pedestrian
    PedestrianLight([12,13]), #12
    PedestrianLight([15,14]), #13
    # north pedestrian
    PedestrianLight([20,21]), #14
    PedestrianLight([22,23]), #15
    PedestrianLight([24,25]), #16
    PedestrianLight([27,26]), #17
    ]

traffic_lights_phases = [
    TrafficLightsPhase([2,4,6,7,12,13], [0,1], traffic_lights, 8),
    TrafficLightsPhase([0,1,15,14,8,9], [2,4], traffic_lights, 5),
    TrafficLightsPhase([3,5,16,17,10,11], [0,1], traffic_lights, 5),
]

if __name__ == "__main__":
    setup()
    while True:
        for phase in traffic_lights_phases:
            run_phase(phase)
