import re, os, sys
import xml.sax
from xml.sax import parse, ContentHandler
import spacy
import timeit
import xml.sax
#from nltk.stem.snowball import SnowballStemmer
from collections import defaultdict

#stemmer = SnowballStemmer("english")

stop_words = set()
inverted_index = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))

index_path = ""
invertedindex_stat = ""

doc_id_to_data = None
push_limit = 4000
last_doc_id = 0

#RegEx to remove URLs
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
regExp6 = re.compile(r'[\'~` \n\"_!=@#$%-^*+{\[}\]\|\\<>/?]', re.DOTALL)

#RegEx to remove {{.*}} from text
regExp9 = re.compile(r'{{(.*?)}}', re.DOTALL)
#RegEx to remove <..> from text
regExp10 = re.compile(r'<(.*?)>' ,re.DOTALL)
#RegEx to remove junk from text
regExp11 = re.compile(r"[~`!@#$%-^*+{\[}\]\|\\<>/?]", re.DOTALL)

# Function t0 clean the text
def cleanText(text):
	try:
		text = regExp1.sub('', text)
		text = regExp2.sub('', text)
		text = regExp3.sub('', text)
		text = regExp4.sub('', text)
		text = regExp5.sub('', text)
		text = regExp10.sub('', text)
	except:
		return text
	return text

def docMappingDump(doc_id, doc_title, doc_data):
	doc_id = str(doc_id)
	doc_title = str(doc_title.encode('utf-8'))
	#print(doc_id, doc_title)
	try:
		if doc_id_to_data is not None:
			doc_id_to_data.write(doc_id + "#" + doc_title + "\n")
		else:
			print("Found None")
	except:
		print("Some Error Occured")

def dumpInvertedIndex(doc_id):
	global index_path, inverted_index
	if any(inverted_index) == False:
		print("No Entries to Dump")

	#print(inverted_index)
	fout = open(index_path + str(doc_id) + ".txt", "w")
	for key,val in  sorted(inverted_index.items()):
		try:
			if key == None or val == None:
				continue
			s = str(key.encode('utf-8')) + ":"
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

	
def insertIntoInvertedIndex(final_words, doc_id, t):
	global inverted_index
	for word in final_words:
		try:
			word = word.strip()
			if word.isalpha() and len(word) > 3 and word not in stop_words:
				if word not in stop_words:
					if word in inverted_index:
						if doc_id in  inverted_index[word]:
							if t in inverted_index[word][doc_id]:
								inverted_index[word][doc_id][t] += 1
							else:
								inverted_index[word][doc_id][t] = 1
						else:
							inverted_index[word][doc_id] = {t:1}
					else:
						inverted_index[word] = dict({doc_id : {t:1}})
		except:
			continue

def cleanExtractedData(extracted_dict, doc_id):
	for info_list in extracted_dict["InfoBox"]:
		try:
			token_list = []
			token_list = re.findall(r'=(.?)\|', info_list, re.DOTALL)
			token_list = ' '.join(token_list)
			token_list = regExp11.sub(' ', token_list)
			token_list = token_list.split()
			insertIntoInvertedIndex(token_list, doc_id, "i")
		except:
			continue

	if len(extracted_dict["Categories"]):
		categories = ' '.join(extracted_dict["Categories"])
		categories = regExp11.sub(' ', categories)
		extracted_dict["Categories"] = categories.split()
		insertIntoInvertedIndex(extracted_dict["Categories"], doc_id, "c")

	if len(extracted_dict["Body"]):
		body = ' '.join(extracted_dict["Body"])
		body = regExp11.sub(' ', body)
		extracted_dict["Body"] = body.split()
		insertIntoInvertedIndex(extracted_dict["Body"], doc_id, "b")
	
	if len(extracted_dict["References"]):
		references = ' '.join(extracted_dict["References"])
		references = regExp11.sub(' ', references)
		extracted_dict["References"] = references.split()
		insertIntoInvertedIndex(extracted_dict["References"], doc_id, "r")
	
	if len(extracted_dict["Links"]):
		links = ' '.join(extracted_dict["Links"])
		links = regExp11.sub(' ', links)
		extracted_dict["Links"] = links.split()
		insertIntoInvertedIndex(extracted_dict["Links"], doc_id, "e")
		

def processBuffer(doc_data, doc_id, is_title, is_text):
	text = doc_data.lower()
	text = cleanText(text)

	if is_title:
		words = text.split()
		final_words = []
		for word in words:
			try:
				if word.isalpha() and word not in stop_words:
					final_words.append(regExp11.sub(' ', word))
			except:
				continue
		insertIntoInvertedIndex(final_words, doc_id, "t")

	elif is_text:
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
				continue
			index += 1

		cleanExtractedData(extracted_dict, doc_id)
		global last_doc_id
		last_doc_id = doc_id
		if doc_id % push_limit == 0:
			dumpInvertedIndex(doc_id)
		#if doc_id == 2:	
		#	sys.exit(0)

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
			processBuffer(self.doc_data, self.doc_id, True, False)
			self.is_title = True
			self.doc_title = self.doc_data
			self.doc_data = ""

		elif tag == "text":
			processBuffer(self.doc_data, self.doc_id, False, True)
			self.is_text = True
			self.buffer = ""

		elif tag == "id" and self.is_firstID:
			docMappingDump(self.doc_id, self.doc_title, self.doc_data)
			self.is_firstID = False
			self.doc_data = ""

	def characters(self, content):
		self.doc_data = self.doc_data + content

def parseXML(dump_path):
	parser = xml.sax.make_parser()
	#parser.setFeature(xml.sax.handler.feature_namespaces, 0)
	handler = WikiHandler()
	parser.setContentHandler(handler)
	parser.parse(dump_path)

def main():
	if len(sys.argv) != 4:
		print("Usage: python3 indexer.py sample.xml output_path invertedindex_stat.txt")
		sys.exit(0);

	global index_path, stop_words, doc_id_to_data, invertedindex_stat
	
	fin = open("stopWords.txt", "r")
	for line in fin:
		line = line.strip()
		stop_words.add(line)
	
	dump_path = sys.argv[1]
	index_path = sys.argv[2]
	invertedindex_stat = sys.argv[3]

	if not os.path.exists(index_path):
		os.makedirs(index_path)

	if index_path[-1:] != '/':
		index_path += '/'

	doc_id_to_data = open(index_path + "docTitleMap.txt", "w")
	
	print("Parsing Started...")
	parseXML(dump_path)


	dumpInvertedIndex(last_doc_id)


if __name__ == "__main__":
	start = timeit.default_timer()
	main()
	stop = timeit.default_timer()
	print(stop - start)