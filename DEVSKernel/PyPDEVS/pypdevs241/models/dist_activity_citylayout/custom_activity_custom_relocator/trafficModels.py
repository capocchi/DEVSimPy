import sys
sys.path.append("../../../src/")
from infinity import *
from DEVS import *
import random

north = 0
east = 1
south = 2
west = 3
vertical = "02"
horizontal = "13"
dir_to_int = {'n': north, 'e': east, 's': south, 'w': west}
int_to_dir = {north: 'n', east: 'e', south: 's', west: 'w'}

class Car:
    def __init__(self, ID, v, v_pref, dv_pos_max, dv_neg_max, departure_time):
        self.ID = ID
        self.v_pref = v_pref
        self.dv_pos_max = dv_pos_max
        self.dv_neg_max = dv_neg_max
        self.departure_time = departure_time
        self.distance_travelled = 0
        self.remaining_x = 0
        self.v = v

    def __eq__(self, other):
        return (self.ID == other.ID and
            self.v_pref == other.v_pref and
            self.dv_pos_max == other.dv_pos_max and
            self.dv_neg_max == other.dv_neg_max and
            self.departure_time == other.departure_time and
            self.distance_travelled == other.distance_travelled and
            self.remaining_x == other.remaining_x and
            self.v == other.v)

    def __str__(self):
        return "Car: ID = " + str(self.ID) + ", v_pref = " + str(self.v_pref) + ", dv_pos_max = " + str(self.dv_pos_max) + ", dv_neg_max = " + str(self.dv_neg_max) + ", departure_time = " + str(self.departure_time) + ", distance_travelled = " + str(self.distance_travelled) + (", v = %3f" % self.v) + ", path = " + str(self.path)

    def copy(self):
        car = Car(self.ID, self.v, self.v_pref, self.dv_pos_max, self.dv_neg_max, self.departure_time)
        car.distance_travelled = self.distance_travelled
        car.remaining_x = self.remaining_x
        car.path = list(self.path)
        return car

class Query:
    def __init__(self, ID):
        self.ID = ID
        self.direction = ''

    def __str__(self):
        return "Query: ID = " + str(self.ID)

    def __eq__(self, other):
        return (self.ID == other.ID and self.direction == other.direction)

    def copy(self):
        query = Query(self.ID)
        query.direction = self.direction
        return query

class QueryAck:
    def __init__(self, ID, t_until_dep):
        self.ID = ID
        self.t_until_dep = t_until_dep

    def __str__(self):
        return "Query Ack: ID = " + str(self.ID) + ", t_until_dep = %.3f" % self.t_until_dep

    def __eq__(self, other):
        return (self.ID == other.ID and self.t_until_dep == other.t_until_dep)

    def copy(self):
        return QueryAck(self.ID, self.t_until_dep)

class BuildingState: 
    def __init__(self, IAT_min, IAT_max, path, name):
        self.currentTime = 0
        from randomGenerator import RandomGenerator
        seed = random.random()
        self.randomGenerator = RandomGenerator(seed)
        self.send_query_delay = self.randomGenerator.uniform(IAT_min, IAT_max)

        self.send_car_delay = INFINITY
        self.path = path
        if path == []:
            self.send_query_delay = INFINITY

        self.name = name
        self.send_query_id = int(name.split("_", 1)[1].split("_")[0]) * 1000 + int(name.split("_", 1)[1].split("_")[1])
        self.send_car_id = self.send_query_id
        self.next_v_pref = 0
        self.sent = 0

    def copy(self):
        new = BuildingState(0, 0, list(self.path), self.name)
        new.currentTime = self.currentTime
        new.send_query_delay = self.send_query_delay
        new.send_car_delay = self.send_car_delay
        new.send_query_id = self.send_query_id
        new.send_car_id = self.send_car_id
        new.next_v_pref = self.next_v_pref
        new.randomGenerator = self.randomGenerator.copy()
        new.sent = self.sent
        return new

    def __str__(self):
        if self.path != []:
            return "Residence: send_query_delay = %.3f, send_query_id = %s, send_car_delay = %.3f, send_car_id = %s" % (self.send_query_delay, self.send_query_id, self.send_car_delay, self.send_car_id)
        else:
            return "Commercial: waiting..."

