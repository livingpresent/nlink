import xml.etree.ElementTree as ET
def extract_carel_data(xml_file, output_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Define namespace handling
    ns = {"ns": "raml20.xsd"}  # Namespace from your XML file

    with open(output_file, 'w', encoding='utf-8') as out_file:
        for managed_object in root.findall(".//ns:managedObject", namespaces=ns):
            if managed_object.get("class") == "CAREL":
                dist_name = managed_object.get("distName")
                scell_prio = None

                for param in managed_object.findall("ns:p", namespaces=ns):
                    if param.get("name") == "scellPrio":
                        scell_prio = param.text
                        break  # Stop searching once found

                if dist_name and scell_prio is not None:
                    out_file.write(f"{dist_name};{scell_prio}\n")
                    print(f"Extracted: {dist_name};{scell_prio}")


if __name__ == "__main__":
    # xml_filename = "input.xml"  # Change to your XML file path
    xml_filename = r'C:\Users\wwonganu\Downloads\Final_202035_Busby_combinedfile_NN2_V8.xml' # Input XML file
    output_filename = "carel.txt"
    extract_carel_data(xml_filename, output_filename)
    print(f"Extraction completed. Results saved in {output_filename}")
