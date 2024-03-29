from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import sin, cos, radians
from random import random, randrange

AGENT_MODES = {
    KEY._1: 'seek',
    KEY._2: 'arrive_slow',
    KEY._3: 'arrive_normal',
    KEY._4: 'arrive_fast',
    KEY._6: 'flee',
    KEY._7: 'pursuit'
} 


class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    DECELERATION_SPEEDS = {
        'slow': 0.9,
        'normal': 0.6,
        'fast': 0.3,
    }

    def __init__(self, world=None, scale=30.0, mass=1.0, mode='flee'):
        # keep a reference to the world object
        self.world = world
        self.mode = mode
        # where am i and where am i going? random
        dir = radians(random()*360)
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))
        self.vel = Vector2D()
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)  # easy scaling of agent size
        self.acceleration = Vector2D()  # current steering force
        self.mass = mass
        # limits?
        self.max_speed = 5000.0
        # data for drawing this agent
        self.color = 'ORANGE'
        self.vehicle_shape = [
            Point2D(-1.0,  0.6),
            Point2D( 1.0,  0.0),
            Point2D(-1.0, -0.6)


        ]

    def calculate(self):
        # reset the steering force
        mode = self.mode
        if mode == 'seek':
            accel = self.seek(self.world.target)
        elif mode == 'arrive_slow':
            accel = self.arrive(self.world.target, 'slow')
        elif mode == 'arrive_normal':
            accel = self.arrive(self.world.target, 'normal') #originally named force, now accel
        elif mode == 'arrive_fast':
            accel = self.arrive(self.world.target, 'fast') #originally named force, now accel
        elif mode == 'flee':
            accel = self.flee(self.world.target)
        elif mode == 'pursuit':
            accel = self.pursuit(self.world.hunter)
        else:
            accel = Vector2D()
        self.acceleration = accel
        return accel

    def update(self, delta):
        ''' update vehicle position and orientation '''
        acceleration = self.calculate()
        # new velocity
        self.vel += acceleration * delta
        # check for limits of new velocity
        self.vel.truncate(self.max_speed)
        # update position
        self.pos += self.vel * delta
        # update heading is non-zero velocity (moving)
        if self.vel.lengthSq() > 0.00000001:
            self.heading = self.vel.get_normalised()
            self.side = self.heading.perp()
        # treat world as continuous space - wrap new position if needed
        self.world.wrap_around(self.pos)

    def render(self, color=None):
        ''' Draw the triangle agent with color'''
        if(color == None):
            egi.set_pen_color(name=self.color)
        else:
            egi.set_pen_color(name=color)
        pts = self.world.transform_points(self.vehicle_shape, self.pos,
                                          self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)

    def flee(self, hunter_pos):
        ''' move away from hunter position '''
## add panic distance (second)
## add flee calculations (first)

        if(Vector2D.distance(self.pos, hunter_pos) < 100):
            desired_vel = (self.pos - hunter_pos).normalise() * self.max_speed
            return (desired_vel - self.vel)
        elif(Vector2D.distance(self.pos, hunter_pos) > 300):
            return self.seek(hunter_pos) 
        else:
            return Vector2D()

    def arrive(self, target_pos, speed):
        ''' this behaviour is similar to seek() but it attempts to arrive at
            the target position with a zero velocity'''
        decel_rate = self.DECELERATION_SPEEDS[speed]
        to_target = target_pos - self.pos
        dist = to_target.length()
        if dist > 0:
            # calculate the speed required to reach the target given the
            # desired deceleration rate
            speed = dist / decel_rate
            # make sure the velocity does not exceed the max
            speed = min(speed, self.max_speed)
            # from here proceed just like Seek except we don't need to
            # normalize the to_target vector because we have already gone to the
            # trouble of calculating its length for dist.
            desired_vel = to_target * (speed / dist)
            return (desired_vel - self.vel)
        return Vector2D(0, 0)

    def pursuit(self, evader):
        ''' this behaviour predicts where an agent will be in time T and seeks
            towards that point to intercept it. '''
        evader.mode = 'flee'
## OPTIONAL EXTRA... pursuit (you'll need something to pursue!)
        self.toEvader = evader.pos - self.pos
        self.relHeading = Vector2D.dot(evader.heading, self.heading)

        if(Vector2D.dot(self.toEvader, self.heading) > 0 and self.relHeading < -0.5):
            return self.seek(evader.pos)

        lookAheadTime = Vector2D.length(self.toEvader) / (self.max_speed + evader.speed())
        return self.seek(evader.pos + evader.vel * lookAheadTime)
        