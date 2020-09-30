import re, os, sys
import timeit
from math import log10
from bisect import bisect
from operator import itemgetter
from collections import defaultdict
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer('english')
stop_words = set()
document_title = {}
total_doc = 0
fout = open("queries_op.txt", "w")
secondary_index = []
index_path = ""

def getFinalResult(landf_dict, count_res):
	count = 0
	flag = False
	for k, v in sorted(landf_dict.items(), reverse = True):
		for k1, v1 in sorted(v.items(), key = itemgetter(1), reverse = True):
			count += 1
			#print(k1, " - ", document_title[k1])
			fout.write(str(k1) + ", " + str(document_title[k1]) + "\n")
			if count == count_res:
				break
		if count == count_res:
			break
	
def stemmedQuery(query):
	search_words = []
	tokens = query.split(' ')
	for word in tokens:
		try:
			word = word.lower()
			word = word.strip()
			if word not in stop_words:
				word = stemmer.stem(word)
			if word.isalpha() and  len(word) > 3 and word not in stop_words:
				search_words.append(word)
		except:
			continue
	return search_words

def searchNormalQuery(count_res, query):
	search_words = stemmedQuery(query)
	
	global_dict = dict(list())
	for word in search_words:
		file_no = bisect(secondary_index, word)
		if file_no < 0:
			continue
		primary_file_name = index_path + "index" + str(file_no) + ".txt"
		primary_file = open(primary_file_name, "r")

		posting_found = False
		for line in primary_file.readlines():
			tokens = line.split(":")
			if word == tokens[0]:
				posting_list = tokens[1].split("|")
				posting_found = True
				break
		if posting_found:
			num_doc = len(posting_list)
		try:
			idf = log10(total_doc / num_doc)
			for i in posting_list:
				doc_id, entry = i.split("-")
				if doc_id not in global_dict:
					global_dict[doc_id] = [entry + "_" + str(idf)]
				else:
					global_dict[doc_id].append(entry + "_" + str(idf))
		except:
			continue
	landf_dict = dict(dict())
	dict_count = 0
	regEx = re.compile(r'(\d+|\s+)')
	for k in global_dict:
		try:
			weighted_freq = 0
			n = len(global_dict[k])
			dict_count += 1
			for x in global_dict[k]:
				x, idf = x.split("_")
				x = x.split(",")
				try:
					for y in x:
						try:
							lis = regEx.split(y)
							tag_type, frequency = lis[0], lis[1]
							if tag_type == "b":
								weighted_freq += int(frequency) * 1
							elif tag_type == "i":
								weighted_freq += int(frequency) * 50
							elif tag_type == "c":
								weighted_freq += int(frequency) * 50
							elif tag_type == "e":
								weighted_freq += int(frequency) * 50
							elif tag_type == "r":
								weighted_freq += int(frequency) * 50
							elif tag_type == "t":
								weighted_freq += int(frequency) * 1000
						except:
							continue
				except:
					continue

		except:
			continue
		if n not in landf_dict:
			landf_dict[n] = {k : float(log10(1 + weighted_freq)) * float(idf)}
		else:
			landf_dict[n][k] = float(log10(1 + weighted_freq)) * float(idf)	

	getFinalResult(landf_dict, count_res)

def getExtractedQuery(query, index_list, field_dict, i, tag):
	required_text = query[index_list[i] + 2 : index_list[i + 1]]
	exracted_query = stemmedQuery(required_text)
	field_dict[tag] = exracted_query

def getFieldDict(query):
	field_dict = dict()
	exracted_query = []
	index_list = []
	index_to_type = {}
	
	index_title = query.find('t:')
	index_to_type[index_title] = 't'
	if index_title != -1:
		index_list.append(index_title)

	index_body = query.find('b:')
	index_to_type[index_body] = 'b'
	if index_body != -1:
		index_list.append(index_body)

	index_category = query.find('c:')
	index_to_type[index_category] = 'c'
	if index_category != -1:
		index_list.append(index_category)

	index_reference = query.find('r:')
	index_to_type[index_reference] = 'r'
	if index_reference != -1:
		index_list.append(index_reference)

	index_infobox = query.find('i:')
	index_to_type[index_infobox] = 'i'
	if index_infobox != -1:
		index_list.append(index_infobox)

	index_external_link = query.find('e:')
	index_to_type[index_external_link] = 'e'
	if index_external_link != -1:
		index_list.append(index_external_link)

	index_list.append(len(query))
	index_list.sort()

	length = len(index_list)
	for i in range(0, length - 1):
		if index_to_type[index_list[i]] == 't':
			getExtractedQuery(query, index_list, field_dict, i, "t")

		if index_to_type[index_list[i]] == 'i':
			getExtractedQuery(query, index_list, field_dict, i, "i")

		if index_to_type[index_list[i]] == 'c':
			getExtractedQuery(query, index_list, field_dict, i, "c")

		if index_to_type[index_list[i]] == 'r':
			getExtractedQuery(query, index_list, field_dict, i, "r")

		if index_to_type[index_list[i]] == 'e':
			getExtractedQuery(query, index_list, field_dict, i, "e")

		if index_to_type[index_list[i]] == 'b':
			getExtractedQuery(query, index_list, field_dict, i, "b")

	return field_dict

