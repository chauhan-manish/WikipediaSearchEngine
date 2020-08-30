import os, sys

index_path = ""

def findNormalQuery(query):
	query = query.lower()
	#print(query)
	query = query.split(' ')
	result = ""
	for root, directory, files in os.walk(index_path):
		for file in sorted(files):
			#print(file)
			fin = open(index_path + file, "r")
			for line in fin.readlines():
				line = line.rstrip()
				tokens = line.split(":")
				for word in  query:
					if tokens[0] == word:
						result = result + tokens[1] + "|"
	print(result)


def findFieldQuery(query):
	field_list = query.split(' ')
	result = ""
	for root, directory, files in os.walk(index_path):
		for file in sorted(files):
			fin = open(index_path + file, "r")
			for line in fin.readlines():
				line = line.rstrip()
				tokens = line.split(":")
				posting_list = tokens[1].split("|")

				for field in field_list:
					words = field.split(":")
					words[1] = words[1].lower()
					if tokens[0] == words[1]:
						for each_list in posting_list:
							if each_list.find(words[0]) != -1:
								result = result + each_list + "|"
					
	print(result)		


def main():
	global index_path
	index_path = sys.argv[1]
	query = sys.argv[2]
	query = query.strip("\"")
	if index_path[-1:] != '/':
		index_path += '/'

	if query.find(':') == -1:
		findNormalQuery(query)
	else:
		findFieldQuery(query)

if __name__ == "__main__":
	main()