class Building(AtomicDEVS):
    def __init__(self, generator, district, path = [], IAT_min = 100, IAT_max = 100, v_pref_min = 15, v_pref_max = 15, dv_pos_max = 15, dv_neg_max = 150, name="Building"):
        # parent class constructor
        AtomicDEVS.__init__(self, name)

        # copy of arguments
        self.IAT_min = IAT_min
        self.IAT_max = IAT_max
        self.v_pref_min = v_pref_min
        self.v_pref_max = v_pref_max
        self.dv_pos_max = dv_pos_max
        self.dv_neg_max = dv_neg_max

        # output ports
        self.q_sans = self.addOutPort(name="q_sans")
        self.q_send = self.addOutPort(name="q_send")
        self.exit = self.addOutPort(name="exit")
        self.Q_send = self.q_send
        self.car_out = self.exit

        # input ports
        self.q_rans = self.addInPort(name="q_rans")
        #self.q_recv = self.addInPort(name="q_recv")
        self.Q_rack = self.q_rans
        self.entry = self.addInPort(name="entry")

        # set the state
        self.state = BuildingState(IAT_min, IAT_max, path, name)
        self.state.next_v_pref = self.state.randomGenerator.uniform(self.v_pref_min, self.v_pref_max)
        self.send_max = 1

        self.district = district

    def intTransition(self):
        mintime = self.timeAdvance()
        #print("Got mintime: " + str(mintime))
        self.state.currentTime += mintime

        self.state.send_query_delay -= mintime
        self.state.send_car_delay -= mintime

        if self.state.send_car_delay == 0:
            self.state.send_car_delay = INFINITY
            self.state.send_car_id = self.state.send_query_id
            self.state.next_v_pref = self.state.randomGenerator.uniform(self.v_pref_min, self.v_pref_max)
        elif self.state.send_query_delay == 0:
            self.state.send_query_delay = INFINITY

        return self.state
            
    def outputFnc(self):
        mintime = self.timeAdvance()
        #print("Got mintime: " + str(mintime))
        currentTime = self.state.currentTime + self.timeAdvance()
        outputs = {}

        if self.state.send_car_delay == mintime:
            v_pref = self.state.next_v_pref
            car = Car(self.state.send_car_id, 0, v_pref, self.dv_pos_max, self.dv_neg_max, currentTime)
            car.path = self.state.path
            #self.poke(self.car_out, car)
            outputs[self.car_out] = [car]
        elif self.state.send_query_delay == mintime:
            query = Query(self.state.send_query_id)
            #self.poke(self.Q_send, query)
            outputs[self.Q_send] = [query]
        return outputs
    
    def timeAdvance(self):
        return min(self.state.send_query_delay, self.state.send_car_delay)

    def extTransition(self, inputs):
        #print("ELAPSED: " + str(self.elapsed))
        #print("Got elapsed: " + str(self.elapsed))
        self.state.currentTime += self.elapsed
        self.state.send_query_delay -= self.elapsed
        self.state.send_car_delay -= self.elapsed
        queryAcks = inputs.get(self.Q_rack, [])
        for queryAck in queryAcks:
          if self.state.send_car_id == queryAck.ID and (self.state.sent < self.send_max):
            self.state.send_car_delay = queryAck.t_until_dep
            if queryAck.t_until_dep < 20000:
                self.state.sent += 1
                # Generate the next situation
                if self.state.sent < self.send_max:
                    self.state.send_query_delay = self.randomGenerator.uniform(self.IAT_min, self.IAT_max)
                    #self.state.send_query_id = int(self.randomGenerator.uniform(0, 100000))
                    self.state.send_query_id += 1000000
        return self.state

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        return 0 if self.state.send_car_delay == float('inf') else 1

class Residence(Building):
    def __init__(self, path, district, name = "Residence", IAT_min = 100, IAT_max = 100, v_pref_min = 15, v_pref_max = 15, dv_pos_max = 15, dv_neg_max = 15):
        Building.__init__(self, True, district, path=path, name=name)

