from collections import defaultdict

class CityRelocator(object):
    def __init__(self):
        self.server = None
        self.kernels = 0
        self.model_ids = []

    def setController(self, controller):
        self.kernels = controller.kernels
        self.server = controller.server
        self.model_ids = controller.model_ids
        self.districts = defaultdict(list)
        for m in controller.total_model.componentSet:
            self.districts[m.district].append(m)
        self.districts = [self.districts[i] for i in range(len(self.districts))]

    def getRelocations(self, GVT, activities, horizon):
        # Ignore activities variable
        # Fetch all models and their activity
        if GVT < 100.0:
            # Still in warmup
            return {}
        previous_district_allocation = [district[0].location for district in self.districts]
        relocate = {}
        district_activities = defaultdict(float)
        for i in range(self.kernels):
            for model_id, activity in list(self.server.getProxy(i).getCompleteActivity().items()):
                district_activities[self.model_ids[model_id].district] += activity
        district_activities = [district_activities[i] for i in range(len(district_activities))]
        print(("All loads: " + str(district_activities)))
        # Shift the loads a little to 'predict the future'
        new_district_activities = list(district_activities)
        for index in range(len(district_activities)):
            leaving = district_activities[index] * (0.0015 * horizon)
            new_district_activities[index] -= leaving
            if index != len(district_activities) - 1:
                if index < 5:
                    arrived = 0
                else:
                    commercials_left = float(10-index)
                    arrived = leaving * ((commercials_left - 1) / (commercials_left))
                new_district_activities[index+1] += (leaving - arrived)
        print(("Guessed loads: " + str(new_district_activities)))
        district_activities = new_district_activities
        avg_activity_per_node = float(sum(district_activities)) / self.kernels
        if avg_activity_per_node < 20:
            # Not enough nodes to actually profit from the relocation
            return {}
        running_activity = 0.0
        district_allocation = []
        to_allocate = []
        for district, activity in enumerate(district_activities):
            if abs(running_activity - avg_activity_per_node) < abs(running_activity - avg_activity_per_node + activity):
                # Enough activity for this node, so put all these districts there
                district_allocation.append(to_allocate)
                running_activity = activity
                to_allocate = [district]
            else:
                running_activity += activity
                to_allocate.append(district)
        if len(district_allocation) < self.kernels:
            # Still have to add the last node
            district_allocation.append(to_allocate)
        else:
            district_allocation[-1].extend(to_allocate)
        print(("Migrating to %s" % district_allocation))
        for node, districts in enumerate(district_allocation):
            for district in districts:
                if previous_district_allocation[district] == node or (previous_district_allocation[district] < node and GVT > horizon):
                    continue
                print(("Moving " + str(district) + " to " + str(node)))
                for model in self.districts[district]:
                    relocate[model.model_id] = node
        return relocate

    def useLastStateOnly(self):
        return True
