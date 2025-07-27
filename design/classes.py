class WorkItem:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.quantity = 1
        self.labor_cost = 0.0
        self.total = 0.0
        self.materials = [MaterialItem()]  # Список MaterialItem
        self.row = 0
        self.number = 0
        self.height = 1
        self.total_materials = 0.0


class MaterialItem:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.quantity = 0
        self.price = 0.0
        self.total = 0.0
        self.row = 0
