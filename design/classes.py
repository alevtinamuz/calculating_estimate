class WorkItem:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.quantity = 1
        self.labor_cost = 0.0
        self.materials = []  # Список MaterialItem


class MaterialItem:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.quantity = 0
        self.price = 0.0
        self.total = 0.0