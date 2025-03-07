from bit_IO.bit_IO import Bit_IO # pip install --ignore-installed "bit_IO @ git+https://github.com/vicente-gonzalez-ruiz/bit_IO"

class Arithmetic_Coding():
    
    # 1/(2^ACCURACY) is the size of the smallest interval to represent.
    ACCURACY = 16
    
    # 0.99..., 0.25. 0.50 and 0.75.
    _0_99 = (1<<ACCURACY) - 1
    _0_25 = _0_99//4 + 1
    _0_50 = _0_25*2
    _0_75 = _0_25*3
    
    def __init__(self):
        self.low = 0
        self.high = Arithmetic_Coding._0_99
        self.bitio = Bit_IO()
        
    def find_interval(self, _range, index, PDF):
        self.high = self.low + (_range*PDF[index - 1])//PDF[0] - 1
        self.low  = self.low + (_range*PDF[index    ])//PDF[0]

    def scale_interval(self):
        self.low = 2*self.low
        self.high = 2*self.high + 1

class Arithmetic_Encoding(Arithmetic_Coding):
    
    def __init__(self):
        super().__init__()
        self.bits_to_follow = 0
        
    def bit_plus_follow(self, bit, file):
        self.bitio.write(bit, file)
        while self.bits_to_follow > 0:
            self.bitio.write(~bit, file)
            self.bits_to_follow -= 1
            
    def encode_index(self, index, PDF, file):
        _range = self.high - self.low + 1
        self.find_interval(_range, index, PDF)
        
        # Incremental transmission
        while True:
            if self.high < Arithmetic_Coding._0_50:
                # The MSb of low and high is 0. Send it.
                self.bit_plus_follow(0, file)
            elif self.low >= Arithmetic_Coding._0_50:
                # The MSb of low and high 1 1. Send it.
                self.bit_plus_follow(1, file)
                # Avoid register overflow.
                self.low -= Arithmetic_Coding._0_50
                self.high -= Arithmetic_Coding._0_50
            elif (self.low >= Arithmetic_Coding._0_25 and self.high < Arithmetic_Coding._0_75):
                # low=01... and high=10...
                self.bits_to_follow += 1
                # Avoid register overflow.
                self.low -= Arithmetic_Coding._0_25
                self.high -= Arithmetic_Coding._0_25   
            else:
                break
            
            self.scale_interval()
            
    def flush(self, file):
        self.bits_to_follow += 1
        if self.low < Arithmetic_Coding._0_25:
            self.bit_plus_follow(0, file)
        else:
            self.bit_plus_follow(1, file)
        for i in range(Arithmetic_Coding.ACCURACY):
            self.bit_plus_follow(0, file)
        self.bitio.flush(file)
        
    def encode_symbol(self, symbol, PDF, file):
        index = symbol + 1
        self.encode_index(index, PDF, file)

class Arithmetic_Decoding(Arithmetic_Coding):
    
    def __init__(self):
        super().__init__()
        
    def init(self, file):
        self.value = 0
        for i in range(Arithmetic_Coding.ACCURACY):
            self.value = 2*self.value
            if self.bitio.read(file):
                self.value += 1
        self.low = 0
        self.high = Arithmetic_Coding._0_99
        return Arithmetic_Coding.ACCURACY
                
    def decode_index(self, PDF, file):
        _range = self.high - self.low + 1
        cummulative_count = ((self.value - self.low + 1)*PDF[0] - 1)//_range
        index = 1
        while PDF[index] > cummulative_count:
            index += 1
            
        # Select the same encoding interval that the encoder.
        self.find_interval(_range, index, PDF)
        
        # Incremental reception.
        while True:
            if self.high < Arithmetic_Coding._0_50:
                pass
            elif self.low >= Arithmetic_Coding._0_50:
                # Expand the high half of the encoding interval and substract 0.5.
                self.value -= Arithmetic_Coding._0_50
                self.low -= Arithmetic_Coding._0_50
                self.high -= Arithmetic_Coding._0_50
            elif (self.low >= Arithmetic_Coding._0_25 and self.high < Arithmetic_Coding._0_75):
                self.value -= Arithmetic_Coding._0_25
                self.low -= Arithmetic_Coding._0_25
                self.high -= Arithmetic_Coding._0_25
            else:
                break
                
            self.scale_interval()
        
            self.value = 2*self.value
            if self.bitio.read(file):
                self.value += 1
        return index
    
    def decode_symbol(self, PDF, file):
        index = self.decode_index(PDF, file)
        return index - 1
