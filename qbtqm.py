

PATH_PAIRS_SEPARATOR = '|'
INT_PATTERN_START = 'i'
LIST_PATTERN_START = 'l'
DICT_PATTERN_START = 'd'
END_DELIMITER = 'e'

class BencodeException(Exception):
    pass

class BencodeParser():
    def __init__(self, file_path = None):
        self.file_path = file_path
        self.pos = 0
        self.file_string = ""
        self.value = None

    def warn(self, text):
        import sys
        print(f"\033[95mWARNING>> {text}\033[0m", file=sys.stderr)

    def check_position(self):
        """Checks the position marker in the parser to warn about reparsing"""
        if self.pos != 0:
            if self.pos == (len(self.file_string)-1):
                self.warn("\033[95mWARNING: Position indicator is at end of file. This indicates a finished parsing")
            self.warn("Position indicator is in the middle of the file. This indicates an unfinished parsing")
    
    def parse(self, file_path = None):
        """Parses with an initialized filepath, or initializes the one provided and parses it"""
        if file_path is not None:
            self.file_path = file_path
        if self.file_path is None:
            raise BencodeException("Attempted to parse self without a filepath.")
        with open(self.file_path, "rb") as fopen:
            file_string = fopen.read().decode(encoding="latin-1")
            self.parse_bencode_string(file_string)

    def parse_bencode_string(self, file_string: str):
        self.file_string = file_string
        self.check_position()
        root_node_parsed_flag = False
        while self.pos < len(self.file_string):
            if root_node_parsed_flag:
                raise BencodeException("Error: Found multiple root items while parsing.")
            value = self.decode_value()
            if value:
                root_node_parsed_flag = True
        self.value = value

    def decode_value(self):
        char = self.file_string[self.pos]
        # print(self.pos, len(self.file_string), char)
        if char == LIST_PATTERN_START:
            return self.decode_list()
        elif char == DICT_PATTERN_START:
            return self.decode_dict()
        elif char == INT_PATTERN_START:
            return self.decode_int()
        elif char.isdecimal():
            return self.decode_string()

    def decode_int(self):
        start = self.pos
        if not self.file_string[self.pos] == INT_PATTERN_START:
            raise BencodeException(f"Integer at position {self.pos} has not 'i' at the start")
        self.pos +=1
        # check if `i0...` is not the (exclusive) valid case of i0e
        if self.file_string[self.pos] == "0" and not self.file_string[self.pos+1] == END_DELIMITER:
            raise BencodeException(f"Integer at position {self.pos} starts with `0`, and it's not the exclusively valid case of i0e")
        # check if it's the invalid case of `i-0...`
        if self.file_string[self.pos] == "-" and self.file_string[self.pos+1] == "0":
            raise BencodeException(f"Integer at position {self.pos} starts with `-0`")

        num_str_buffer = []
        
        while not self.file_string[self.pos] == "e":
            if self.file_string[self.pos].isdecimal() or self.file_string[self.pos] == "-":
                num_str_buffer.append(self.file_string[self.pos])
            else:
                raise BencodeException(f"Malformed int at position {start}. Non-int, non-dash character encountered at {self.pos}, while parsingint beginning at {start}")
            self.pos += 1
            if self.pos == len(self.file_string):
                raise BencodeException(f"Unterminated int at position {start}.")

        if self.file_string[self.pos] == "e":
            self.pos += 1
            return int(''.join(num_str_buffer))

    def decode_string(self):
        start = self.pos
        length_str_buffer = []
        str_lenght = None
        while self.pos < len(self.file_string):
            if self.file_string[self.pos] == ":":
                str_lenght = int(''.join(length_str_buffer))
                self.pos += 1
                break
            elif self.file_string[self.pos].isdecimal():
                length_str_buffer.append(self.file_string[self.pos])
            else:
                raise BencodeException (f"Length character '{self.file_string[self.pos]}' at position {self.pos} from string starting at position {start} is not decimal or colon.")
            self.pos += 1
        
        if str_lenght is None:
            raise BencodeException("No colon detected before data end")

        if self.pos+str_lenght <= len(self.file_string):
            str_slice = self.file_string[self.pos:self.pos+str_lenght]
            self.pos +=str_lenght
            return str_slice
        else:
            raise BencodeException (f"Defined string length of {str_lenght} is greater than remaining length of {len(self.file_string)-self.pos}.")

    def decode_list(self):
        start = self.pos
        if not self.file_string[self.pos] == LIST_PATTERN_START:
            raise BencodeException(f"List at position {self.pos} has not '{LIST_PATTERN_START}' at the start.")
        self.pos +=1
        list_buffer = []
        
        while not self.file_string[self.pos] == END_DELIMITER:
            list_buffer.append(self.decode_value())
            if self.pos == len(self.file_string):
                raise BencodeException(f"Unterminated list at position {start}")
        
        self.pos +=1
        return list_buffer

    def decode_dict(self):
        start = self.pos
        if not self.file_string[self.pos] == DICT_PATTERN_START:
            raise BencodeException(f"Dict at position {self.pos} has not '{LIST_PATTERN_START}' at the start.")
        self.pos +=1
        dict_buffer = {}
        
        while not self.file_string[self.pos] == END_DELIMITER:
            key_start_pos = self.pos
            key = self.decode_value()
            if not type(key) == str:
                raise BencodeException(f"Error while parsing dictionary key at position {key_start_pos}: Returned parsed value is not type(str).")
            value_start_pos = self.pos
            value = self.decode_value()
            if value is None:
                raise BencodeException(f"Attempted to parse a value at position {value_start_pos} for key `{key}` at position {key_start_pos}, but none was found.")
            if self.pos == len(self.file_string):
                raise BencodeException(f"Unterminated dict at position {start}")
            dict_buffer[key] = value

        self.pos +=1
        return dict_buffer

    def write(self, out_file):
        with open(out_file or self.file_path, "wb") as fopen:
            fopen.write(self.encode_value(self.value).encode("latin-1"))

    def encode_value(self, value):
        if type(value) == int:
            return self.encode_int(value)
        if type(value) == str:
            return self.encode_string(value)
        if type(value) == list:
            return self.encode_list(value)
        if type(value) == dict:
            return self.encode_dict(value)

    def encode_int(self, value):
        return f"i{value}e"

    def encode_string(self, value):
        return f"{len(value)}:{value}"

    def encode_list(self, value):
        placeholder_list = [LIST_PATTERN_START]
        for item in value:
            placeholder_list.append(self.encode_value(item))
        placeholder_list.append(END_DELIMITER)
        return ''.join(placeholder_list)

    def encode_dict(self, value):
        placeholder_dict = [DICT_PATTERN_START]
        for k, v in value.items():
            placeholder_dict.append(self.encode_string(k))
            placeholder_dict.append(self.encode_value(v))
        placeholder_dict.append(END_DELIMITER)
        return ''.join(placeholder_dict)

    def outjson(self, out_json):
        import json
        with open(out_json,"wt") as fopen:
            json.dump(self.value, fopen, indent=2)


