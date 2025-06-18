class BaseStatistics:
    _size = 0
    _avg = 0
    _min = 0
    _max = 0
    _var = 0
    _std = 0                              
    
    def __init__(self, data: list) -> None:
        self._data = list(data)
        self._size = len(self._data)
        self._avg = sum(self._data) / len(self._data)
        self._min = min(self._data)
        self._max = max(self._data)
        # Calculate standard deviation
        self._var = sum((x - self._avg) ** 2 for x in self._data) / len(self._data)
        self._std = self._var ** 0.5

    def __str__(self):
        return f"Size={self._size}, Avg={self._avg}, Min={self._min}, Max={self._max} : {self._data}"

    @property
    def avg(self):
        return self._avg
    @property
    def min(self):
        return self._min
    @property
    def max(self):
        return self._max
    @property
    def std(self):
        return self._std
    @property
    def var(self):
        return self._var
    
