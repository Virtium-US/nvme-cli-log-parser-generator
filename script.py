import csv
import sys

#variable to hold the name of the attribute and it's offset
variable_ls = []

''' opens the csv file, saves it's contents in a list and returns that list with the name of the file'''
def open_csv_file(file_):
    with open(file_,'r') as file:
        file_reader = csv.reader(file, delimiter=',')
        file_list = []
        for line in file_reader:
            file_list.append(line)
        return file_list, file.name

'''
   creates a variable for the struct and appends it the body of the struct. Takes in the attribute name,
   the string for the struct body, the size of the attribute, and the number of ignore values, returns
   the newly created struct body and the count of the ignore values
'''    
def gen_struct_body(name,body,size,count):
    name = name.replace('.','_')
    name = name.replace('/','_')
    name = name.replace('-','')
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
    body = body + decleration + '\n    '
    return body, count

'''generates the struct, takes the file list and the file name returns a formatted string for a struct'''        
def create_struct(file,file_name):
    name = file_name.split('.')[0]
    struct_header = 'typedef struct _' + name + '{\n'
    struct_body = '    '
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
    struct = struct_header + struct_body[:-4] + '} ' + name
    return struct

'''
   creates the print function using the variable list, takes in the file name and returns the string
   for the print function
'''
def create_print(file_name):
    funct_header = 'static void print_' + file_name + '(' + file_name + '* data_block) {\n'
    funct_body = '    '
    for tup in variable_ls:
        if tup[1] < 8:
            print_s = 'printf("' + tup[0] + ': %d\\n", data_block->' + tup[0] + ');\n    '
        else:
            print_s = 'printf("' + tup[0] + ': %ld\\n", data_block->' + tup[0] + ');\n    '
        if 'ignore' in tup[0]:
            pass
        else:
            funct_body += print_s
            
    funct = funct_header + funct_body[0:-4] + '}'
    
    return funct

'''creats the parse function, takes in the file name, the log lenth and the log number'''    
def create_parse(file_name, log_len, log_number):
    funct_header = 'static int vt_parse_' + file_name + '_info(int argc, char **argv, struct command *cmd, struct plugin *plugin) {\n    '
    funct_body = 'OPT_ARGS(opts) = {\n        OPT_END()\n    };\n\n    '
    funct_body += 'int fd = parse_and_open(argc, argv, "", opts);\n    if(fd < 0) {\n        '
    funct_body += 'printf("Error parse and open (fd = %d)\\n", fd);\n        return -1;\n    }\n\n    '
    funct_body += 'int log_len = ' + str(log_len) + '\n    unsigned char* log_data = malloc(log_len);\n    '
    funct_body += 'int err = nvme_get_log(fd, NVME_NSID_ALL, ' + str(log_number) + ', 0, 1, log_len, log_data);\n\n    '
    funct_body += 'if (err != 0) {\n        printf("Invalid log page access!\\n");\n    } else {\n        '
    funct_body += file_name + ' data_block;\n        memcpy($data_block, log_data, sizeof(data_block));\n        '
    funct_body += 'print_' + file_name +'(&data_block);\n    }\n\n    free(log_data);\n\n    return err;\n}'

    return funct_header + funct_body

'''creates the plugin entry, takes in the file name and returns the a formatted string for the plugin'''
def create_plugin(file_name):
    name = file_name.replace('_','-')
    plugin = 'ENTRY("parse-' + name +'",' + '"Prints formatted Series *insert text here* data block' + '", vt_parse_' + file_name + '_info)'

    return plugin

'''main function that runs all the program'''
def main(file,log_len,log_val):    
    file, file_name = open_csv_file(file)
    struct = create_struct(file,file_name)
    funct_print = create_print(file_name.split('.')[0])
    parse = create_parse(file_name.split('.')[0],log_len,log_val)
    plugin = create_plugin(file_name.split('.')[0])
    print('//struct for ' + file_name + '\n\n' + struct + '\n\n//print function for ' + file_name
          + '\n\n' + funct_print + '\n\n//parse function for ' + file_name + '\n\n' + parse
          + '\n\n//plugin for ' + file_name + '\n\n' + plugin)
    
if __name__ == "__main__":
    main(sys.argv[1],sys.argv[2],sys.argv[3])
