import xml.sax
import re, os, sys, timeit
from collections import defaultdict
from xml.sax import parse, ContentHandler
from nltk.stem.snowball import SnowballStemmer

stop_words = set()
words_in_index = set()
inverted_index = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))

index_path = ""
invertedindex_stat = ""

push_limit = 5000
last_doc_id = 0
file_no = 0

tokens_in_dump = 0
tokens_in_index = 0

#Stemmer object
stemmer = SnowballStemmer("english")

#RegEx to remove URLs, CSS, Punctuations
regExp1 = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.DOTALL)
#RegEx to remove CSS
regExp2 = re.compile(r'{\|(.*?)\|}', re.DOTALL)
#RegEx to remove {{citr **}} or {{vcite **}}
regExp3 = re.compile(r'{{v?cite(.*?)}}', re.DOTALL)
#RegEx to remove Punctuations
regExp4 = re.compile(r'[-.,:;_?()"/\']', re.DOTALL)
#RegEx to remove [[file:]]
regExp5 = re.compile(r'\[\[file:(.*?)\]\]', re.DOTALL)
#RegEx to remove Special Characters
regExp6 = re.compile(r'[~`!@#$%-^*+{\[}\]\|\\<>/?]', re.DOTALL)
#RegEx to remove <..> from text
regExp7 = re.compile(r'<(.*?)>' ,re.DOTALL)

# Function to clean the text
def cleanText(text):
	try:
		text = regExp1.sub('', text)
		text = regExp2.sub('', text)
		text = regExp3.sub('', text)
		text = regExp4.sub('', text)
		text = regExp5.sub('', text)
		text = regExp7.sub('', text)
	except:
		return text
	return text

def dumpInvertedIndex(doc_id, file_no):
	global index_path, inverted_index
	if any(inverted_index) == False:
		print("No Entries to Dump")

	#print(inverted_index)
	fout = open(index_path + str(file_no) + ".txt", "w")
	for key,val in  sorted(inverted_index.items()):
		try:
			if key == None or val == None:
				continue
			s = str(key) + ":"
			if s == ":":
				continue
			for k,v in sorted(val.items()):
				try:
					s = s + str(k) + "-"
					if s == "-":
						continue
					for k1,v1 in v.items():
						try:
							if k1 == None or v1 == None:
								break
							s = s + str(k1) + str(v1) + ","
						except:
							continue
					s = s[:-1] + "|"
				except:
					continue
			if s != "":
				fout.write(s[:-1] + "\n")
		except:
			continue
	fout.close()
	inverted_index.clear()
	print(str(doc_id) + " Documents Processed...")

	
def insertIntoInvertedIndex(final_words, doc_id, ch):
	global inverted_index, tokens_in_dump, tokens_in_index
	for word in final_words:
		try:
			word = word.strip()
			if word.isalpha() and len(word) > 3 and word not in stop_words:
				tokens_in_dump += 1

				word = stemmer.stem(word)
				if word not in stop_words:
					if word not in words_in_index:
						tokens_in_index += 1
						words_in_index.add(word)

					if word in inverted_index.keys():
						if doc_id in  inverted_index[word].keys():
							if ch in inverted_index[word][doc_id].keys():
								inverted_index[word][doc_id][ch] += 1
							else:
								inverted_index[word][doc_id][ch] = 1
						else:
							inverted_index[word][doc_id] = {ch:1}
					else:
						inverted_index[word] = dict({doc_id:{ch:1}})
		except:
			continue

def cleanExtractedDict(extracted_dict, doc_id, field, ch):
	text = ' '.join(extracted_dict[field])
	text = regExp6.sub(' ', text)
	extracted_dict[field] = text.split()
	insertIntoInvertedIndex(extracted_dict[field], doc_id, ch)

def cleanExtractedData(extracted_dict, doc_id):
	for info_list in extracted_dict["InfoBox"]:
		try:
			token_list = []
			token_list = re.findall(r'=(.?)\|', info_list, re.DOTALL)
			token_list = ' '.join(token_list)
			token_list = regExp6.sub(' ', token_list)
			token_list = token_list.split()
			insertIntoInvertedIndex(token_list, doc_id, "i")
		except:
			continue

	if len(extracted_dict["Body"]):
		cleanExtractedDict(extracted_dict, doc_id, "Body", "b")

	if len(extracted_dict["References"]):
		cleanExtractedDict(extracted_dict, doc_id, "References", "r")
	
	if len(extracted_dict["Categories"]):
		cleanExtractedDict(extracted_dict, doc_id, "Categories", "c")
	
	if len(extracted_dict["Links"]):
		cleanExtractedDict(extracted_dict, doc_id, "Links", "e")
	