def convert_fastresume_dir(*,input_dir = "", output_dir, input_file, inplace = False):
    import os
    while not os.path.exists(input_dir):
        input_dir = input("QT_backup directory address:")
        if not os.path.isdir(input_dir):
            print(f"Path does not exist: {input_dir}")

    if output_dir is None and not inplace:
        while output_dir is None:
            temp_out_dir = input(f"No output dir was given, and --inplace was not specified. By default this will drop all the files in the current directory ({output_dir}). If you wish to specify a different directory, type it now: ")
            if len(temp_out_dir) == 0:
                output_dir = os.getcwd()
            else:
                if not os.path.isdir(temp_out_dir):
                    mkdir_answer = input(f"Path does not exist. Create it [Y/n]?")
                    if mkdir_answer.lower() in ("","y"):
                        os.makedirs(temp_out_dir)
                output_dir = temp_out_dir

    fastresume_paths_dict = {}
    fastresume_files_count = 0
    torrent_files = []

    for file in os.listdir(input_dir):
        try:
            if file.endswith(".fastresume"):
                fastresume_files_count +=1
                file_path = os.path.join(input_dir,file)
                p = BencodeParser(file_path)
                p.parse()
                if not type(fastresume_paths_dict.get(p.value["save_path"])) == list:
                    fastresume_paths_dict[p.value["save_path"]] = []
                fastresume_paths_dict[p.value["save_path"]].append(p)
            elif file.endswith(".torrent") and not inplace:
                torrent_files.append(file_path)
        except BencodeException as e:
            print(f"Exception found when parsing file number {fastresume_files_count}, named `{file}`:")
            print(e)
            exit(1)

    if len(fastresume_paths_dict.keys()) == 0:
        print(f"\033[95mWARNING>> No saved torrent paths were registered. {fastresume_files_count} fastresume files were found and processed. Exiting now...\033[0m")
        exit(1)
    print(f"Found {len(fastresume_paths_dict.keys())} unique paths. You will now be shown all of the unique paths to get an idea, and then will be prompted *once per unique path* to provide a replacement path. If you do not want to replace a path just give an empty input (hit Enter without typing anything). REMEMBER to account for file path case-sensitivity if the target system is case-sensitive.")
    print(f"Paths:\n{"\n".join(fastresume_paths_dict.keys())}\n")

    collected_paths = {}
    if input_file:
        missing_in_fastresume_paths = []
        missing_fastresume_paths = [x for x in fastresume_paths_dict.keys()]
        with open(input_file, "rt") as in_file:
            for line_n, line_text in enumerate(in_file):
                path_pair = line_text.strip().split(PATH_PAIRS_SEPARATOR)
                if len(path_pair) != 2:
                    raise ValueError(f"Line {line_n} in path pairs file '{input_file}' was not properly formed")
                if path_pair[0] in fastresume_paths_dict:
                    collected_paths[path_pair[0]] = path_pair[1]
                    missing_fastresume_paths.remove(path_pair[0])
                else:
                    missing_in_fastresume_paths.append(path_pair[0])
        if len(missing_in_fastresume_paths) > 0:
            print(f"The following paths listed on the file as replacement candidates were not found in the list of collected paths from fastresume files and will be ignored:\n {"\n".join(missing_in_fastresume_paths)}")
        if len(missing_fastresume_paths) > 0:
            print(f"The following paths collected from the fastresume files were not listed on the file as replacement candidates and will be ignored:\n {"\n".join(missing_fastresume_paths)}")
    else:
        for key in fastresume_paths_dict.keys():
            replacement_path = input(f"Replacement path for `{key}`: ")
            collected_paths[key] = replacement_path

    all_accepted = False
    while not all_accepted:
        print("All replacements are set as follows:")
        print("\n".join([ str(i)+") "+v for i, v in enumerate([k+" -> "+(v if len(v)>0 else "[NO CHANGE]") for k, v in collected_paths.items()])]))
        print("If all spark joy, type 'y' and press enter. If you want to change any *one*, type *just* the corresponding number and press enter.")
        choice = ""
        while not (choice.isdecimal() or choice.lower() == "y"):
            print("choice:", choice)
            choice = input("'Y' if all OK, number to change: ")
            print("choice:", choice)

        if choice.isdecimal() and (choice_i := int(choice)) < len(collected_paths):
            selected_redo_path = list(collected_paths)[int(choice)]
            collected_paths[selected_redo_path] = input(f"Replacement path for `{selected_redo_path}`: ")
        elif choice.lower() == "y":
            all_accepted = True

    if all_accepted:
        if not inplace:
            import shutil
            for torrent_file in torrent_files:
               shutil.copy2(torrent_file, os.path.join(output_dir, os.path.basename(torrent_file)))
        for key, replacement in collected_paths.items():
            for fastresume_p in fastresume_paths_dict[key]:
                print(f"REPLACING>>> {fastresume_p.value["save_path"]} -> {replacement if len(replacement) > 0 else "[NO CHANGE]"}")
                if len(replacement) > 0:
                    fastresume_p.value["save_path"] = replacement
                    fastresume_p.value["qBt-savePath"] = replacement.replace('\\','/')
                if inplace:
                    fastresume_p.write()
                else:
                    fastresume_p.write(os.path.join(output_dir, os.path.basename(fastresume_p.file_path)))

if __name__ == "__main__":
    import argparse
    argument_parser = argparse.ArgumentParser(
        prog="Batch qBittorrent downloaded file location modifier",
        description="This program reads all the *.fastresume files in a given directory, detects and collects the download locations of their respective torrents, and mass-replaces said locations for user-provided ones.",
    )
    argument_parser.add_argument("input_dir", nargs="?", dest="p_input_dir")
    argument_parser.add_argument("output_dir", nargs="?", dest="p_output_dir")
    argument_parser.add_argument("-d", "--input-dir", dest="o_input_dir")
    argument_parser.add_argument("-o", "--output-dir", dest="o_output_dir")
    argument_parser.add_argument("-f", "--input-file")
    argument_parser.add_argument("-i", "--inplace", action='store_true')

    arguments = argument_parser.parse_args()

    convert_fastresume_dir(input_dir = arguments.o_input_dir or arguments.p_input_dir, output_dir=arguments.o_output_dir or arguments.p_output_dir, input_file=arguments.input_file, inplace=arguments.inplace)