class CommercialState(object):
    def __init__(self, car):
        self.car = car

    def __str__(self):
        return "CommercialState"

    def copy(self):
        return CommercialState(self.car)

class Commercial(Building):
    def __init__(self, district, name="Commercial"):
        Building.__init__(self, False, district, name=name)
        self.state = CommercialState(None)
        self.toCollector = self.addOutPort(name="toCollector")

    def extTransition(self, inputs):
        return CommercialState(inputs[self.entry][0])

    def intTransition(self):
        return CommercialState(None)

    def outputFnc(self):
        return {self.toCollector: [self.state.car]}

    def timeAdvance(self):
        if self.state.car is None:
            return INFINITY
        else:
            return 0.0

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        return 0
            
class RoadSegmentState():
    def __init__(self):
        self.cars_present = []
        self.query_buffer = []
        self.deny_list = []
        self.reserved = False
        self.send_query_delay = INFINITY
        self.send_query_id = None
        self.send_ack_delay = INFINITY
        self.send_ack_id = None
        self.send_car_delay = INFINITY
        self.send_car_id = None
        self.last_car = None

    def __eq__(self, other):
        if not (self.send_query_delay == other.send_query_delay and
              self.send_ack_delay == other.send_ack_delay and
              self.send_car_delay == other.send_car_delay and
              self.send_query_id == other.send_query_id and
              self.send_ack_id == other.send_ack_id and
              self.send_car_id == other.send_car_id and
              self.last_car == other.last_car and
              self.reserved == other.reserved):
            return False
        if self.query_buffer != other.query_buffer:
            return False
        if len(self.cars_present) != len(other.cars_present):
            return False
        for c1, c2 in zip(self.cars_present, other.cars_present):
            if c1 != c2:
                return False
        if len(self.deny_list) != len(other.deny_list):
            return False
        for q1, q2 in zip(self.deny_list, other.deny_list):
            if q1 != q2:
                return False
        return True

    def copy(self):
        new = RoadSegmentState()
        new.cars_present = [c.copy() for c in self.cars_present]
        new.query_buffer = list(self.query_buffer)
        new.deny_list = [q.copy() for q in self.deny_list]
        new.reserved = self.reserved
        new.send_query_delay = self.send_query_delay
        new.send_query_id = self.send_query_id
        new.send_ack_delay = self.send_ack_delay
        new.send_ack_id = self.send_ack_id
        new.send_car_delay = self.send_car_delay
        new.send_car_id = self.send_car_id
        new.last_car = self.last_car
        return new

    def __str__(self):
        string = "Road segment: cars_present = ["
        for i in self.cars_present:
            string += str(i.ID) + ", "
        return string + "] , send_query_delay = %.3f, send_ack_delay = %.3f, send_car_delay = %.3f, send_ack_id = %s" % (self.send_query_delay, self.send_ack_delay, self.send_car_delay, self.send_ack_id)

