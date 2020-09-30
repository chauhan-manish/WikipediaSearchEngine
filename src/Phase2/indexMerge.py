import os,sys
import timeit
import glob
from collections import defaultdict
from heapq import heapify, heappush, heappop

final_index_path = "/content/drive/My Drive/FinalIndex/"
index_file_count = 0
chunk_size = 500000

total = 0
inverted_index = {}
secondary_index = dict()

index_files = glob.glob("/content/drive/My Drive/inverted_index/*")
files_completed = []
file_pointers = []
curr_row_file = []
percolator = []
words = {}

def writeToPrimary():
	offset = []
	firstWord = True
	global index_file_count
	index_file_count += 1
	fileName = final_index_path + "index" + str(index_file_count) + ".txt"
	fp = open(fileName,"w")
	for i in sorted(inverted_index):
		if firstWord:
			secondary_index[i] = index_file_count
			firstWord = False
		toWrite = str(i) + ":" + inverted_index[i] + "\n"
		fp.write(toWrite)

def writeToSecondary():
	fileName = final_index_path + "secondary_index.txt"
	fp = open(fileName,"w")
	for i in sorted(secondary_index):
		toWrite = str(i) + " " + str(secondary_index[i]) + "\n"
		fp.write(toWrite)

def main():
	file_count = 0
	for i in range(len(index_files)):
		files_completed.append(1)
		fp = open(index_files[i],"r")
		file_pointers.append(fp)
		file_count += 1
		curr_row_file.append( file_pointers[i].readline())
		words[i] = curr_row_file[i].split(':')
		#print words[i]
		if words[i][0] not in percolator:
			heappush(percolator,words[i][0])

	while True:
		if files_completed.count(0) == len(index_files):
			#print(files_completed)
			break
		else:
			total += 1
			word = heappop(percolator)
			for i in range(len(index_files)):
				if files_completed[i] and words[i][0] == word:
					if word in inverted_index:
						inverted_index[word] += "|" + words[i][1]
					else:
						inverted_index[word] = words[i][1]

					if total == chunk_size:
						total = 0
						writeToPrimary()
						inverted_index.clear()

					curr_row_file[i] = file_pointers[i].readline().strip()

					if curr_row_file[i]:
						words[i] = curr_row_file[i].split(':')
						if words[i][0] not in percolator:
							heappush(percolator,words[i][0])
					else:
						files_completed[i] = 0
						file_pointers[i].close()

	writeToPrimary()
	writeToSecondary()

if __name__ == "__main__":
	start = timeit.default_timer()
	main()
	stop = timeit.default_timer()
	print(stop - start, "Seconds")
	print((stop - start) / 60.0, "Minutes")