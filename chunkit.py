#
# Process NASA / JPL PDS '.IMG' files
# from HiRISE camera on Mars Reconaissance Orbiter
# for their Digital Terrain Models DTEEC files
#
# see also
# http://www.uahirise.org/dtm/
# https://pds.jpl.nasa.gov/documents/sr/AppendixC.pdf
# https://github.com/RyanBalfanz/PyPDS
# http://en.wikipedia.org/wiki/Single-precision_floating-point_format
# http://docs.scipy.org/doc/numpy/reference/generated/numpy.frombuffer.html
# https://trac.osgeo.org/gdal/ticket/3939
# https://geoweb.rsl.wustl.edu/community/index.php?/topic/81-opening-img-binary-files/
# http://answers.unity3d.com/questions/7652/issue-with-importing-raw-heightmaps-made-in-photos.html

from pprint import pprint
from pds.core.common import open_pds
from pds.core.parser import Parser
from fractions import Fraction
import sys,string,binascii
from PIL import Image

import numpy as np

debugon = False

def debug(*args):
	global debugon
	if debugon: print args
	sys.stdout.flush()

def verify_label(l):
	status = ''
	if l.has_key('IMAGE'):
		if not l['IMAGE'].has_key('LINES'):
			status += '\nno LINES subkey under IMAGE key'
		if not l['IMAGE'].has_key('LINE_SAMPLES'):
			status += '\nno LINE_SAMPLES subkey under IMAGE key'
	else:
		status = '\nno IMAGE key in label'

	if status != '': return status

	if not l.has_key('RECORD_BYTES'):
		status += '\nno RECORD_BYTES key in label'
	if not l['IMAGE'].has_key('SAMPLE_BITS'):
		status += '\nno SAMPLE_BITS key in label'
	elif int(l['IMAGE']['SAMPLE_BITS']!='32'):
		status += '\nonly know how to deal with 32-bit samples'
		# 32 bits, 8 bit bytes, 4 bytes per sample (4 bytes per pixel)

	if status != '': return status

	if int(l['RECORD_BYTES']) != 4 * int(l['IMAGE']['LINE_SAMPLES']):
		status += '\nRECORD_BYTES should be 4 times LINE_SAMPLES'
	
	if not l['IMAGE'].has_key('SAMPLE_TYPE'):
		status += '\nno SAMPLE_TYPE label'
	if not l['IMAGE'].has_key('SCALING_FACTOR'):
		status += '\nscaling factor not found'
	if not l['IMAGE'].has_key('OFFSET'):
		status += '\nOFFSET not found under IMAGE label'

	if l.has_key('RECORD_TYPE'):
		if not l['RECORD_TYPE'] == 'FIXED_LENGTH':
			status += '\nRECORD_TYPE should be FIXED_LENGTH'
	else:
		status += '\nno RECORD_TYPE key in label'

	if status=='': status = 'ok'

	return status

def print_info(l):
	debug('count of image lines:',l['IMAGE']['LINES'])
	debug('bits per pixel',l['IMAGE']['SAMPLE_BITS'])
	debug('pixels per line:',l['IMAGE']['LINE_SAMPLES'])
	debug('byte count per line',l['RECORD_BYTES'])


# process number types.
#
# see https://pds.jpl.nasa.gov/documents/sr/AppendixC.pdf
#
# scientific notation; 
# value = 1.mantissa * 2 to the power of ( exponent - bias )
#
# Very Slow. Much room for optimization.

def PC_REAL_32_to_pyfloat(sample):
	#debug(np.frombuffer(sample,dtype=np.float32))
	return np.frombuffer(sample,dtype=np.float32)

	b0 = sample[0]
	b1 = sample[1]
	b2 = sample[2]
	b3 = sample[3]
	#debug( bin(b0), bin(b1), bin(b2), bin(b3) )
	#debug( hex(b0), hex(b1), hex(b2), hex(b3) )
	#debug( b0, b1, b2, b3 )
	exponent_bias = 127
	# bit order: bit 7, bit 6, bit 5, ... bit 0
	m2 =    b0
	m1 =    b1
	m0 =    b2 & 0b01111111
	e0 =    (b2 & 0b10000000) >> 7
	msign = (b3 & 0b10000000) >> 7
	e1 =    (b3 & 0b01111111) << 1
	m = (m0 / 2.0**7) + (m1 / 2.0**15) + (m2 / 2.0**23)
	mantissa =  (-1 ** msign) * (1+m)
	exponent = e0 | e1
	#debug('e0 ',bin(e0), 'e1',bin(e1))
	#debug('msign',msign,'m',m)
	#debug('mantissa',mantissa,float(mantissa))
	#debug('exponent',bin(exponent),exponent, '-bias',exponent-exponent_bias)
	v = mantissa * ( 2 ** ( exponent - exponent_bias ) )
	debug(float(v))
	return float(v)

