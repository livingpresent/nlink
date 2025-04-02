import xml.etree.ElementTree as ET

def extract_managed_object_data(xml_string):
    """Extract data from managedObject block."""
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        print("Invalid XML block. Please provide a valid XML block.")
        return None
    
    if root.tag != 'managedObject':
        print("No managedObject found in the provided XML block.")
        return None
    
    data = {}
    data['class'] = root.attrib.get('class')
    data['operation'] = root.attrib.get('operation')
    
    parameters = []
    for p in root.findall('.//p'):
        parameters.append(p.attrib.get('name'))
    
    data['parameters'] = parameters
    return data

def write_to_file(data, file_path):
    """Write extracted data to file."""
    with open(file_path, 'a') as f:
        f.write(f"class = {data['class']}\n")
        f.write(f"operation = {data['operation']}\n")
        f.write("parameters:\n")
        for param in data['parameters']:
            f.write(f"{param}\n")
        f.write("\n")

def main():
    input_file_path = input("Enter the input file path: ")
    output_file_path = input("Enter the output file path: ")
    
    while True:
        with open(input_file_path, 'r') as input_file:
            xml_block = input_file.read()
        
        data = extract_managed_object_data(xml_block)
        if data:
            write_to_file(data, output_file_path)
            print("Data written to file.")
        else:
            print("Failed to extract data from the provided XML block.")
        
        continue_input = input("Do you want to process another block? (yes/no): ")
        if continue_input.lower() != 'yes':
            break

if __name__ == "__main__":
    main()