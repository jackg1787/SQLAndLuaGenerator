
# Package management - These are base packages with python 3. you don't need to install anything else
import os
import csv

# DISCLAMER AND INSTRUCTIONs
print("""    ###########################################################################################################
    #                                                                                                         #
    # Script to create the parsing script and create script for a sql save connector                          #
    # To use, simply generate the sql connector to a csv file, and run this script on it.                     #
    # It will produce a sql txt file to be run on the db, and a lua file to be pasted into the parsing script #
    #                                                                                                         #
    # The script can produce either MySQL or SQL Server, and will either produce a stored procedure, or just  #
    # the insert statements depending on which options you go for.                                            #
    #                                                                                                         #   
    # NOTE: ONLY THE FIELDS CONTAINED WITHIN EACH BLOCK WILL BE IN EACH TABLE. IF THERE                       #
    # IS A UNIQUE ID YOU WANT IN ALL TABLES IT NEEDS TO BE ADDED MANUALLY AFTER!!                             #
    # Conversely, if there are repeated fields the SP will not work as you cannot define same name twice.     #
    # Check your fields, or be aware of these limitations if the scripts are not working!                     #
    #                                                                                                         #
    # How it works: Basically its just a series of for loops- loop through the csv until you find a 'node'    #
    # This indicates the name of a block. then for each of the fields until you find the next node, write the #
    # Required code.                                                                                          #
    #                Code by Jack Gorton 05/06/2018 jack.gorton@gdslink.com                                   #
    ###########################################################################################################
""")

# get file name and location
directory = input("input path to file without quotes: ")
NameOfInputFile = input("input name of file without quotes: ")

# set what type of SQL to be generated, and wheter a stored procedure needs to be created
TypeOfSQL = input("What Type of SQL? For MySql Hit 1, for SQL Server 2: ")
SPOrInsert = input("if you need a Stored Procedure press 1, otherwise press 2: ")

# define function to remove n'th charater of string. used to remove last commas in insert statements
def remove_char(str, n):
      k = len(str)-n
      first_part = str[:k] 
      last_pasrt = str[k+1:]
      return first_part + last_pasrt
  
#SetWD
os.chdir(directory)
#set up list to hold data
fullcsv = []
# create the two files
file = open("LuaParsingScript.txt","w")    
file2 = open("SQLCreateScript.txt","w") 

# Read the CSV file
with open(NameOfInputFile, 'rt') as csvfile:
    next(csvfile)
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        fullcsv.append(row)
        
# get list of tables    
TableNames = []
for row in fullcsv:
    #print(row[0])
    if row[0]=="    NODE":
        TableNames.append(row[1])
        
# get name of root node e.g. Request        
RootNode = TableNames[0]
del TableNames[0] 
  
# start of lua parsing script   
file.write("MainRecord = 0 \n")
file.write("RequestKey= GetSegmentKey(MainRecord,<><"+RootNode+"><>,1) \n")
file.write("if RequestKey ~= -1 then \n sql_statement = \'\' \n sql_declaration = \'\'  \n sql_declaration2 = \'\'")

# LUA PARSING SCRIPT loop- get field values, and add the string.gsub line to escape any quotes 
for i in range(len(fullcsv)):
    if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
        # comment for the name of the block
        line ="\n"+"\t--"+fullcsv[i][1]+"\n"
        file.write(line)
        #set name of block for use in the get field value lines
        NodeName = fullcsv[i][1]
        # loop from start of node
        for j in range(i+1,len(fullcsv)):
            # only loop for fields- break when find the next node
            if fullcsv[j][0]=='    FIELD':
                # this writes fieldname = '' followed by a new line
                line = "\t"+fullcsv[j][1]+"= \'\' \n" 
                file.write(line)
                # get field value line
                line =  "\t"+fullcsv[j][1]+ "=GetFieldValue(RequestKey,<><"+RootNode+"<><"+NodeName+"^^^"+fullcsv[j][1]+"><>)"+"\n"
                file.write(line)
                #gsub line
                line =  "\t"+fullcsv[j][1]+ "=string.gsub("+fullcsv[j][1]+",\"\'\", \"\'\'\" ) \n"
                file.write(line)
                j=j+1
                
            else:
                break
            
