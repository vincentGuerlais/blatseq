#! /usr/bin/env python

import os
import sys

####################
### Get Help
####################

# print the help and exit the programm

def getHelp() :
	print """blatSeq help
	Usage : python blatSeq.py input_file output_file database_file
	
	if you don't want to do the BLAT, replace the database_file by --noBLAT
	your txt file should be named output_file.txt and be in the same folder though
	"""
	sys.exit()

# Is the first argument a call for help ? or is there the amount of required arguments ?

if len(sys.argv)!=4 :
	getHelp()


####################
### Variables
####################

#input file name
fastaFileName = sys.argv[1]
#output file name
newFastaFileName = sys.argv[2]
#the fileName for the txt (result of the BLAT) file. autogenerated from output file name
txtFileName = sys.argv[2] + ".txt"
#the database filename for the BLAT
dbFileName = sys.argv[3]
#this list is going to be filled with the genes coordinates
geneList = {}
#the gene Id is used to rename the contigs matching the same gene
geneId = 0

#Do the files exist ?
if not os.path.isfile(fastaFileName) :
	print fastaFileName, " can't be found \n"
	getHelp()
if dbFileName != "--noBLAT" :
	if not os.path.isfile(dbFileName) :
		print dbFileName, " can't be found \n"
		getHelp()


####################
### Functions
####################

### BLAT

#using blat via the shell with our parameters

def blat(dbFileName, fastaFileName, txtFileName) :

	os.system("blat " + '-out=blast8 ' + dbFileName + ' ' + fastaFileName + ' ' + txtFileName)
	
### Parsing the txt file

#the output of a BLAT is a txt file. We want to know the scaffold name and the position of
#the first match.
#the results are assembled in a dictionary with the scaffold as primary key.
#


def createGeneList(txtFile) :
		
	#opening the file to read
	readtxt = open(txtFile, 'r')

	#used to know if we're considering only the first hit
	lastQname = ''
	
	#read the txt results line by line
	for line in readtxt :
		line = line.split("\t")
	
		#/!\ loss of time ? /!\
		
		Qname = [line[0]]
		
		#we're using only the first hit (we do not use it if the name is the same
		#as the last one)
		if Qname != lastQname :
			lastQname = Qname[:]
		
			#strand is concatenated to the scaffold to allow only one test
			if line[8] > line[9] :
				scaffold = line[1] + "-"
			else :
				scaffold = line[1] + "+"
			#both are changed to integers to allow mathematical operations
			matchStart = int(line[15])
			matchEnd = int(line[16])

			
			#if scaffold already exists
			if scaffold in geneList :

				geneCount = 0
				lenGenList = len(geneList[scaffold])
				
				while geneCount < lenGenList :
					#overlapping test (True if results[0]<results[1]):
					overlappingTest = [max(geneList[scaffold][geneCount][0], matchStart),
					min(geneList[scaffold][geneCount][1], matchEnd)]
					#if there's an overlapping sequence, updating the gene start/end
					#positions and adding the gene name to the list of genes mapping on
					#this position
					if overlappingTest[0] < overlappingTest[1] :
						matchStart = min(geneList[scaffold][geneCount][0], matchStart)
						matchEnd = max(geneList[scaffold][geneCount][1], matchEnd)
						Qname += geneList[scaffold][geneCount][2]
						del geneList[scaffold][geneCount]
						lenGenList -= 1
						if lenGenList == 0 :
							geneList[scaffold].append([matchStart,matchEnd,Qname])
						else :
							geneCount = 0
				#if there's no overlapping sequence, adding this sequence as a new gene on 
				#this scaffold
					else :
						if geneCount >= len(geneList[scaffold])-1 :
							geneList[scaffold].append([matchStart,matchEnd,Qname])
							lenGenList = 0
						geneCount += 1
			else :
				#if it's a new scaffold
				geneList[scaffold] = [[matchStart,matchEnd,Qname]]
	readtxt.close()
	return geneList
	
def readFasta(fastaFile) :
	fastaContent = {}
	key = ''
	content = ''

	readFa = open(fastaFile, 'r')

	for line in readFa :
		if line[0] == '>' :
			fastaContent[key] = content
			content = ''
				
			lineSplit = line.split()
			key = lineSplit[0][1:]
		else :
			content += line
		
	fastaContent[key] = content	
	del fastaContent['']
	readFa.close()
	return fastaContent
	
def createFastaFile(geneList,fastaContent,outputFile) :
	geneNumber = 0
	newFasta = open(outputFile,'w')
	
	for scaff in geneList :
		for gene in range(0,len(geneList[scaff])) :
			for contig in range(0,len(geneList[scaff][gene][2])) :
				newFasta.write(">" + geneList[scaff][gene][2][contig] + '_gene_' + str(geneNumber) + '\n')
				newFasta.write(fastaContent[geneList[scaff][gene][2][contig]])
				del fastaContent[geneList[scaff][gene][2][contig]]
			geneNumber += 1
	for unmatch in fastaContent :
		newFasta.write(">" + unmatch + '_NoBlatMatchFound\n')
		newFasta.write(fastaContent[unmatch])
	print "new genes number : " , geneNumber
	
	newFasta.close()


####################
### Main
####################

#printing a line to know that the programm is running. to be removed ?
print "running blatSeq0.2"

if dbFileName != "--noBLAT" :
	print "BLAT"
	blat(dbFileName, fastaFileName, txtFileName)
	print "end of BLAT"
else :
	print "noBLAT"

print "creating gene list"
geneList = createGeneList(txtFileName)
print "gene list done"

print "reading original fasta file"
fastaContent = readFasta(fastaFileName)
print "fasta file read"

print "creating new fasta file"
createFastaFile(geneList,fastaContent,newFastaFileName)
print "output created"

#programm is over
print "done blatSeq"

