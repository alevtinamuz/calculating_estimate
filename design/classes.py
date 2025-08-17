class WorkItem:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.quantity = 0.0
        self.labor_cost = 0.0
        self.total_work = 0.0
        self.materials = [MaterialItem()]  # Список MaterialItem
        self.row = 0
        self.number = 0
        self.height = 1
        self.total_materials = 0.0

    def calc_total_materials(self):
        s = 0
        for material in self.materials:
            s += material.total

        return s


class MaterialItem:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.quantity = 0.0
        self.price = 0.0
        self.total = 0.0
        self.row = 0

    def calc_total(self):
        return self.quantity * self.price


class SectionItem:
    def __init__(self):
        self.name = ""
        self.works = []
        self.total = 0.0
        self.row = 0
        self.height = 0

    def calc_total(self):
        s = 0
        for work in self.works:
            s += work.total

        return s