def processText(doc_data, doc_id):
	text = doc_data.lower()
	text = cleanText(text)

	extracted_dict = {}
	extracted_dict["Body"] = []
	extracted_dict["InfoBox"] = []
	extracted_dict["Categories"] = []
	extracted_dict["References"] = []
	extracted_dict["Links"] = []
	
	lines = text.split("\n")
	index = 0
	length = len(lines)
	while index < length:
		try:
			if lines[index].startswith("{{infobox"):
				while True:
					if (index + 1) >= length or lines[index + 1].endswith("}}"):
						break
					index += 1
					extracted_dict["InfoBox"].append(lines[index])
			elif "[[category" in lines[index]:
				line = lines[index][11 : -2]
				extracted_dict["Categories"].append(line)
			elif lines[index].startswith("="):
				title_text = lines[index].replace("=", "")
				if title_text == "references" or title_text == "see also" or title_text == "further reading" or title_text == "external links":
					while index < length:
						if (index + 1) >= length or lines[index + 1].startswith("="):
							break
						index += 1
						if title_text == "references":
							extracted_dict["References"].append(lines[index])
						elif title_text == "external links" and lines[index].startswith("*"):
							extracted_dict["Links"].append(lines[index])
			else:
				extracted_dict["Body"].append(lines[index])

		except:
			index += 1
			continue
		index += 1

	cleanExtractedData(extracted_dict, doc_id)
	global last_doc_id, file_no
	last_doc_id = doc_id
	if doc_id % push_limit == 0:
		dumpInvertedIndex(doc_id, file_no)
		file_no += 1

def processTitle(doc_data, doc_id):
	text = doc_data.lower()
	text = cleanText(text)
	words = text.split()
	final_words = []
	for word in words:
		try:
			if word.isalpha() and word not in stop_words:
				final_words.append(regExp6.sub(' ', word))
		except:
			continue
	insertIntoInvertedIndex(final_words, doc_id, "t")

class WikiHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.doc_id = 0
		self.doc_data = ""
		self.doc_title = ""
		self.doc_text = ""
		self.is_title = False
		self.is_text = False
		self.is_page = False
		self.is_firstID = False

	def startElement(self, tag, attribute):
		if tag == "title":
			self.doc_data = ""
			self.is_title = True
			self.is_firstID = True

		elif tag == "page":
			self.is_page = True
			self.doc_id = self.doc_id + 1

		elif tag == "text":
			self.doc_data = ""
			self.is_text = True

		elif tag == "id" and self.is_firstID:
			self.doc_data = ""

	def endElement(self, tag):
		if tag == "title":
			processTitle(self.doc_data, self.doc_id)
			self.is_title = True
			self.doc_title = self.doc_data
			self.doc_data = ""

		elif tag == "text":
			processText(self.doc_data, self.doc_id)
			self.is_text = True
			self.buffer = ""

	def characters(self, content):
		self.doc_data = self.doc_data + content

def parseXML(dump_path):
	parser = xml.sax.make_parser()
	handler = WikiHandler()
	parser.setContentHandler(handler)
	parser.parse(dump_path)

def loadStopWords():
	global stop_words
	fin = open("./2019201052/stopWords.txt", "r")
	for line in fin:
		line = line.strip()
		stop_words.add(line)
	fin.close()

def main():
	if len(sys.argv) != 4:
		print("Usage: bash index.sh wiki_dump.xml output_path invertedindex_stat.txt")
		sys.exit(0);

	global index_path, doc_id_to_data, invertedindex_stat
	
	dump_path = sys.argv[1]
	index_path = sys.argv[2]
	invertedindex_stat = sys.argv[3]

	if not os.path.exists(index_path):
		os.makedirs(index_path)

	if index_path[-1:] != '/':
		index_path += '/'

	print("Parsing Started...")
	parseXML(dump_path)
	dumpInvertedIndex(last_doc_id, file_no)

	fout = open(invertedindex_stat, "w")
	fout.write(str(tokens_in_dump) + "\n")
	fout.write(str(tokens_in_index) + "\n")
	fout.close()


if __name__ == "__main__":
	start = timeit.default_timer()
	main()
	stop = timeit.default_timer()
	print(stop - start, "Seconds")
	print((stop - start) / 60.0, "Minutes")
	