class RoadSegment(AtomicDEVS):
    def __init__(self, district, load, l = 100.0, v_max = 18.0, observ_delay = 0.1, name = "RoadSegment"):
        AtomicDEVS.__init__(self, name)

        # arguments
        self.l = float(l)
        self.v_max = v_max
        self.observ_delay = observ_delay
        self.district = district
        self.load = load

        # in-ports
        self.q_rans = self.addInPort(name="q_rans")
        self.q_recv = self.addInPort(name="q_recv")
        self.car_in = self.addInPort(name="car_in")
        self.entries = self.addInPort(name="entries")
        self.q_rans_bs = self.addInPort(name="q_rans_bs")
        self.q_recv_bs = self.addInPort(name="q_recv_bs")
        # compatibility bindings...
        self.Q_recv = self.q_recv
        self.Q_rack = self.q_rans

        # out-ports
        self.q_sans = self.addOutPort(name="q_sans")
        self.q_send = self.addOutPort(name="q_send")
        self.car_out = self.addOutPort(name="car_out")
        self.exits = self.addOutPort(name="exits")

        self.q_sans_bs = self.addOutPort(name="q_sans_bs")
        # compatibility bindings...
        self.Q_send = self.q_send
        self.Q_sack = self.q_sans

        self.state = RoadSegmentState()

    def extTransition(self, inputs):
        queries = inputs.get(self.Q_recv, [])
        queries.extend(inputs.get(self.q_recv_bs, []))
        cars = inputs.get(self.car_in, [])
        cars.extend(inputs.get(self.entries, []))
        acks = inputs.get(self.Q_rack, [])
        acks.extend(inputs.get(self.q_rans_bs, []))

        self.state.send_query_delay -= self.elapsed
        self.state.send_ack_delay -= self.elapsed
        self.state.send_car_delay -= self.elapsed

        for query in queries:
            if (not self.state.reserved) and not (len(self.state.cars_present) > 1 or (len(self.state.cars_present) == 1 and self.state.cars_present[0].v == 0)):
                self.state.send_ack_delay = self.observ_delay
                self.state.send_ack_id = query.ID
                self.state.reserved = True
            else:
                self.state.query_buffer.append(query.ID)
                self.state.deny_list.append(query)
                if self.state.send_ack_delay == INFINITY:
                    self.state.send_ack_delay = self.observ_delay
                    self.state.send_ack_id = query.ID
            self.state.last_car = query.ID
        for car in self.state.cars_present:
            car.remaining_x -= self.elapsed * car.v

        for car in cars:
            self.state.last_car = None
            car.remaining_x = self.l
            self.state.cars_present.append(car)

            if len(self.state.cars_present) != 1:
                for other_car in self.state.cars_present:
                    other_car.v = 0
                self.state.send_query_delay = INFINITY
                self.state.send_ack_delay = INFINITY
                self.state.send_car_delay = INFINITY
            else:
                self.state.send_query_delay = 0
                self.state.send_query_id = car.ID
                if self.state.cars_present[-1].v == 0:
                    t_to_dep = INFINITY
                else:
                    t_to_dep = max(0, self.l/self.state.cars_present[-1].v)
                self.state.send_car_delay = t_to_dep
                self.state.send_car_id = car.ID

        for ack in acks:
            if (len(self.state.cars_present) == 1) and (ack.ID == self.state.cars_present[0].ID):
                car = self.state.cars_present[0]
                t_no_col = ack.t_until_dep
                v_old = car.v
                v_pref = car.v_pref
                remaining_x = car.remaining_x

                if t_no_col + 1 == t_no_col:
                    v_new = 0
                    t_until_dep = INFINITY
                else:
                    v_ideal = remaining_x / max(t_no_col, remaining_x / min(v_pref, self.v_max))
                    diff = v_ideal - v_old
                    if diff < 0:
                        if -diff > car.dv_neg_max:
                            diff = -car.dv_neg_max
                    elif diff > 0:
                        if diff > car.dv_pos_max:
                            diff = car.dv_pos_max
                    v_new = v_old + diff
                    if v_new == 0:
                      t_until_dep = INFINITY
                    else:
                      t_until_dep = car.remaining_x / v_new
                
                car.v = v_new

                t_until_dep = max(0, t_until_dep)
                if t_until_dep > self.state.send_car_delay and self.state.last_car is not None:
                    self.state.send_ack_delay = self.observ_delay
                    self.state.send_ack_id = self.state.last_car
                self.state.send_car_delay = t_until_dep
                self.state.send_car_id = ack.ID

                if t_until_dep == INFINITY:
                  self.state.send_query_id = ack.ID
                else:
                  self.state.send_query_id = None
                self.state.send_query_delay = INFINITY
        return self.state

    def intTransition(self):
        for _ in range(self.load):
            pass
        mintime = self.mintime()
        self.state.send_query_delay -= mintime
        self.state.send_ack_delay -= mintime
        self.state.send_car_delay -= mintime
        if self.state.send_ack_delay == 0:
            self.state.send_ack_delay = INFINITY
            self.state.send_ack_id = None

        elif self.state.send_query_delay == 0:
            # Just sent a query, now deny all other queries and wait until the current car has left
            self.state.send_query_delay = INFINITY
            self.state.send_query_id = None
        elif self.state.send_car_delay == 0:
            self.state.cars_present = []
            self.state.send_car_delay = INFINITY
            self.state.send_car_id = None

            # A car has left, so we can answer to the first other query we received
            if len(self.state.query_buffer) != 0:
                self.state.send_ack_delay = self.observ_delay
                #print("Setting %s in %s" % (self.state.query_buffer, self.name))
                self.state.send_ack_id = self.state.query_buffer.pop()
            else:
                # No car is waiting for this segment, so 'unreserve' it
                self.state.reserved = False
        if self.state.send_ack_id == None and len(self.state.deny_list) > 0:
            self.state.send_ack_delay = self.observ_delay
            #print("Denylist = %s in %s" % (self.state.deny_list, self.name))
            self.state.send_ack_id = self.state.deny_list[0].ID
            self.state.deny_list = self.state.deny_list[1:]

        return self.state

    def outputFnc(self):
        outputs = {}
        mintime = self.mintime()
        if self.state.send_ack_delay == mintime:
            ackID = self.state.send_ack_id
            if len(self.state.cars_present) == 0:
                t_until_dep = 0
            elif (self.state.cars_present[0].v) == 0:
                t_until_dep = INFINITY
            else:
                t_until_dep = self.l / self.state.cars_present[0].v
            ack = QueryAck(ackID, t_until_dep)
            outputs[self.Q_sack] = [ack]
            outputs[self.q_sans_bs] = [ack]
        elif self.state.send_query_delay == mintime:
            query = Query(self.state.send_query_id)
            if self.state.cars_present[0].path != []:
                query.direction = self.state.cars_present[0].path[0]
                outputs[self.Q_send] = [query]
        elif self.state.send_car_delay == mintime:
            car = self.state.cars_present[0]
            car.distance_travelled += self.l
            if len(car.path) == 0:
                outputs[self.exits] = [car]
            else:
                outputs[self.car_out] = [car]
        return outputs

    def mintime(self):
        return min(self.state.send_query_delay, self.state.send_ack_delay, self.state.send_car_delay)

    def timeAdvance(self):
        #return min(self.state.send_query_delay, self.state.send_ack_delay, self.state.send_car_delay)
        delay = min(self.state.send_query_delay, self.state.send_ack_delay, self.state.send_car_delay)
        # Take care of floating point errors
        return max(delay, 0)

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        # If a car has collided, no activity is here
        return 1 if len(self.state.cars_present) == 1 else 0

