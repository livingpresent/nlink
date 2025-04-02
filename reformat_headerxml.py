import csv
import os

def reformat_file(input_file):
    output_file = os.path.splitext(input_file)[0] + "_reformat.csv"
    
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=';')
        writer.writerow(['class', 'operation', 'parameters'])
        
        current_class = None
        current_operation = None
        parameters = []
        
        for line in infile:
            line = line.strip()
            if line.startswith("class ="):
                current_class = line.split("=", 1)[1].strip()
            elif line.startswith("operation ="):
                current_operation = line.split("=", 1)[1].strip()
            elif line.startswith("parameters:"):
                parameters = []
            elif line:
                parameters.append(line)
            else:
                for param in parameters:
                    writer.writerow([current_class, current_operation, param])
                current_class = None
                current_operation = None
                parameters = []

        # Handle the last block if the file does not end with a blank line
        if current_class and current_operation and parameters:
            for param in parameters:
                writer.writerow([current_class, current_operation, param])

if __name__ == "__main__":
    input_file = r'C:\Users\wwonganu\Downloads\busby_fromson.txt'  # Replace with your input file name
    reformat_file(input_file)