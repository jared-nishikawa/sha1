#!/usr/bin/python

import sys

BITSPERCHAR = 8

# 32-bit NOT
def not32(x):
	return x ^ (2**32-1)

# XOR
def xor(*args):
	L = len(args[0])
	for word in args:
		assert len(word) == L
	ret = ''
	for i in range(L):
		newchar = 0
		for word in args:
			newchar ^= ord( word[i] )
		ret += chr( newchar )
	return ret

# String (each char is a byte, big-endian) to int
def strtoint(word):
	word = word[::-1] # Reverse it, so there
	total = 0
	for index,char in enumerate(word):
		total += 256 ** index * ord(char)
	return total

# Int to string (each char is a byte, big-endian)
# String is of length L bytes
def inttostr(N, L):
	N = N % (2 ** (BITSPERCHAR*L) )
	ret = ''
	while N > 0:
		ret += chr( N % 256)
		N /= 256
	while len(ret) < L:
		ret += '\x00'
	return ret[::-1]

# Rotate left by n bits
# 'word' is an array of bytes
def lrot(word, n):
	# B has '0b' on the front... get rid of it
	B = bin( strtoint(word))[2:]
	# pad...
	while len(B) < BITSPERCHAR*len(word):
		B = '0' + B
	# Now shift left
	newB = B[n:] + B[:n]
	newint = int(newB, 2)
	# Assumedly, returning a word of the same length
	return inttostr(newint, len(word) )

# Rotate left by n bits...
# num is an integer
# length in bytes...?
def introt(num, n, length):
	_num = inttostr(num, length)
	_num = lrot(_num, n)
	return strtoint(_num)
	
if __name__ == "__main__":

	# Usage
	if len( sys.argv ) < 2:
		print "Usage: %s <message>" % sys.argv[0]
		sys.exit(1)

	# Initialize variables
	msg = sys.argv[1]

	# 32 bit constants
	h0 = 0x67452301
	h1 = 0xEFCDAB89
	h2 = 0x98BADCFE
	h3 = 0x10325476
	h4 = 0xC3D2E1F0
	
	# Note: mlen is a multiple of 8
	mlen = len(msg) * BITSPERCHAR

	# Pre-processing
	# Note: 448 is a multiple of 8
	offset = (448 - mlen % 512) % 512

	# Therefore, offset is a multiple of 8
	c_offset = offset/BITSPERCHAR
	
	suffix = '\x80' + '\x00' * (c_offset - 1)
	msg += suffix
	
	# Message length, as a 64 bit integer (8 bytes)
	mlenx = inttostr(mlen, 8)
	msg += mlenx

	# Length should be 0 mod 64
	assert len(msg) % 64 == 0

	# Note: 64 * 8 = 512
	
	# Process the message in successive 512-bit chunks (i.e. 64 byte chunks)
	chunks = [ msg[64*i:64*(i+1)] for i in range( len(msg) / 64)]
	
	for chunk in chunks:
		# Break chunk into sixteen 32-bit (4-byte) big-endian words
		w = [ chunk[4*i:4*(i+1)] for i in range(16)]
		
		# Extend the sixteen 32-bit words into eight 32-bit words
		for i in range(16,80):
			X = xor( w[i-3], w[i-8], w[i-14], w[i-16])
			w.append( lrot(X,1))
		
		# Initialize hash value for this chunk
		a = h0
		b = h1
		c = h2
		d = h3
		e = h4

		# Main loop
		for i in range(80):
			if i < 20:
				f = (b & c) | ( not32(b) & d)
				k = 0x5A827999	
			elif i < 40:
				f = b ^ c ^ d
				k = 0x6ED9EBA1
			elif i < 60:
				f = (b & c) | (b & d) | (c & d)
				k = 0x8F1BBCDC
			else:
				f = b ^ c ^ d
				k = 0xCA62C1D6
			#_a = inttostr(a, 32)
			#_a = lrot(_a, 5)
			#_a = strtoint(_a)
			# leftrotate a by 5, a is 32 bits (aka 4 bytes)
			_a = introt(a, 5, 4)
			temp = _a + f + e + k + strtoint(w[i])
			e = d
			d = c
			#_b = inttostr(b,32)
			#_b = lrot(_b, 30)
			#_b = strtoint(_b)
			_b = introt(b, 30, 4)
			c = _b
			b = a
			a = temp
		# Add this chunk's hash to result so far
		h0 = (h0 + a) % (2**32)
		h1 = (h1 + b) % (2**32)
		h2 = (h2 + c) % (2**32)
		h3 = (h3 + d) % (2**32)
		h4 = (h4 + e) % (2**32)

	# Produce the final hash value (big-endian) as a 160 bt number:
	hh = h0 * (2**128) + h1 * (2**96) + h2 * (2**64) + h3 * (2**32) + h4
	print hex(hh)[2:].strip('L')
