# convert .raw data from heightmap to javascript

import array,sys,struct
fname = 'hm.gray'
if len(sys.argv)>1:
	fname = sys.argv[1]
f = open( fname,'rb')
data = f.read()
f.close()
print '// data from file '+fname
print "var heightdata = '"
for i in range(0,128*128):
	s = struct.unpack('H',data[i:i+2])
	print float(s[0]/65535.0),','


