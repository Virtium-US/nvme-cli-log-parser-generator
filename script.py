import csv
import argparse
from argparse import RawTextHelpFormatter

#parse arugments
parser = argparse.ArgumentParser(description='Parse a log csv file into usable code for the nvme virtium plugin\n\n'
                                 + 'format is as follows:\n\n\tpython3 script.py csvfile_name series_name+log_type log_length log_num description\n\n'
                                 + 'example:\n\n\tpython3 script.py test.csv series61_vs 4096 0xc6 Prints formatted Series 61-specific info block',
                                 formatter_class=RawTextHelpFormatter)
parser.add_argument("file", help="input for the file")
parser.add_argument("series", help="input for the log type you are to retrive from whatever series you want")
parser.add_argument("len", help="input for log length")
parser.add_argument("num", help="input for the log number")
parser.add_argument("desc", help="input for the description of the plugin", nargs='+')

#variable to hold the name of the attribute and it's offset
variable_ls = []

''' opens the csv file, saves it's contents in a list and returns that list'''
def open_csv_file(file_):
    with open(file_,'r') as file:
        file_reader = csv.reader(file, delimiter=',')
        file_list = []
        for line in file_reader:
            file_list.append(line)
        return file_list

'''
   creates a variable for the struct and appends it the body of the struct. Takes in the attribute name,
   the string for the struct body, the size of the attribute, and the number of ignore values, returns
   the newly created struct body and the count of the ignore values
'''    
def gen_struct_body(name,body,size,count):
    name = name.replace('.','_')
    name = name.replace('/','_')
    name = name.replace('-','')
    name = name.replace('(',' ')
    name = name.replace(')',' ')
    name = name[0].lower() + name[1:]
    name = name.split(' ')
    if len(name) > 1:
        name = [w.capitalize() for w in name]
    n = ''
    n = n.join(name)
    n = n[0].lower() + n[1:]
    
    if 'Ignore' in n:
        n = 'ignore' + str(count)
        count += 1
    if 'reserve' in n:
        n = 'reserve' + str(count)
        count += 1
    if n in body:
        body = body.replace(n,n+'1')
        n = n + '2'
    variable_ls.append((n,size))
    if size == 8:
        decleration = 'uint64_t ' + n + ';'
    elif size == 4:
        decleration = 'uint32_t ' + n + ';'
    elif size == 2:
        decleration = 'uint16_t ' + n + ';'
    elif size == 1:
        decleration = 'uint8_t ' + n + ';'
    else:
        decleration = 'uint8_t ' + n +'[' + str(size) +'];'
    body = body + decleration + '\n\t'
    return body, count

'''generates the struct, takes the file list and the series name returns a formatted string for a struct'''        
def create_struct(file,series_name):
    struct_header = 'typedef struct _' + series_name + '{\n'
    struct_body = '\t'
    ign_count = 1
    for i in range(1,len(file)):
        if '-' in file[i][0]:
            offset = file[i][0].split('-')
            size = int(offset[1]) - int(offset[0])
        else:
            if i != len(file)-1:
                size = int(file[i+1][0]) - int(file[i][0])
            else:
                size = 8
        nm = file[i][1].replace('\n','')
        struct_body, ign_count = gen_struct_body(nm,struct_body,size,ign_count)
    struct = struct_header + struct_body[:-1] + '} ' + series_name + ';'
    return struct

'''
   creates the print function using the variable list, takes in the series name and returns the string
   for the print function
'''
def create_print(series_name):
    funct_header = 'static void print_' + series_name + '_info(' + series_name + '* data_block) {\n'
    funct_body = '\t'
    for tup in variable_ls:
        if tup[1] <8:
            print_s = 'printf("' + tup[0] + ': %d\\n", data_block->' + tup[0] + ');\n\t'
        else:
            print_s = 'printf("' + tup[0] + ': %ld\\n", data_block->' + tup[0] + ');\n\t'
        if 'ignore' in tup[0]:
            pass
        elif 'reserve' in tup[0]:
            pass
        else:
            funct_body += print_s
            
    funct = funct_header + funct_body[:-1] + '}'
    
    return funct

'''creats the parse function, takes in the series name, the log lenth and the log number'''    
def create_parse(series_name, log_len, log_number):
    funct_header = 'static int vt_parse_' + series_name + '_info(int argc, char **argv, struct command *cmd, struct plugin *plugin) {\n\t'
    funct_body = 'OPT_ARGS(opts) = {\n\t\tOPT_END()\n\t};\n\n\t'
    funct_body += 'int fd = parse_and_open(argc, argv, "", opts);\n\tif(fd < 0) {\n\t\t'
    funct_body += 'printf("Error parse and open (fd = %d)\\n", fd);\n\t\treturn -1;\n\t}\n\n\t'
    funct_body += 'int log_len = ' + str(log_len) + ';\n\tunsigned char* log_data = malloc(log_len);\n\t'
    funct_body += 'int err = nvme_get_log(fd, NVME_NSID_ALL, ' + str(log_number) + ', 0, 1, log_len, log_data);\n\n\t'
    funct_body += 'if (err != 0) {\n\t\tprintf("Invalid log page access!\\n");\n\t} else {\n\t\t'
    funct_body += series_name + ' data_block;\n\t\tmemcpy(&data_block, log_data, sizeof(data_block));\n\t\t'
    funct_body += 'print_' + series_name +'(&data_block);\n\t}\n\n\tfree(log_data);\n\n\treturn err;\n}'

    return funct_header + funct_body

'''creates the plugin entry, takes in the series name and returns the a formatted string for the plugin'''
def create_plugin(series_name,description):
    name = series_name.replace('_','-')
    plugin = 'ENTRY("parse-' + name +'",' + '"' + description + '", vt_parse_' + series_name + ')'

    return plugin

'''main function that runs all the program'''
def main(file,series_name,log_len,log_val,description):    
    file = open_csv_file(file)
    struct = create_struct(file,series_name)
    funct_print = create_print(series_name)
    parse = create_parse(series_name,log_len,log_val)
    plugin = create_plugin(series_name,description)
    print('//struct for ' + series_name + '\n\n' + struct + '\n\n//print function for ' + series_name
          + '\n\n' + funct_print + '\n\n//parse function for ' + series_name + '\n\n' + parse
          + '\n\n//plugin for ' + series_name + '\n\n' + plugin)
    
if __name__ == "__main__":
    args = parser.parse_args()
    main(args.file,args.series,args.len,args.num,' '.join(args.desc))
