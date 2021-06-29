# NVMe cli log parser genderator

A python command line script that gemerates a NVMe parser code for the [Virtium Plugin](https://github.com/Virtium-US/nvme-cli/tree/master/plugins/virtium)

## Getting Started

To use the this tool, clone the repository:
```
$git clone https://github.com/Virtium-US/nvme-cli-log-parser-generator.git
```

Inside the repository there is a *script.py*, the program you will run to generate the parser code, *test.csv* a csv file used as a test example, and *output* a txt file that shows an example of what the output will look like

***NOTE: the program only takes csv files of log descriptions. If the file is any other format make sure to either copy the contents into a csv file or convert the file to a csv file.***

## Running the Program

The program takes several arguments: file name, the log type + the series of the NVMe, log length, the log's number, and a description of what the pluggin is doing.

```
$ python3 script.py --help

usage: script.py [-h] file series len num desc [desc ...]

Parse a log csv file into usable code for the nvme virtium plugin

format is as follows:

	python3 script.py csvfile_name series_name+log_type log_length log_num description

example:

	python3 script.py test.csv series61_vs 4096 0xc6 Prints formatted Series 61-specific info block

positional arguments:
  file        input for the file
  series      input for the log type you are to retrive from whatever series you want
  len         input for log length
  num         input for the log number
  desc        input for the description of the plugin

optional arguments:
  -h, --help  show this help message and exit
```