class Road(CoupledDEVS):
    def __init__(self, district, load, name="Road", segments=5):
        CoupledDEVS.__init__(self, name)
        self.segment = []
        for i in range(segments):
            self.segment.append(self.addSubModel(RoadSegment(load=load, district=district, name=(name + "_" + str(i)))))

        # in-ports
        self.q_rans = self.addInPort(name="q_rans")
        self.q_recv = self.addInPort(name="q_recv")
        self.car_in = self.addInPort(name="car_in")
        self.entries = self.addInPort(name="entries")
        self.q_rans_bs = self.addInPort(name="q_rans_bs")
        self.q_recv_bs = self.addInPort(name="q_recv_bs")

        # out-ports
        self.q_sans = self.addOutPort(name="q_sans")
        self.q_send = self.addOutPort(name="q_send")
        self.car_out = self.addOutPort(name="car_out")
        self.exits = self.addOutPort(name="exits")
        self.q_sans_bs = self.addOutPort(name="q_sans_bs")

        self.connectPorts(self.q_rans, self.segment[-1].q_rans)
        self.connectPorts(self.q_recv, self.segment[0].q_recv)
        self.connectPorts(self.car_in, self.segment[0].car_in)
        self.connectPorts(self.entries, self.segment[0].entries)
        self.connectPorts(self.q_rans_bs, self.segment[0].q_rans_bs)
        self.connectPorts(self.q_recv_bs, self.segment[0].q_recv_bs)

        self.connectPorts(self.segment[0].q_sans, self.q_sans)
        self.connectPorts(self.segment[-1].q_send, self.q_send)
        self.connectPorts(self.segment[-1].car_out, self.car_out)
        self.connectPorts(self.segment[0].exits, self.exits)
        self.connectPorts(self.segment[0].q_sans_bs, self.q_sans_bs)

        for i in range(segments):
            if i == 0:
                continue
            self.connectPorts(self.segment[i].q_sans, self.segment[i-1].q_rans)
            self.connectPorts(self.segment[i-1].q_send, self.segment[i].q_recv)
            self.connectPorts(self.segment[i-1].car_out, self.segment[i].car_in)

