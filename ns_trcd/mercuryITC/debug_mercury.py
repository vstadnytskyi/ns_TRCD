import visa, serial

rm = visa.ResourceManager()
reslist =rm.list_resources()
print rm.resource_info(reslist[1], extended=True)
print 'List of Resources \n' ,reslist
mercury = rm.open_resource(reslist[6])
print(mercury.query("*IDN?"))