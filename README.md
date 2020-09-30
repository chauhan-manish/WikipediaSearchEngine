# WikipediaSearchEngine
# Prerequisites

    Python3
    Porter stemmer
    stop words list

# About Project

# Built Search Engine Platform by creating Inverted Index on the Wikipedia Data Dump of size 45 GB.

# Following Steps Follows to create Inverted Indexing

    Parsing using etree : Need to parse each page , title tag, infobox, body , category etc..
    Tokenization : Tokenize sentense to get each token using regular expression
    Case Folding : make it all to lowercase
    Stop Words Removal : remove stop word which are more frequently occured in a sentences
    Stemming : get root/base word and store it
    Inverted Index Creation : create word & its positing list consist of doc_id : TF-IDf score


# Features

    support field query like title:abc body:aaa infobox:zyx
    showing only top k relevent search result
    Response time is nearly 3-4 second

# Challenges

    Difficult to process such huge Data dump of 45 GB
    Can not store word & its posting list into a main memory, So Used K-way Merge sort
    Can not Load full final index into main memory, So Bild Secondary Index on top of Primary Index (Posting List)

# To Create indexing from Wiki Dump

python3 indexer.py <wiki_dump_path> <index_path>

# To Search Query

python3 search.py <index_path> queries.txt
