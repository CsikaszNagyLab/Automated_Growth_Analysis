import csv
class Layout:
    def __init__(self, file_path):
        self.valid = True
        self.layout_id = ""
        self.mapping = dict()
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            self.layout_id = next(reader)[0]
            for line in reader:
                if len(line) > 3 or len(line) < 2:
                    self.valid = False
                    return
                self.mapping[line[0]] = line[1]
            if len(self.mapping) == 0:
                self.valid = False
                return

if __name__ == "__main__":
    testLayout = Layout("./tests/files/experiment/layout1.csv")
    print(testLayout.layout_id)
    print(testLayout.mapping)