#insert looks the same for mysql and sql server, so do both outside of type of sql if statemnts.
### INSERT OPTION
if SPOrInsert == '2':  
        # set some lists to hold the full strings
        megalist = ''     
        dotties = ''
        # this loop writes the lua for the ususal 'insert into Table(names,...)VALUES('"..value.."', ...);
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                megalist = megalist+"\n sql_declaration = sql_declaration ..\" INSERT INTO "+fullcsv[i][1]+"( "
                list2 = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        dot = "\'\".."+fullcsv[j][1]+"..\"\', "
                        list2=list2+fullcsv[j][1]+", "
                        dotties = dotties+ dot
                        j=j+1
                        
                    else:
                         #remove last commas   
                        list2 = remove_char(list2,2)
                        dotties = remove_char(dotties,2)
                        #construct the insert
                        megalist= megalist+list2+")"+"VALUES("+dotties+");"
                        break 
                    
        #write to file                  
        file.write(megalist)  
        
#### MySQL OPTION ####       
if TypeOfSQL == '1':         
    #### STORED PROCEDURE OPTION ####            
    if SPOrInsert == '1':  
          
        megalist = ''            
        #sql declerations for lua parsing script exec sp         
        file.write("\n sql_declaration = sql_declaration ..\" SET \"")
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                megalist = megalist+"\n sql_declaration = sql_declaration ..\" "
                list2 = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        line4 =" @"+fullcsv[j][1]+"= \'\".."+fullcsv[j][1]+"..\"\', "
                        list2=list2+line4
                        j=j+1
                        
                    else:
                        megalist= megalist+list2+"\""
                        break 
                    
        #remove last comma            
        megalist = remove_char(megalist,3)            
        file.write(megalist)
        file.write("\n sql_declaration = sql_declaration ..\" ; \"")
        
        #exec sp
        megalist = ''
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                megalist= megalist+"\n sql_declaration2 = sql_declaration2 ..\"  "
                list2 = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        line4 =" @"+fullcsv[j][1]+", "
                        list2=list2+line4
                        j=j+1
                        
                    else:
                        megalist= megalist+list2+"\""
                        break 
                    
        #remove last comma
        megalist = remove_char(megalist,3)            
        file.write(megalist)  
        
        #all the guff at end of script- actually call the sp etc.    
        file.write("\n \n sql_statement = sql_statement .. sql_declaration.. \"CALL insertrecord( \"..sql_declaration2..\" );\" \n OutputInfoString(\"MySQL STATEMENT: \" ..sql_statement) \nSetDataStream(sql_statement)")    
        
    
        
    #### MySQL CREATE table sql script ####
  
    megalist = ''
    for i in range(len(fullcsv)):
        if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
            line2 = "CREATE TABLE "+fullcsv[i][1]+"("+fullcsv[i][1]+"TableID INT NOT NULL AUTO_INCREMENT,"
            file2.write(line2)
            NodeName = fullcsv[i][1]
            
            for j in range(i+1,len(fullcsv)):
                if fullcsv[j][0]=='    FIELD':
                    line2 =fullcsv[j][1]+" VARCHAR(" +fullcsv[j][2]+"),"
                    file2.write(line2)
                    j=j+1
                    
                else:
                    line2 = " PRIMARY KEY("+fullcsv[i][1]+"TableID) ); \n \n"
                    file2.write(line2)
                    break 
    
          
    #### SQL SCRIPT TO CREATE THE SP ON THE MySQL server ####
    if SPOrInsert == '1':  
        #SQL CREATE sp- get all fields  
        file2.write("\nDELIMITER $$ \nCREATE PROCEDURE `insertrecord`(")
        megalist = ''
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                list1 = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        line3 ="IN "+fullcsv[j][1]+" VARCHAR(" +fullcsv[j][2]+"),\n"
                        list1=list1+line3
                        j=j+1
                        
                    else:
                        list1 = list1[:-2]
                        line3 = list1+",\n \n"
                        megalist = megalist+line3
                        break 
                    
          # remove a trailing comma          
        megalist = remove_char(megalist,4)            
        file2.write(megalist)  
                    
        file2.write(") \nBEGIN \nDECLARE EXIT HANDLER FOR SQLEXCEPTION \n\tBEGIN\n\tROLLBACK;\n\tRESIGNAL; \nEND;\n START TRANSACTION;  \n \n")            
        # loop to create the insert record sps            
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                line3 = "INSERT INTO "+fullcsv[i][1]+"("
                file2.write(line3)
                tablechunk = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        line3 =fullcsv[j][1]+",\n"
                        tablechunk = tablechunk+line3
                        j=j+1
                        
                    else:
                        tablechunk = tablechunk[:-2]
                        line3 = tablechunk+") VALUES( "+tablechunk+"); \n \n"
                        file2.write(line3)
                        break 
        
        file2.write("COMMIT; \nEND$$ \nDELIMITER ;")