def maketile(f,samplesperline,xcursor,ycursor,tilew,tileh):
	f.seek(0)
	f.seek(xcursor+ycursor*samplesperline)
	fdata = f.read(tilew*4)
	imgs += [Image.frombuffer(mode='F',size=(tilew,1),data=fdata)]
	img = Image.new(size=(tilew,tileh))
	counter = 0 
	for i in imgs:
		img.paste((i,counter))
		counter+=1
	return img

def process_samples(filename,label):
	recordsize = int(label['RECORD_BYTES'])
	numlines = int(label['IMAGE']['LINES'])
	samplesperline = int(label['IMAGE']['LINE_SAMPLES'])
	bytes_per_sample = int(label['IMAGE']['SAMPLE_BITS'])/8
	numtype = label['IMAGE']['SAMPLE_TYPE']
	missingconst = 0
	s = ''
	minval = float(label['IMAGE']['VALID_MINIMUM'])
	maxval = float(label['IMAGE']['VALID_MAXIMUM'])
	if label['IMAGE'].has_key('MISSING_CONSTANT'):
		s = ''
		s += label['IMAGE']['MISSING_CONSTANT'][9:11]
		s += label['IMAGE']['MISSING_CONSTANT'][7:9]
		s += label['IMAGE']['MISSING_CONSTANT'][5:7]
		s += label['IMAGE']['MISSING_CONSTANT'][3:5]
		missingconst = bytearray( s.decode('hex') )
	debug('missing constant:',missingconst,s)
	# PDS files often have an ASCII label at the beginning of binary data
	# We need to read as binary here. 
	f = open(filename,'rb')

	# read past the first record, which is assumed to be the ASCII label.
	f.read(recordsize)

	# skip black lines for debugging
	# for i in range(0,1000): f.read(recordsize)

	#for line in range(0,numlines):
	tmp = samplesperline / 1024
	tilew =  tmp * 1024 + (samplesperline % 1024)/tmp
	tmp = numlines / 1024
	tileh =  tmp * 1024 + (numlines % 1024)/tmp
	print 'w:',samplesperline,'tilew:',tilew
	print 'h:',numlines,'tileh:',tileh
	xcursor = 0
	ycursor = 0
	for ycursor in range(0,numlines,tileh):
		img = maketile(f,xcursor,ycursor,tilew,tileh)

	for line in range(0,10): #numlines):
		print line+1, '/', numlines
		fdata = f.read(recordsize)
		record = bytearray(fdata)
		values = np.frombuffer(record,dtype=np.float32)
		img = Image.frombuffer(mode='F',size=(recordsize/4,1),data=fdata)
		print img.format
		print img.mode
		print img.size
		print img.info
		print len(values)
		for i in range(0,len(record),bytes_per_sample):
			break
			#if (i%recordsize/80==0): debug('.',
			sample = bytearray(record[i:i+bytes_per_sample])
			#pprint(sample)
			if numtype=='PC_REAL' and len(sample)==4:
				#value = PC_REAL_32_to_pyfloat(sample)
				value = np.frombuffer(sample,dtype=np.float32)
			else:
				pass
				#debug('unknown number type')
			if sample == missingconst:
				#print '.',
				pass
			else:
				pass
				#if value>minval and value<maxval: debug( 'ok' )
				#else: debug( 'out of range' )
				#print value ,
			#debug( value )


p = Parser()

filename = '/tmp/x.img'
file = open_pds(filename)
label = p.parse( file )

if '--label' in string.join(sys.argv):
	pprint(label)
	sys.exit(0)

if '--debug' in string.join(sys.argv): debugon=True

status = verify_label(label)
if status!='ok':
	debug('error:',status)
else:
	debug('label verified')
	print_info(label)

process_samples( filename, label )

