from datetime import datetime, timezone
import h5py

import os
os.system('cls' if os.name == 'nt' else 'clear')


# relative path, must add the full path
file = h5py.File("SR_DS_GL20_production_2026-03-01_12-00-29_UTC.h5", 'r')
print(file.name)
print(list(file.values())[0])


print()
group1 = list(file.values())[0]
print(group1.name)
print(group1.keys())
print(group1.items())
print(group1.attrs.keys())

print()
group2 = list(group1.values())[0]
print(group2.name)
print(group2.keys())
print(group2.items())
print(group2.attrs.keys())

print()
group3 = list(group2.values())[0]
print(group3.name)
print(group3.keys())
print(group3.values())
print(group3.attrs.keys())
test = group3.attrs.items()
for key, value in test:
    print(f"{key}: {value}")
print(datetime.fromtimestamp(1772035819, tz=timezone.utc))


print()
datadt = list(group2.values())[1]
print(datadt.name)
print(datadt.shape)
# print(group4.attrs.values())

print()
data = list(group3.values())[0]
print(data.name)
# print(data.keys())
# print(data.items())
# print(data.attrs.keys())
print(data.shape)
print(data.size)
print(data.ndim)
print(data.dtype)
print(f"{4 * data.size} (in bytes)")
print(data.nbytes)
data2 = data[:, :520, 200:300]
print(data2.shape)


print()
file.close()