def searchFieldQuery(count_res, query):
	query = query.lower()
	field_dict = getFieldDict(query)
	docs = {}
	global_dict = dict(list())
	for key in field_dict.keys():
		stemmed_words = field_dict[key]
		for word in stemmed_words:
			try:
				file_no = bisect(secondary_index, word)
				if file_no < 0:
					continue
				primary_file_name = index_path + "index" + str(file_no) + ".txt"
				primary_file = open(primary_file_name, "r")

				posting_found = False
				for line in primary_file.readlines():
					tokens = line.split(":")
					if word == tokens[0]:
						posting_list = tokens[1].split("|")
						posting_found = True
						break

				if posting_found:
					num_doc = len(posting_list)
				try:
					idf = log10(total_doc / num_doc)
					for i in posting_list:
						doc_id, entry = i.split("-")
						if key not in entry:
							continue
						if doc_id not in global_dict:
							global_dict[doc_id] = [entry + "_" + str(idf) + "_" + str(key)]
						else:
							global_dict[doc_id].append(entry + "_" + str(idf) + "_" + str(key))
				except:
					continue
			except:
				continue
	
	landf_dict = dict(dict())
	dict_count = 0
	regEx = re.compile(r'(\d+|\s+)')
	for k in global_dict:
		try:
			weighted_freq = 0
			n = len(global_dict[k])
			dict_count += 1
			for x in global_dict[k]:
				x, idf, key = x.split("_")
				x = x.split(",")
				try:
					for y in x:
						try:
							lis = regEx.split(y)
							tag_type, frequency = lis[0], lis[1]
							if tag_type == "i" and key == "i":
								weighted_freq += int(frequency) * 50
							elif tag_type == "r" and key == "r":
								weighted_freq += int(frequency) * 50
							elif tag_type == "c" and key == "c":
								weighted_freq += int(frequency) * 50
							elif tag_type == "e" and key == "e":
								weighted_freq += int(frequency) * 50
							elif tag_type == "b" and key == "b":
								weighted_freq += int(frequency) * 1
							elif tag_type == "t" and key == "t":
								weighted_freq += int(frequency) * 1000
						except:
							continue
				except:
					continue

		except:
			continue
		if n not in landf_dict:
			landf_dict[n] = {k : float(log10(1 + weighted_freq)) * float(idf)}
		else:
			landf_dict[n][k] = float(log10(1 + weighted_freq)) * float(idf)	

	getFinalResult(landf_dict, count_res)

def searchQuery(k, query):
	if query.find(":") == -1:
		searchNormalQuery(k, query)
	else:
		searchFieldQuery(k, query)

def loadStopWords():
	global stop_words
	try:
		fin = open("stopWords.txt", "r")
		for line in fin:
			line = line.strip()
			stop_words.add(line)
		fin.close()
	except:
		print("Error in Stop Words File")

def loadSecondaryIndex():
	global secondary_index
	try:
		fin = open(index_path + "secondaryIndex.txt", "r")
		for line in fin:
			line = line.strip()
			secondary_index.append(line.split(' ')[0])
		fin.close()
	except:
		print("Error in Secondary Index File")

def loadDocumentID():
	global document_title, total_doc
	try:
		fin = open(index_path + "docTitleMap.txt", "r")
		for line in fin:
			line = line.strip()
			doc_id, doc_title = line.split("#")
			total_doc += 1
			document_title[doc_id] = doc_title
		fin.close()
	except:
		print("Error in Document Title File")

def initialize():
	loadStopWords()
	loadSecondaryIndex()
	loadDocumentID()
	
def main():
	if len(sys.argv) != 2:
		print("Usage: python3 search.py queris.txt")
		sys.exit(0)

	global index_path
	index_path = "FinalIndex/"

	if index_path[-1:] != '/':
		index_path += '/'

	initialize()
	total_query = 0
	total_time = 0.0
	input_file = sys.argv[1]
	fin = open(input_file, "r")
	for line in fin.readlines():
		#query = input("Enter the search query: ")
		#print(line)
		total_query += 1
		line = line.strip()
		k, query = line.split(",")
		query = query.strip()
		start = timeit.default_timer()
		searchQuery(int(k), query)
		end = timeit.default_timer()
		total_time += (end - start)
		#print((end - start), "Seconds")
		#print((end - start) / 60.0, "Minutes")

	avg_time = total_time / total_query
	fout.write(str(total_time) + ", " + str(avg_time))
	fin.close()
	fout.close()

if __name__ == "__main__":
	main()