class IntersectionState():
    def __init__(self, switch_signal):
        self.send_query = []
        self.send_ack = []
        self.send_car = []
        self.queued_queries = []
        self.id_locations = [None, None, None, None]
        self.block = vertical
        self.switch_signal = switch_signal
        self.ackDir = {}

    def __str__(self):
        return "ISECT blocking " + str(self.block)
        return "Intersection: send_query = " + str(self.send_query) + ", send_ack = " + str(self.send_ack) + ", send_car = " + str(self.send_car) + ", block = " + str(self.block)

    def copy(self):
        new = IntersectionState(self.switch_signal)
        new.send_query = [q.copy() for q in self.send_query]
        new.send_ack = [a.copy() for a in self.send_ack]
        new.send_car = [c.copy() for c in self.send_car]
        new.queued_queries = [q.copy() for q in self.queued_queries]
        new.id_locations = list(self.id_locations)
        new.block = self.block
        new.switch_signal = self.switch_signal
        new.ackDir = dict(self.ackDir)
        return new

class Intersection(AtomicDEVS):
    def __init__(self, district, name="Intersection", switch_signal = 30):
        AtomicDEVS.__init__(self, name=name)
        self.state = IntersectionState(switch_signal)
        self.switch_signal_delay = switch_signal
        self.district = district

        self.q_send = []
        self.q_send.append(self.addOutPort(name="q_send_to_n"))
        self.q_send.append(self.addOutPort(name="q_send_to_e"))
        self.q_send.append(self.addOutPort(name="q_send_to_s"))
        self.q_send.append(self.addOutPort(name="q_send_to_w"))

        self.q_rans = []
        self.q_rans.append(self.addInPort(name="q_rans_from_n"))
        self.q_rans.append(self.addInPort(name="q_rans_from_e"))
        self.q_rans.append(self.addInPort(name="q_rans_from_s"))
        self.q_rans.append(self.addInPort(name="q_rans_from_w"))

        self.q_recv = []
        self.q_recv.append(self.addInPort(name="q_recv_from_n"))
        self.q_recv.append(self.addInPort(name="q_recv_from_e"))
        self.q_recv.append(self.addInPort(name="q_recv_from_s"))
        self.q_recv.append(self.addInPort(name="q_recv_from_w"))

        self.q_sans = []
        self.q_sans.append(self.addOutPort(name="q_sans_to_n"))
        self.q_sans.append(self.addOutPort(name="q_sans_to_e"))
        self.q_sans.append(self.addOutPort(name="q_sans_to_s"))
        self.q_sans.append(self.addOutPort(name="q_sans_to_w"))

        self.car_in = []
        self.car_in.append(self.addInPort(name="car_in_from_n"))
        self.car_in.append(self.addInPort(name="car_in_from_e"))
        self.car_in.append(self.addInPort(name="car_in_from_s"))
        self.car_in.append(self.addInPort(name="car_in_from_w"))

        self.car_out = []
        self.car_out.append(self.addOutPort(name="car_out_to_n"))
        self.car_out.append(self.addOutPort(name="car_out_to_e"))
        self.car_out.append(self.addOutPort(name="car_out_to_s"))
        self.car_out.append(self.addOutPort(name="car_out_to_w"))

    def intTransition(self):
        self.state.switch_signal -= self.timeAdvance()
        if self.state.switch_signal <= 1e-6:
            # We switched our traffic lights
            self.state.switch_signal = self.switch_signal_delay
            self.state.queued_queries = []
            self.state.block = vertical if self.state.block == horizontal else horizontal

            for loc, car_id in enumerate(self.state.id_locations):
                # Notify all cars that got 'green' that they should not continue
                if car_id is None:
                    continue
                try:
                    if str(loc) in self.state.block:
                        query = Query(car_id)
                        query.direction = int_to_dir[self.state.ackDir[car_id]]
                        self.state.queued_queries.append(query)
                except KeyError:
                    pass
        self.state.send_car = []
        self.state.send_query = []
        self.state.send_ack = []
        return self.state

    def extTransition(self, inputs):
        # Simple forwarding of all messages
        # Unless the direction in which it is going is blocked
        self.state.switch_signal -= self.elapsed
        for direction in range(4):
            blocked = str(direction) in self.state.block
            for car in inputs.get(self.car_in[direction], []):
                self.state.send_car.append(car)
                # Got a car, so remove its ID location entry
                try:
                    del self.state.ackDir[car.ID]
                    self.state.id_locations[self.state.id_locations.index(car.ID)] = None
                except (KeyError, ValueError):
                    pass
                self.state.queued_queries = [query for query in self.state.queued_queries if query.ID != car.ID]
            for query in inputs.get(self.q_recv[direction], []):
                self.state.id_locations[direction] = query.ID
                self.state.ackDir[query.ID] = dir_to_int[query.direction]
                if blocked:
                    self.state.send_ack.append(QueryAck(query.ID, INFINITY))
                    self.state.queued_queries.append(query)
                else:
                    self.state.send_query.append(query)
            for ack in inputs.get(self.q_rans[direction], []):
                self.state.ackDir[ack.ID] = direction
                if (ack.t_until_dep > self.state.switch_signal) or ((ack.ID in self.state.id_locations) and (str(self.state.id_locations.index(ack.ID)) in self.state.block)):
                    try:
                        self.state.id_locations.index(ack.ID)
                        t_until_dep = INFINITY
                        nquery = Query(ack.ID)
                        nquery.direction = int_to_dir[direction]
                        self.state.queued_queries.append(nquery)
                    except ValueError:
                        continue
                else:
                    t_until_dep = ack.t_until_dep
                self.state.send_ack.append(QueryAck(ack.ID, t_until_dep))
        return self.state

    def outputFnc(self):
        # Can simply overwrite, as multiple calls to the same destination is impossible
        toSend = {}
        new_block = vertical if self.state.block == horizontal else horizontal
        if self.state.switch_signal == self.timeAdvance():
            # We switch our traffic lights
            # Resend all queries for those that are waiting
            for query in self.state.queued_queries:
                if str(self.state.id_locations.index(query.ID)) not in new_block:
                    toSend[self.q_send[dir_to_int[query.direction]]] = [query]
            for loc, car_id in enumerate(self.state.id_locations):
                # Notify all cars that got 'green' that they should not continue
                if car_id is None:
                    continue
                if str(loc) in new_block:
                    toSend[self.q_sans[loc]] = [QueryAck(car_id, INFINITY)]
                else:
                    try:
                        query = Query(car_id)
                        query.direction = int_to_dir[self.state.ackDir[car_id]]
                        toSend[self.q_send[self.state.ackDir[car_id]]] = [query]
                    except KeyError:
                        pass
        # We might have some messages to forward too
        for car in self.state.send_car:
            dest = car.path.pop(0)
            toSend[self.car_out[dir_to_int[dest]]] = [car]
        for query in self.state.send_query:
            toSend[self.q_send[dir_to_int[query.direction]]] = [query]
        for ack in self.state.send_ack:
            # Broadcast for now
            try:
                toSend[self.q_sans[self.state.id_locations.index(ack.ID)]] = [ack]
            except ValueError:
                pass
        return toSend

    def timeAdvance(self):
        if len(self.state.send_car) + len(self.state.send_query) + len(self.state.send_ack) > 0:
            return 0.0
        else:
            return max(self.state.switch_signal, 0.0)

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        return len(self.state.send_car)

class CollectorState(object):
    def __init__(self):
        self.cars = []

    def copy(self):
        new = CollectorState()
        new.cars = list(self.cars)
        return new

    def __str__(self):
        ## Print your statistics here!
        s = "All cars collected:"
        for car in self.cars:
            s += "\n\t\t\t%s" % car 
        return s

class Collector(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "Collector")
        self.car_in = self.addInPort("car_in")
        self.state = CollectorState()
        self.district = 0

    def extTransition(self, inputs):
        self.state.cars.extend(inputs[self.car_in])
        return self.state

    def preActivityCalculation(self):
        return None

    def postActivityCalculation(self, _):
        return 0
