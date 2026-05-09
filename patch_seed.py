import subprocess, sys

seed = open('/home/valen/XDEI/PracticaFinal/appCoruna/seed_data.py').read().replace(
    'http://localhost:1026/v2', 'http://orion:1026/v2'
)
with open('/tmp/seed_docker.py', 'w') as f:
    f.write(seed)
print("Written /tmp/seed_docker.py")
