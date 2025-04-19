# open txt file
apis = set()
txt_file = "Grab/data/inspects.txt"
with open(txt_file, "r", encoding="utf-8") as file:
    content = file.read()
    # show the line that contain /api/
    lines = content.splitlines()
    for line in lines:
        if "/api/" in line:
            # print(line)
            line = line.split('"')
            # print('\n',line)
            for text in line:
                if "/api/" in text:
                    apis.add(text)

# save to txt file
with open("Grab/data/apis.txt", "w", encoding="utf-8") as file:
    for api in apis:
        file.write(api + "\n")
