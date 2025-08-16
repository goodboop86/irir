class Utils:

    @staticmethod
    def broad_enable(target):
        true_values = {"true", "True", "on", "yes", True, 1}
        return target in true_values
