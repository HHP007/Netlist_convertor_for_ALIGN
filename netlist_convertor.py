import re
import sys
import os

def convert_spectre_to_spice_subcircuit(spectre_file_path):
    spice_netlist = ""
    node_names = set()
    global_variable = ""
    continuation_line = ""

    with open(spectre_file_path, 'r') as spectre_file:
        # Extract the circuit name from the file path
        circuit_name = os.path.splitext(os.path.basename(spectre_file_path))[0]

        tokens = []  # Initialize tokens outside the loop

        for line in spectre_file:
            line = re.sub(r'//.*', '', line).strip()

            # Handle continuation lines
            if line.endswith('\\'):
                continuation_line += line[:-1].strip() + ' '
                continue
            else:
                line = continuation_line + line
                continuation_line = ""

            # Add white space around closing brackets for later extraction
            line = re.sub(r'(\))', r' \1 ', line)

            # Extract global variable and replace its third word
            if line.startswith("global"):
                tokens = line.split()
                if len(tokens) >= 3:
                    # Find the third word even if it has brackets
                    third_word = re.search(r'\b' + re.escape(tokens[2]) + r'\b', line)
                    if third_word:
                        global_variable = third_word.group()
            elif line.startswith("include"):
                continue
            elif 'global_variable' in locals() and len(tokens) >= 3:
                # Replace occurrences of the third word even if it has brackets
                line = re.sub(re.escape(tokens[2]), "vdd", line)

            # Extract nodes inside brackets and add to node_names
            if re.match(r'^[a-zA-Z]\d', line):
                nodes = re.search(r'\((.*?)\)', line)
                if nodes:
                    node_names.update(nodes.group(1).split())

    # Add .subckt line at the top with unique words
    subcircuit_nodes = sorted(set([node for node in node_names if not node.startswith("net")]))
    subcircuit_nodes.extend(['vdd', '0'])
    subcircuit_nodes = ' '.join(sorted(set(subcircuit_nodes), key=subcircuit_nodes.index))
    spice_netlist += f".subckt {circuit_name} {subcircuit_nodes}\n"

    with open(spectre_file_path, 'r') as spectre_file:
        for line in spectre_file:
            line = re.sub(r'//.*', '', line).strip()

            # Handle continuation lines
            if line.endswith('\\'):
                continuation_line += line[:-1].strip() + ' '
                continue
            else:
                line = continuation_line + line
                continuation_line = ""

            # Convert component definitions
            if re.match(r'^[a-zA-Z]\d', line):
                tokens = re.split(r'\s+', line)
                component_name = tokens[0][0].lower() + tokens[0][1:]
                spice_line = f"{component_name} "

                # Extract nodes inside brackets
                nodes = re.search(r'\((.*?)\)', line)
                if nodes:
                    nodes = nodes.group(1).split()
                    spice_line += ' '.join(nodes) + ' '

                # Handle MOSFET components
                if component_name.startswith('m'):
                    # Extract the word after the closing bracket
                    closing_bracket_word = re.search(r'\) (\S+)', line)
                    if closing_bracket_word:
                        word_after_bracket = closing_bracket_word.group(1)
                        # Replace underscores with "rvt"
                        word_after_bracket = re.sub(r'_(\S+)', r'_rvt', word_after_bracket)
                        spice_line += f"{word_after_bracket} "

                    for token in tokens[1:]:
                        if "=" in token and "type=" not in token and "mode=" not in token:
                            param, value = token.split('=')
                            if param.startswith("w"):
                                spice_line += f"w={value} "
                            elif param.startswith("l"):
                                spice_line += f"l={value} "
                            elif param.startswith("nf"):
                                spice_line += f"nf={value} "
                            elif param.startswith("m"):
                                spice_line += f"m={value} "
                    
                else:
                    # Add other parameters for non-MOSFET components
                    for token in tokens[1:]:
                        if "=" in token and "type=" not in token and "mode=" not in token :
                            param, value = token.split('=')
                            spice_line += f"{value} "
                        #elif "w=" in token :
                            
                           # param, value = token.split('=')
                           # spice_line += f"{param}={value} "
                        else:
                            continue

                spice_netlist += spice_line[:-1] + "\n"

    # Add an end statement to close the Spice subcircuit
    spice_netlist += f".ends {circuit_name}\n"

    # Replace any remaining "vdd!" with "vdd"
    spice_netlist = spice_netlist.replace("vdd!", "vdd")

    # Remove all brackets from the final spice file
    spice_netlist = re.sub(r'[{}()]', '', spice_netlist)

    # Write the converted netlist to a new file with .sp extension
    spice_file_path = f"{circuit_name}.sp"
    with open(spice_file_path, 'w') as spice_file:
        spice_file.write(spice_netlist)

    print(f"Conversion successful. Spice subcircuit saved to {spice_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_spectre_to_spice_subcircuit.py <input_file.txt>")
        sys.exit(1)

    spectre_file_path = sys.argv[1]
    convert_spectre_to_spice_subcircuit(spectre_file_path)