#### SQL SERVER OPTION ###       
elif TypeOfSQL == '2':
    
    #### SQLServer CREATE table sql script ####
    megalist = ''
    for i in range(len(fullcsv)):
        if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
            line2 = "CREATE TABLE "+fullcsv[i][1]+"("+fullcsv[i][1]+"TableID int identity(1,1) PRIMARY KEY"
            file2.write(line2)
            
            for j in range(i+1,len(fullcsv)):
                if fullcsv[j][0]=='    FIELD':
                    if int(fullcsv[j][2])< 8000:
                        line2 =", "+fullcsv[j][1]+" VARCHAR(" +fullcsv[j][2]+")"
                        file2.write(line2)
                        j=j+1
                    else:
                        line2 =", "+fullcsv[j][1]+" VARCHAR(MAX)"
                        file2.write(line2)
                        j=j+1
                else:
                    file2.write("); \n \n")
                    break 

        
    #### STORED PROCEDURE FOR SQL SERVER ####
    if SPOrInsert == '1':  
        megalist = ''
        #SQL CREATE STORED PROC- get all fields IN THE FORM @NAME VARCHAR(N) = '' 
        file2.write("\nSET ANSI_NULLS ON\nGO\nSET QUOTED_IDENTIFIER ON\nGO\n\nCREATE PROCEDURE [dbo].[insertrecord]\n")
        megalist = ''
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                list1 = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        if int(fullcsv[j][2])< 8000:
                            line3 ="@"+fullcsv[j][1]+" VARCHAR(" +fullcsv[j][2]+") = \'\',\n"
                            list1=list1+line3
                            j=j+1
                        else:
                            line3 ="@"+fullcsv[j][1]+" VARCHAR(MAX) = \'\',\n"
                            list1=list1+line3
                            j=j+1
                        
                    else:
                        list1 = list1[:-2]
                        line3 = list1+",\n \n"
                        megalist = megalist+line3
                        break
                    
        megalist = remove_char(megalist,4)            
        file2.write(megalist) 
        # STUFF AT THE START OF THE SP
        file2.write("AS\nBEGIN\nSET NOCOUNT ON;\nBEGIN TRANSACTION\nBEGIN TRY\n")
        # INSERT BITS FOR THE SP
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                line3 = "INSERT INTO "+fullcsv[i][1]+"("
                file2.write(line3)
                tablechunk = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        line3 =fullcsv[j][1]+",\n"
                        tablechunk = tablechunk+line3
                        j=j+1
                        
                    else:
                        tablechunk = tablechunk[:-2]
                        line3 = tablechunk+") VALUES( "+tablechunk+"); \n \n"
                        file2.write(line3)
                        break 
        # END STUFF OF THE SP, INCLUDING A CATCH/ ROLLBACK FOR ANY ERRORS, AND A SELECT IDENTITY TO RETURN THE TRANSACTION IDENTITY
        file2.write("SELECT @@IDENTITY AS IDENT\nCOMMIT\nEND TRY\nBEGIN CATCH\nROLLBACK\nEND CATCH \nEND\nGO ;")            
                    
        #### SQL SERVER Execute SP LUA Script ####             
        megalist = ''
        for i in range(len(fullcsv)):
            if fullcsv[i][0]=='    NODE' and fullcsv[i][1] != RootNode:
                megalist= megalist+"\n sql_declaration = sql_declaration ..\"  "
                list2 = ''
                for j in range(i+1,len(fullcsv)):
                    if fullcsv[j][0]=='    FIELD':
                        line4 =" @"+fullcsv[j][1]+"= N\'\".."+fullcsv[j][1]+"..\"\', "
                        list2=list2+line4
                        j=j+1
                        
                    else:
                        megalist= megalist+list2+"\""
                        break 
                    
        #remove last comma
        megalist = remove_char(megalist,3)            
        file.write(megalist)  
        file.write("\nsql_statement = sql_statement .. \" EXEC insertrecord \"\nsql_statement = sql_statement .. sql_declaration \nSetDataStream(sql_statement)")

else:
    print("How hard is it to type a 1 or a 2")
    
file.close()
file2.close()  
    