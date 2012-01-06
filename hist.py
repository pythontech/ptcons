class History:
    def __init__(self, bufsize=1024):
	self.bufsize = bufsize
	self.bufs = []
	self.size = 0

    def add(self, data):
	pos = 0
	while pos < len(data):
	    psize = self.bufsize - (self.size % self.bufsize)
	    part = data[pos:][:psize]
	    if psize == self.bufsize:
		self.bufs.append(part)
	    else:
		self.bufs[-1] += part
	    self.size += len(part)
	    pos += len(part)

    def fetch(self, pos0, pos1):
	'''Get a list of strings comprising positions pos0:pos1'''
	if pos0 < 0 or pos1 > self.size:
	    raise ValueError, "Bad range"
	b0, c0 = divmod(pos0, self.bufsize)
	b1, c1 = divmod(pos1, self.bufsize)
	if pos0 == pos1:
	    return []
	elif b0 == b1:
	    return [self.bufs[b0][c0:c1]]
	else:
	    return [self.bufs[b0][c0:]] + \
		   self.bufs[b0+1:b1] + \
		   [self.bufs[b1][:c1]]

    def __len__(self):
	return self.size

    def __getslice__(self, beg, end):
	if beg < 0:
	    beg += self.size
	if end < 0:
	    end += self.size
	beg = min(max(0, beg), self.size)
	end = min(max(beg, end), self.size)
	return ''.join(self.fetch(beg,end))
